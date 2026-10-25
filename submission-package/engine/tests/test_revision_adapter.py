"""Tests for conversion of generated drafts into candidate assets."""

import pytest
from pydantic import ValidationError

from engine.generation_contract import GeneratedDraft
from engine.revision_adapter import create_revision_asset
from engine.schemas import (
    AssetFormat,
    ContentAsset,
    ReadinessStatus,
    ReviewStatus,
)


def make_draft(
    content_format="static_post",
    product_claims=None,
    video_script=None,
):
    data = {
        "draft_id": "draft-revision-002",
        "content_format": content_format,
        "angle": "A clearly identified sample angle",
        "hook": "A sample hook for reviewer evaluation",
        "caption": "Sample content; replace with verified candidate information.",
        "call_to_action": "Review the sample",
        "hashtags": ["#sample", "#prototype"],
        "product_claims": product_claims or [],
    }
    if video_script is not None:
        data["video_script"] = video_script
    return GeneratedDraft.model_validate(data)


def make_asset(**overrides):
    values = {
        "asset_id": "asset-sample-001",
        "version": 2,
        "source_id": "candidate-source-001",
        "platform": "linkedin",
        "asset_format": "graphic",
        "utm_url": "https://example.com/sample",
        "target_metric": "clicks",
        "created_by_run_id": "run-sample-002",
    }
    values.update(overrides)
    return create_revision_asset(make_draft(), **values)


def test_creates_asset_with_supplied_version_and_metadata():
    asset = make_asset()

    assert isinstance(asset, ContentAsset)
    assert asset.asset_id == "asset-sample-001"
    assert asset.version == 2
    assert asset.source_id == "candidate-source-001"
    assert asset.created_by_run_id == "run-sample-002"


def test_maps_draft_content_fields():
    asset = make_asset()

    assert asset.angle == "A clearly identified sample angle"
    assert asset.hook == "A sample hook for reviewer evaluation"
    assert asset.caption.startswith("Sample content")
    assert asset.cta == "Review the sample"
    assert asset.hashtags == ["#sample", "#prototype"]


def test_new_asset_is_draft_with_all_reviews_pending():
    asset = make_asset()

    assert asset.readiness_status == ReadinessStatus.DRAFT
    assert asset.usefulness_review == ReviewStatus.PENDING
    assert asset.accuracy_review == ReviewStatus.PENDING
    assert asset.rights_review == ReviewStatus.PENDING


def test_preserves_product_claim_references():
    draft = make_draft(
        product_claims=[
            {
                "claim_text": "Example claim supplied for a schema test",
                "capability_ids": ["capability-test-001"],
            }
        ]
    )

    asset = create_revision_asset(
        draft,
        asset_id="asset-sample-002",
        version=1,
        source_id="candidate-source-001",
        platform="linkedin",
        asset_format="graphic",
        utm_url="https://example.com/sample",
        target_metric="clicks",
        created_by_run_id="run-sample-001",
    )

    assert len(asset.product_claims) == 1
    assert asset.product_claims[0].capability_ids == ["capability-test-001"]


def test_requires_explicit_metadata():
    with pytest.raises(TypeError):
        create_revision_asset(make_draft())


def test_rejects_blank_source_id():
    with pytest.raises(ValidationError):
        make_asset(source_id=" ")


def test_rejects_invalid_utm_url():
    with pytest.raises(ValidationError):
        make_asset(utm_url="not-a-url")


def test_short_video_requires_video_asset_format():
    draft = make_draft(
        content_format="short_video",
        video_script=["Opening", "Main point", "Closing"],
    )

    with pytest.raises(ValueError, match="short_video"):
        create_revision_asset(
            draft,
            asset_id="asset-video-001",
            version=1,
            source_id="candidate-source-001",
            platform="youtube_shorts",
            asset_format="graphic",
            utm_url="https://example.com/video",
            target_metric="views",
            created_by_run_id="run-video-001",
        )


def test_video_requires_duration_and_aspect_ratio():
    draft = make_draft(
        content_format="short_video",
        video_script=["Opening", "Main point", "Closing"],
    )

    with pytest.raises(ValidationError):
        create_revision_asset(
            draft,
            asset_id="asset-video-002",
            version=1,
            source_id="candidate-source-001",
            platform="youtube_shorts",
            asset_format="video",
            utm_url="https://example.com/video",
            target_metric="views",
            created_by_run_id="run-video-002",
        )


def test_accepts_video_when_required_properties_are_supplied():
    draft = make_draft(
        content_format="short_video",
        video_script=["Opening", "Main point", "Closing"],
    )

    asset = create_revision_asset(
        draft,
        asset_id="asset-video-003",
        version=1,
        source_id="candidate-source-001",
        platform="youtube_shorts",
        asset_format="video",
        utm_url="https://example.com/video",
        target_metric="views",
        created_by_run_id="run-video-003",
        video_duration_seconds=30,
        aspect_ratio="9:16",
    )

    assert asset.format == AssetFormat.VIDEO
    assert asset.video_duration_seconds == 30
    assert asset.aspect_ratio == "9:16"
    assert asset.readiness_status == ReadinessStatus.DRAFT


def test_rejects_carousel_with_graphic_format():
    draft = make_draft(content_format="carousel")

    with pytest.raises(ValueError, match="carousel"):
        create_revision_asset(
            draft,
            asset_id="asset-carousel-001",
            version=1,
            source_id="candidate-source-001",
            platform="linkedin",
            asset_format="graphic",
            utm_url="https://example.com/carousel",
            target_metric="engagement",
            created_by_run_id="run-carousel-001",
        )


def test_rejects_non_draft_input_object():
    with pytest.raises(TypeError, match="GeneratedDraft"):
        create_revision_asset(
            {"draft_id": "not-validated"},
            asset_id="asset-sample-003",
            version=1,
            source_id="candidate-source-001",
            platform="linkedin",
            asset_format="graphic",
            utm_url="https://example.com/sample",
            target_metric="clicks",
            created_by_run_id="run-sample-003",
        )
