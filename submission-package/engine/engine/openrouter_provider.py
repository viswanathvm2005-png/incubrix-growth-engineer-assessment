"""OpenRouter adapter using Python's standard library only.

This provider returns structured drafts. It does not publish content or
prove that product claims are factually supported.
"""
import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .generation_contract import GenerationRequest, GenerationResult


DEFAULT_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openrouter/free"
DEFAULT_TIMEOUT_SECONDS = 45

ALLOWED_CONTENT_FORMATS = (
    "static_post",
    "carousel",
    "short_video",
    "story",
    "text_post",
)


def _load_local_env_file(path: str | Path = ".env") -> None:
    """Load simple KEY=VALUE entries without overriding existing variables."""
    env_path = Path(path)
    if not env_path.is_file():
        return

    for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if value.startswith(("'", '"')) and value.endswith(("'", '"')):
            value = value[1:-1]

        if key and key not in os.environ:
            os.environ[key] = value


def _extract_json_object(content: str) -> dict:
    """Extract one unambiguous JSON object, optionally surrounded by prose."""
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Provider response was empty; expected a JSON object.")

    cleaned = content.strip()

    # Prefer a complete fenced JSON block when the model supplies one.
    fence_matches = re.findall(
        r"```(?:json)?\s*(.*?)\s*```",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    candidates = fence_matches if fence_matches else [cleaned]

    parsed_objects = []
    decoder = json.JSONDecoder()

    for candidate in candidates:
        candidate = candidate.strip()

        # First try a direct parse. This covers normal JSON and fenced JSON.
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                parsed_objects.append(parsed)
                continue
            if parsed is not None:
                continue
        except json.JSONDecodeError:
            pass

        # If explanatory text surrounds JSON, scan for complete JSON objects.
        for match in re.finditer(r"\{", candidate):
            try:
                parsed, _end = decoder.raw_decode(candidate[match.start():])
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                parsed_objects.append(parsed)

    # De-duplicate identical objects that may have been found by multiple scans.
    unique = []
    seen = set()
    for item in parsed_objects:
        fingerprint = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if fingerprint not in seen:
            seen.add(fingerprint)
            unique.append(item)

    if not unique:
        raise ValueError("Provider response was not valid JSON object content.")
    if len(unique) > 1:
        raise ValueError("Provider response contained multiple JSON objects.")
    return unique[0]


def build_generation_messages(request: GenerationRequest) -> list[dict]:
    """Build a provider prompt from validated request data."""
    authorized_ids = list(request.authorized_capability_ids)
    brief_data = request.brief.model_dump(mode="json")
    required_format = str(
        getattr(
            request.brief.content_format,
            "value",
            request.brief.content_format,
        )
    )

    system_prompt = (
        "You are a cautious social media content drafting assistant. "
        "Return ONLY one valid JSON object. Do not include Markdown "
        "outside the JSON object. The top-level object must have this "
        "structure: "
        '{"brief_id":"string","status":"success","drafts":['
        '{"draft_id":"string","content_format":"static_post",'
        '"angle":"string","hook":"string","caption":"string",'
        '"call_to_action":"string","hashtags":["string"],'
        '"product_claims":[{"claim_text":"string",'
        '"capability_ids":["authorized-id"]}],'
        '"video_script":["spoken/narrated beat"] or null}],'
        '"warnings":["string"]}. '
        "When more than one draft is requested, make the drafts "
        "meaningfully different in their underlying content angles, not "
        "just their labels or wording. Vary the audience problem, "
        "educational approach, example, or intended discussion point when "
        "the supplied brief supports it. Give each draft a distinct hook "
        "and caption that express its own angle. For video drafts, make "
        "the script beats specific to that draft's angle. Do not claim "
        "that drafts are distinct merely because their IDs differ. Do not "
        "invent product capabilities, evidence, statistics, or outcomes "
        "to create variety. If the brief does not support factual variety, "
        "stay within the supplied information. "        "The only allowed content_format values are "
        "'static_post', 'carousel', 'short_video', 'story', and "
        "'text_post'. Never use 'text', 'graphic', or 'video' as "
        "content_format values. The user message supplies the exact "
        "required format. Every draft's content_format MUST equal that "
        "exact required format. Return exactly the requested number of "
        "drafts. Use the supplied brief_id exactly. "
        "Do not invent product features, customers, results, statistics, "
        "prices, guarantees, testimonials, or performance claims. "
        "Every product-specific claim must cite one or more capability IDs "
        "from the authorized list AND from the brief capability list. "
        "If the authorized list is empty, make no product-specific claims "
        "and return product_claims as an empty list for every draft. "
        "Do not invent capability IDs. If the supplied information is "
        "insufficient, use cautious generic wording and add a warning. "
        "For short_video, include video_script as a non-empty array of "
        "spoken or narrated beats. For every other format, set "
        "video_script to null. Content is a draft for human review, "
        "not approved or published content."
    )

    user_payload = {
        "brief": brief_data,
        "required_content_format": required_format,
        "allowed_content_formats": list(ALLOWED_CONTENT_FORMATS),
        "requested_draft_count": request.requested_draft_count,
        "authorized_capability_ids": authorized_ids,
        "required_brief_capability_ids": list(request.brief.capability_ids),
        "important_instruction": (
            "Match required_content_format exactly. Do not substitute "
            "a synonym or a different format."
        ),
    }

    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": json.dumps(user_payload, ensure_ascii=False),
        },
    ]


