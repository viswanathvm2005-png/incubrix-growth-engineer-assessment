import json
from types import SimpleNamespace

import pytest

from engine.generation_contract import GenerationResult
from engine.openrouter_provider import (
    OpenRouterGenerationProvider,
    _extract_json_object,
    build_generation_messages,
)


def make_request():
    brief = SimpleNamespace(
        brief_id="brief-test",
        content_format="text_post",
        capability_ids=[],
        model_dump=lambda mode="json": {
            "brief_id": "brief-test",
            "content_format": "text_post",
            "capability_ids": [],
        },
    )
    return SimpleNamespace(
        brief=brief,
        requested_draft_count=1,
        authorized_capability_ids=[],
    )


def make_provider_response():
    result = {
        "brief_id": "brief-test",
        "status": "success",
        "drafts": [
            {
                "draft_id": "draft-001",
                "content_format": "text_post",
                "angle": "General educational angle",
                "hook": "A question to start a conversation",
                "caption": "A general educational draft for review.",
                "call_to_action": "Share your perspective.",
                "hashtags": ["Learning"],
                "product_claims": [],
                "video_script": None,
            }
        ],
        "warnings": [],
    }
    return {
        "model": "test-model",
        "choices": [{"message": {"content": json.dumps(result)}}],
    }


def test_provider_requires_api_key_without_calling_network(tmp_path):
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        OpenRouterGenerationProvider(
            api_key="",
            env_file=tmp_path / "missing.env",
        )


def test_provider_rejects_non_https_endpoint():
    with pytest.raises(ValueError, match="HTTPS"):
        OpenRouterGenerationProvider(
            api_key="test-key",
            endpoint="http://example.invalid/api",
            env_file="missing-test.env",
        )


def test_extract_json_accepts_markdown_fence():
    parsed = _extract_json_object('```json\n{"status":"success"}\n```')
    assert parsed == {"status": "success"}


def test_extract_json_accepts_surrounding_explanatory_text():
    parsed = _extract_json_object(
        'Here is the result:\n{"status":"success","drafts":[]} \nDone.'
    )
    assert parsed == {"status": "success", "drafts": []}


def test_extract_json_accepts_whitespace_and_plain_json():
    assert _extract_json_object(' \n {"status":"success"} \t') == {
        "status": "success"
    }


@pytest.mark.parametrize("content", ["", "   ", "not json", "```json\n{bad}\n```"])
def test_extract_json_rejects_empty_or_malformed_json(content):
    with pytest.raises(ValueError, match="empty|valid JSON"):
        _extract_json_object(content)


def test_extract_json_rejects_non_object_json():
    with pytest.raises(ValueError, match="JSON object"):
        _extract_json_object('["not", "an object"]')


def test_extract_json_rejects_multiple_objects():
    with pytest.raises(ValueError, match="multiple JSON objects"):
        _extract_json_object('First {"a":1} then {"b":2}')


def test_prompt_disallows_claims_without_authorized_ids():
    messages = build_generation_messages(make_request())
    system_prompt = messages[0]["content"]
    user_payload = json.loads(messages[1]["content"])

    assert "make no product-specific claims" in system_prompt
    assert user_payload["authorized_capability_ids"] == []


def test_generate_parses_mocked_http_response(monkeypatch):
    import engine.openrouter_provider as module

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return json.dumps(make_provider_response()).encode("utf-8")

    def fake_urlopen(request, timeout):
        assert request.full_url == module.DEFAULT_ENDPOINT
        assert timeout > 0
        assert request.get_header("Authorization") == "Bearer test-key"
        return FakeResponse()

    monkeypatch.setattr(module, "urlopen", fake_urlopen)

    provider = OpenRouterGenerationProvider(
        api_key="test-key",
        model="test-model",
        env_file="missing-test.env",
    )
    result = provider.generate(make_request())

    assert isinstance(result, GenerationResult)
    assert result.brief_id == "brief-test"
    assert len(result.drafts) == 1
    assert result.drafts[0].content_format == "text_post"
    assert result.provider_name == "openrouter"
    assert result.model_name == "test-model"
    assert any("human review" in item for item in result.warnings)


def test_generate_rejects_unexpected_provider_envelope(monkeypatch):
    import engine.openrouter_provider as module

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return b'{"unexpected": true}'

    monkeypatch.setattr(
        module,
        "urlopen",
        lambda request, timeout: FakeResponse(),
    )

    provider = OpenRouterGenerationProvider(
        api_key="test-key",
        env_file="missing-test.env",
    )
    with pytest.raises(ValueError, match="unexpected response structure"):
        provider.generate(make_request())


@pytest.mark.parametrize("status_code", [429, 500])
def test_generate_handles_http_error(monkeypatch, status_code):
    from urllib.error import HTTPError
    import engine.openrouter_provider as module

    def fake_urlopen(request, timeout):
        raise HTTPError(
            request.full_url,
            status_code,
            "mock error",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr(module, "urlopen", fake_urlopen)

    provider = OpenRouterGenerationProvider(
        api_key="test-key",
        env_file="missing-test.env",
    )

    with pytest.raises(RuntimeError, match=f"HTTP status {status_code}"):
        provider.generate(make_request())


def test_generate_handles_connection_error(monkeypatch):
    from urllib.error import URLError
    import engine.openrouter_provider as module

    def fake_urlopen(request, timeout):
        raise URLError("mock connection failure")

    monkeypatch.setattr(module, "urlopen", fake_urlopen)

    provider = OpenRouterGenerationProvider(
        api_key="test-key",
        env_file="missing-test.env",
    )

    with pytest.raises(RuntimeError, match="Could not reach OpenRouter"):
        provider.generate(make_request())


def test_generate_handles_timeout(monkeypatch):
    import engine.openrouter_provider as module

    def fake_urlopen(request, timeout):
        raise TimeoutError("mock timeout")

    monkeypatch.setattr(module, "urlopen", fake_urlopen)

    provider = OpenRouterGenerationProvider(
        api_key="test-key",
        env_file="missing-test.env",
    )

    with pytest.raises(RuntimeError, match="timed out"):
        provider.generate(make_request())


def test_prompt_requires_substantive_diversity_for_multiple_drafts():
    messages = build_generation_messages(make_request())
    system_prompt = messages[0]["content"].casefold()

    assert "meaningfully different" in system_prompt
    assert "underlying content angles" in system_prompt
    assert "distinct hook" in system_prompt
    assert "do not invent product capabilities" in system_prompt


def test_generate_handles_response_read_timeout(monkeypatch):
    import engine.openrouter_provider as module

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            raise TimeoutError("mock response-read timeout")

    monkeypatch.setattr(
        module,
        "urlopen",
        lambda request, timeout: FakeResponse(),
    )

    provider = OpenRouterGenerationProvider(
        api_key="test-key",
        timeout_seconds=2,
        env_file="missing-test.env",
    )

    with pytest.raises(RuntimeError, match="timed out"):
        provider.generate(make_request())


def test_generate_handles_response_read_connection_reset(monkeypatch):
    import engine.openrouter_provider as module

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            raise ConnectionResetError("mock connection reset")

    monkeypatch.setattr(
        module,
        "urlopen",
        lambda request, timeout: FakeResponse(),
    )

    provider = OpenRouterGenerationProvider(
        api_key="test-key",
        timeout_seconds=2,
        env_file="missing-test.env",
    )

    with pytest.raises(RuntimeError, match="connection|network|reset"):
        provider.generate(make_request())
