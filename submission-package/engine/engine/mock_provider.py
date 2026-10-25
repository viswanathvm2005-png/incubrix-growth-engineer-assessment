"""Deterministic mock provider for testing content-generation workflows.

This is test infrastructure, not an AI model. The output consists of
labelled synthetic patterns and does not verify product facts.
"""

from .content_brief import ContentFormat
from .generation_contract import (
    GeneratedDraft,
    GenerationRequest,
    GenerationResult,
    GenerationStatus,
    validate_generation_result,
)


_MOCK_PATTERNS = [
    {
        "angle": "Educational explanation",
        "hook": "[MOCK CONTENT — TEST ONLY] Start by explaining the core idea.",
        "caption": "[MOCK CONTENT — TEST ONLY] Explain the supplied message in plain language.",
        "script": [
            "[MOCK CONTENT — TEST ONLY] Introduce the core idea.",
            "[MOCK CONTENT — TEST ONLY] Explain the supplied message simply.",
            "[MOCK CONTENT — TEST ONLY] Close with the requested call to action.",
        ],
    },
    {
        "angle": "Practical checklist",
        "hook": "[MOCK CONTENT — TEST ONLY] Turn the message into a checklist.",
        "caption": "[MOCK CONTENT — TEST ONLY] Present the supplied message as a short checklist.",
        "script": [
            "[MOCK CONTENT — TEST ONLY] Introduce a checklist format.",
            "[MOCK CONTENT — TEST ONLY] Connect the checklist to the supplied message.",
            "[MOCK CONTENT — TEST ONLY] Close with the requested call to action.",
        ],
    },
    {
        "angle": "Common mistake",
        "hook": "[MOCK CONTENT — TEST ONLY] Identify a possible misunderstanding.",
        "caption": "[MOCK CONTENT — TEST ONLY] Explain the supplied message by contrasting it with a possible misunderstanding.",
        "script": [
            "[MOCK CONTENT — TEST ONLY] Introduce a possible misunderstanding.",
            "[MOCK CONTENT — TEST ONLY] Clarify the supplied message without adding factual claims.",
            "[MOCK CONTENT — TEST ONLY] Close with the requested call to action.",
        ],
    },
    {
        "angle": "Step-by-step structure",
        "hook": "[MOCK CONTENT — TEST ONLY] Break the message into steps.",
        "caption": "[MOCK CONTENT — TEST ONLY] Organize the supplied message into a simple sequence.",
        "script": [
            "[MOCK CONTENT — TEST ONLY] Introduce a step-by-step structure.",
            "[MOCK CONTENT — TEST ONLY] Explain the supplied message as a sequence.",
            "[MOCK CONTENT — TEST ONLY] Close with the requested call to action.",
        ],
    },
    {
        "angle": "Question-led introduction",
        "hook": "[MOCK CONTENT — TEST ONLY] Begin with a question about the message.",
        "caption": "[MOCK CONTENT — TEST ONLY] Use a question to introduce the supplied message.",
        "script": [
            "[MOCK CONTENT — TEST ONLY] Ask a question about the topic.",
            "[MOCK CONTENT — TEST ONLY] Connect the question to the supplied message.",
            "[MOCK CONTENT — TEST ONLY] Close with the requested call to action.",
        ],
    },
    {
        "angle": "Myth-versus-fact format",
        "hook": "[MOCK CONTENT — TEST ONLY] Separate an assumption from the message.",
        "caption": "[MOCK CONTENT — TEST ONLY] Structure the supplied message as an assumption-versus-clarification exercise.",
        "script": [
            "[MOCK CONTENT — TEST ONLY] Introduce an assumption for discussion, not as a fact.",
            "[MOCK CONTENT — TEST ONLY] Clarify using only the supplied message.",
            "[MOCK CONTENT — TEST ONLY] Close with the requested call to action.",
        ],
    },
    {
        "angle": "Reflection prompt",
        "hook": "[MOCK CONTENT — TEST ONLY] Invite the reader to reflect.",
        "caption": "[MOCK CONTENT — TEST ONLY] Present the supplied message as a reflection prompt.",
        "script": [
            "[MOCK CONTENT — TEST ONLY] Invite the audience to reflect on the topic.",
            "[MOCK CONTENT — TEST ONLY] Relate the reflection to the supplied message.",
            "[MOCK CONTENT — TEST ONLY] Close with the requested call to action.",
        ],
    },
    {
        "angle": "Summary format",
        "hook": "[MOCK CONTENT — TEST ONLY] Reduce the message to its essentials.",
        "caption": "[MOCK CONTENT — TEST ONLY] Summarize the supplied message in a concise format.",
        "script": [
            "[MOCK CONTENT — TEST ONLY] Introduce a concise summary.",
            "[MOCK CONTENT — TEST ONLY] State the supplied message clearly.",
            "[MOCK CONTENT — TEST ONLY] Close with the requested call to action.",
        ],
    },
    {
        "angle": "Audience discussion",
        "hook": "[MOCK CONTENT — TEST ONLY] Open a discussion about the topic.",
        "caption": "[MOCK CONTENT — TEST ONLY] Frame the supplied message as a discussion starter.",
        "script": [
            "[MOCK CONTENT — TEST ONLY] Introduce a discussion prompt.",
            "[MOCK CONTENT — TEST ONLY] Connect the discussion to the supplied message.",
            "[MOCK CONTENT — TEST ONLY] Close with the requested call to action.",
        ],
    },
    {
        "angle": "Key takeaway",
        "hook": "[MOCK CONTENT — TEST ONLY] Focus on one takeaway.",
        "caption": "[MOCK CONTENT — TEST ONLY] Present the supplied message as a single takeaway.",
        "script": [
            "[MOCK CONTENT — TEST ONLY] Introduce the takeaway format.",
            "[MOCK CONTENT — TEST ONLY] State the supplied message as the takeaway.",
            "[MOCK CONTENT — TEST ONLY] Close with the requested call to action.",
        ],
    },
]


