import pytest
from pydantic import ValidationError

from engine.content_brief import ContentBrief, ContentFormat, Platform
from engine.generation_contract import (
    GeneratedDraft,
    GenerationRequest,
    GenerationResult,
    GenerationStatus,
    validate_generation_result,
)
from engine.schemas import CapabilityReference


def make_brief(*, content_format=ContentFormat.TEXT_POST, capability_ids=None):
    values = {
        "brief_id": "brief-test-001",
        "campaign_objective": "Explain a verified product capability",
        "target_audience": "Technology decision makers",
        "platform": Platform.LINKEDIN,
        "content_format": content_format,
        "source_ids": ["source-test-001"],
        "capability_ids": capability_ids or [],
    }
    if content_format == ContentFormat.SHORT_VIDEO:
        values["requested_duration_seconds"] = 30
        values["aspect_ratio"] = "9:16"
    return ContentBrief(**values)


def make_request(
    *,
    content_format=ContentFormat.TEXT_POST,
    brief_capabilities=None,
    authorized_capabilities=None,
):
    return GenerationRequest(
        request_id="request-test-001",
        brief=make_brief(
            content_format=content_format,
            capability_ids=brief_capabilities,
        ),
        requested_draft_count=2,
        authorized_capability_ids=authorized_capabilities or [],
    )


def make_draft(
    *,
    draft_id="draft-test-001",
    content_format=ContentFormat.TEXT_POST,
    claims=None,
    video_script=None,
):
    return GeneratedDraft(
        draft_id=draft_id,
        content_format=content_format,
        angle="Explain one idea clearly",
        hook="A sample educational hook",
        caption="This is a synthetic draft for contract testing.",
        call_to_action="Learn more",
        hashtags=["#Example"],
        product_claims=claims or [],
        video_script=video_script,
    )


def make_result(
    *,
    drafts=None,
    brief_id="brief-test-001",
    status=GenerationStatus.SUCCESS,
):
    return GenerationResult(
        brief_id=brief_id,
        status=status,
        drafts=drafts if drafts is not None else [make_draft()],
    )


def test_valid_request_and_response():
    request = make_request()
    result = make_result()
    validated = validate_generation_result(request, result)
    assert validated.status == GenerationStatus.SUCCESS
    assert len(validated.drafts) == 1


def test_request_rejects_brief_capability_not_authorized():
    with pytest.raises(ValidationError, match="not present"):
        make_request(brief_capabilities=["CAP-001"], authorized_capabilities=[])


def test_empty_capability_register_authorizes_no_product_claims():
    request = make_request()
    claim = CapabilityReference(
        claim_text="An unsupported product claim",
        capability_ids=["CAP-001"],
    )
    result = make_result(drafts=[make_draft(claims=[claim])])
    with pytest.raises(ValueError, match="unauthorized capability IDs"):
        validate_generation_result(request, result)


def test_claim_must_be_requested_by_brief():
    request = make_request(
        brief_capabilities=["CAP-001"],
        authorized_capabilities=["CAP-001"],
    )
    claim = CapabilityReference(
        claim_text="A claim tied to another capability",
        capability_ids=["CAP-002"],
    )
    result = make_result(drafts=[make_draft(claims=[claim])])
    with pytest.raises(ValueError, match="unauthorized capability IDs"):
        validate_generation_result(request, result)


def test_valid_authorized_claim_passes_structural_check():
    request = make_request(
        brief_capabilities=["CAP-001"],
        authorized_capabilities=["CAP-001"],
    )
    claim = CapabilityReference(
        claim_text="A candidate-verified claim",
        capability_ids=["CAP-001"],
    )
    result = make_result(drafts=[make_draft(claims=[claim])])
    assert validate_generation_result(request, result) == result


def test_result_must_match_brief_id():
    request = make_request()
    result = make_result(brief_id="different-brief")
    with pytest.raises(ValueError, match="does not match"):
        validate_generation_result(request, result)


def test_result_cannot_exceed_requested_draft_count():
    request = make_request()
    result = make_result(
        drafts=[
            make_draft(draft_id="draft-1"),
            make_draft(draft_id="draft-2"),
            make_draft(draft_id="draft-3"),
        ]
    )
    with pytest.raises(ValueError, match="more drafts than requested"):
        validate_generation_result(request, result)


def test_short_video_requires_script():
    request = make_request(content_format=ContentFormat.SHORT_VIDEO)
    result = make_result(
        drafts=[make_draft(content_format=ContentFormat.SHORT_VIDEO)]
    )
    with pytest.raises(ValueError, match="needs a video script"):
        validate_generation_result(request, result)


def test_short_video_with_script_passes():
    request = make_request(content_format=ContentFormat.SHORT_VIDEO)
    result = make_result(
        drafts=[
            make_draft(
                content_format=ContentFormat.SHORT_VIDEO,
                video_script=["Opening hook", "Explain the idea", "Closing CTA"],
            )
        ]
    )
    assert validate_generation_result(request, result) == result


def test_non_video_draft_rejects_video_script():
    request = make_request()
    result = make_result(
        drafts=[make_draft(video_script=["Unexpected video script"])]
    )
    with pytest.raises(ValueError, match="cannot contain a video script"):
        validate_generation_result(request, result)


def test_success_cannot_have_zero_drafts():
    with pytest.raises(ValidationError, match="successful result"):
        make_result(drafts=[])


def test_failed_result_cannot_contain_drafts():
    with pytest.raises(ValidationError, match="failed result"):
        make_result(status=GenerationStatus.FAILED)


def test_unknown_provider_metadata_can_remain_null():
    result = make_result()
    assert result.provider_name is None
    assert result.model_name is None


def test_extra_response_fields_are_rejected():
    with pytest.raises(ValidationError):
        GeneratedDraft(
            **{
                "draft_id": "draft-test",
                "content_format": "text_post",
                "angle": "Educational",
                "hook": "A hook",
                "caption": "A caption",
                "call_to_action": "Learn more",
                "unexpected_field": "not allowed",
            }
        )
def test_generation_contract_rejects_duplicate_draft_ids():
    request = make_request()

    duplicate_draft = make_draft(draft_id="same-draft-id")

    result = make_result(
        drafts=[
            duplicate_draft,
            duplicate_draft.model_copy(),
        ]
    )

    with pytest.raises(ValueError, match="duplicate draft IDs"):
        validate_generation_result(request, result)


@pytest.mark.parametrize("field", ["hook", "caption"])
def test_generation_contract_rejects_exact_duplicate_content(field):
    request = make_request()

    first = make_draft(draft_id="draft-one")
    second = make_draft(draft_id="draft-two")

    if field == "hook":
        second = second.model_copy(update={"hook": first.hook})
    else:
        second = second.model_copy(update={"caption": first.caption})

    result = make_result(drafts=[first, second])

    with pytest.raises(ValueError, match="duplicate"):
        validate_generation_result(request, result)
