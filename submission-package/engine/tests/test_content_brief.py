import pytest
from pydantic import ValidationError

from engine.content_brief import ContentBrief, ContentFormat, Platform


def valid_brief(**overrides):
    data = {
        "brief_id": "brief-001",
        "campaign_objective": "Explain a verified product feature",
        "target_audience": "Prospective customers",
        "platform": "linkedin",
        "content_format": "text_post",
        "source_ids": ["source-001"],
    }
    data.update(overrides)
    return data


def test_valid_text_post_brief_is_accepted():
    brief = ContentBrief(**valid_brief())

    assert brief.platform == Platform.LINKEDIN
    assert brief.content_format == ContentFormat.TEXT_POST
    assert brief.source_ids == ["source-001"]
    assert brief.capability_ids == []


def test_valid_short_video_requires_and_accepts_metadata():
    brief = ContentBrief(
        **valid_brief(
            content_format="short_video",
            platform="instagram",
            requested_duration_seconds=30,
            aspect_ratio="9:16",
        )
    )

    assert brief.requested_duration_seconds == 30
    assert brief.aspect_ratio == "9:16"


def test_source_ids_are_required():
    with pytest.raises(ValidationError):
        ContentBrief(**valid_brief(source_ids=[]))


def test_blank_objective_is_rejected():
    with pytest.raises(ValidationError):
        ContentBrief(**valid_brief(campaign_objective="   "))


def test_short_video_without_duration_is_rejected():
    with pytest.raises(ValidationError):
        ContentBrief(
            **valid_brief(
                content_format="short_video",
                aspect_ratio="9:16",
            )
        )


def test_short_video_without_aspect_ratio_is_rejected():
    with pytest.raises(ValidationError):
        ContentBrief(
            **valid_brief(
                content_format="short_video",
                requested_duration_seconds=30,
            )
        )


def test_video_over_60_seconds_is_rejected():
    with pytest.raises(ValidationError):
        ContentBrief(
            **valid_brief(
                content_format="short_video",
                requested_duration_seconds=61,
                aspect_ratio="9:16",
            )
        )


def test_non_video_cannot_have_requested_duration():
    with pytest.raises(ValidationError):
        ContentBrief(
            **valid_brief(requested_duration_seconds=30)
        )


def test_invalid_aspect_ratio_is_rejected():
    with pytest.raises(ValidationError):
        ContentBrief(
            **valid_brief(
                content_format="short_video",
                requested_duration_seconds=30,
                aspect_ratio="vertical",
            )
        )


def test_duplicate_source_ids_are_rejected():
    with pytest.raises(ValidationError):
        ContentBrief(
            **valid_brief(source_ids=["source-001", "source-001"])
        )