class MockGenerationProvider:
    """Return predictable, labelled synthetic drafts."""

    provider_name = "mock"
    model_name = "deterministic-test-provider"

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate test patterns and validate them against the request."""
        drafts = []
        key_message = request.brief.key_message

        for index in range(request.requested_draft_count):
            pattern = _MOCK_PATTERNS[index % len(_MOCK_PATTERNS)]
            is_video = (
                request.brief.content_format == ContentFormat.SHORT_VIDEO
            )

            script = (
                [
                    f"{pattern['script'][0]} Supplied message: {key_message}",
                    f"{pattern['script'][1]} Supplied message: {key_message}",
                    pattern["script"][2],
                ]
                if is_video
                else None
            )

            drafts.append(
                GeneratedDraft(
                    draft_id=f"{request.request_id}-mock-{index + 1:02d}",
                    content_format=request.brief.content_format,
                    angle=f"[MOCK CONTENT — TEST ONLY] {pattern['angle']}",
                    hook=pattern["hook"],
                    caption=(
                        f"{pattern['caption']} "
                        f"Supplied message: {key_message}"
                    ),
                    call_to_action=request.brief.call_to_action,
                    hashtags=[],
                    product_claims=[],
                    video_script=script,
                )
            )

        result = GenerationResult(
            brief_id=request.brief.brief_id,
            status=GenerationStatus.SUCCESS,
            drafts=drafts,
            warnings=[
                "MOCK OUTPUT ONLY: not generated by an AI model.",
                "Patterns test structural variation, not publish-ready quality.",
                "Review product claims, factual accuracy, usefulness, and rights "
                "before any real-world use.",
            ],
            provider_name=self.provider_name,
            model_name=self.model_name,
        )

        return validate_generation_result(request, result)
