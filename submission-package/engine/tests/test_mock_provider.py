import pytest

from engine.content_brief import ContentBrief, ContentFormat, Platform
from engine.generation_contract import GenerationRequest, GenerationStatus
from engine.mock_provider import MockGenerationProvider


def make_request(
    *,
    content_format=ContentFormat.TEXT_POST,
    requested_draft_count=3,
):
    brief = ContentBrief(
        brief_id="brief-mock-test",
        campaign_objective="Test the generation workflow",
        target_audience="Assessment reviewers",
        platform=Platform.LINKEDIN,
        content_format=content_format,
        source_ids=["source-test-001"],
        capability_ids=[],
        key_message="Explain the supplied message clearly",
        tone="Professional and approachable",
        call_to_action="Learn more",
        avoid_topics=[],
        requested_duration_seconds=(
            30 if content_format == ContentFormat.SHORT_VIDEO else None
        ),
        aspect_ratio=(
            "9:16" if content_format == ContentFormat.SHORT_VIDEO else None
        ),
    )
    return GenerationRequest(
        request_id="request-mock-test",
        brief=brief,
        requested_draft_count=requested_draft_count,
        authorized_capability_ids=[],
    )


def test_mock_provider_returns_requested_number_of_drafts():
    request = make_request(requested_draft_count=3)
    result = MockGenerationProvider().generate(request)

    assert len(result.drafts) == 3
    assert result.status == GenerationStatus.SUCCESS


def test_mock_provider_uses_stable_draft_ids():
    provider = MockGenerationProvider()
    request = make_request(requested_draft_count=2)

    first = provider.generate(request)
    second = provider.generate(request)

    assert [draft.draft_id for draft in first.drafts] == [
        draft.draft_id for draft in second.drafts
    ]


def test_mock_provider_labels_output_as_mock():
    result = MockGenerationProvider().generate(make_request())

    assert all("[MOCK CONTENT" in draft.caption for draft in result.drafts)
    assert any("MOCK OUTPUT ONLY" in warning for warning in result.warnings)
    assert result.provider_name == "mock"


def test_mock_provider_preserves_brief_format():
    request = make_request(content_format=ContentFormat.STATIC_POST)
    result = MockGenerationProvider().generate(request)

    assert all(
        draft.content_format == ContentFormat.STATIC_POST
        for draft in result.drafts
    )


def test_mock_provider_short_video_includes_script():
    request = make_request(content_format=ContentFormat.SHORT_VIDEO)
    result = MockGenerationProvider().generate(request)

    assert all(draft.video_script for draft in result.drafts)
    assert all(
        draft.content_format == ContentFormat.SHORT_VIDEO
        for draft in result.drafts
    )


def test_mock_provider_non_video_has_no_video_script():
    result = MockGenerationProvider().generate(make_request())

    assert all(draft.video_script is None for draft in result.drafts)


@pytest.mark.parametrize("count", [1, 2, 5, 10])
def test_mock_provider_supports_valid_draft_counts(count):
    result = MockGenerationProvider().generate(
        make_request(requested_draft_count=count)
    )

    assert len(result.drafts) == count


def test_mock_provider_does_not_invent_product_claim_references():
    result = MockGenerationProvider().generate(make_request())

    assert all(not draft.product_claims for draft in result.drafts)


def test_mock_provider_produces_distinct_hooks_and_captions():
    result = MockGenerationProvider().generate(
        make_request(requested_draft_count=10)
    )

    hooks = [draft.hook.strip().casefold() for draft in result.drafts]
    captions = [draft.caption.strip().casefold() for draft in result.drafts]

    assert len(set(hooks)) == len(hooks), "Duplicate hooks detected."
    assert len(set(captions)) == len(captions), "Duplicate captions detected."