class OpenRouterGenerationProvider:
    """Call OpenRouter's OpenAI-compatible chat-completions endpoint."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        endpoint: str | None = None,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        env_file: str | Path = ".env",
    ):
        _load_local_env_file(env_file)

        self.api_key = (
            api_key
            or os.environ.get("OPENROUTER_API_KEY")
            or ""
        ).strip()
        self.model = (
            model or os.environ.get("OPENROUTER_MODEL") or DEFAULT_MODEL
        ).strip()
        self.endpoint = (
            endpoint
            or os.environ.get("OPENROUTER_BASE_URL")
            or DEFAULT_ENDPOINT
        ).strip()
        self.timeout_seconds = timeout_seconds

        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is not configured. Set it in your "
                "local .env file or environment before selecting this provider."
            )
        if not self.model:
            raise ValueError("OpenRouter model name must not be blank.")
        if not self.endpoint.startswith("https://"):
            raise ValueError("OpenRouter endpoint must use HTTPS.")
        if self.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be at least 1.")

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Send one request and validate the response's JSON structure."""
        payload = {
            "model": self.model,
            "messages": build_generation_messages(request),
            "temperature": 0.2,
        }

        http_request = Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost",
                "X-Title": "IncuBrix Assessment Content Engine",
            },
            method="POST",
        )

        try:
            with urlopen(
                http_request,
                timeout=self.timeout_seconds,
            ) as response:
                response_text = response.read().decode("utf-8")
        except HTTPError as exc:
            raise RuntimeError(
                f"OpenRouter request failed with HTTP status {exc.code}."
            ) from None
        except URLError as exc:
            raise RuntimeError(
                f"Could not reach OpenRouter: {exc.reason}"
            ) from None
        except TimeoutError:
            raise RuntimeError("OpenRouter request timed out.") from None
        except OSError as exc:
            raise RuntimeError(
                f"OpenRouter network error while reading the response: {exc}"
            ) from None

        try:
            envelope = json.loads(response_text)
            content = envelope["choices"][0]["message"]["content"]
        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
            raise ValueError(
                "OpenRouter returned an unexpected response structure."
            ) from None

        if not isinstance(content, str) or not content.strip():
            raise ValueError("OpenRouter returned empty message content.")

        result_data = _extract_json_object(content)
        result_data["provider_name"] = "openrouter"
        result_data["model_name"] = envelope.get("model") or self.model

        result = GenerationResult.model_validate(result_data)
        result.warnings = list(dict.fromkeys([
            *result.warnings,
            "AI-generated content requires human review before use.",
            "Capability ID checks are structural; they do not prove a claim is true.",
        ]))
        return result

