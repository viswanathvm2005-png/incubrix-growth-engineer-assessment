"""Convert a generated draft into an explicitly versioned candidate asset.

This module does not approve content, submit reviews, publish posts, or invent
candidate metadata. It creates a ContentAsset that remains a draft.
"""

from .generation_contract import GeneratedDraft
from .schemas import (
    AssetFormat,
    ContentAsset,
    Platform,
    ReadinessStatus,
    ReviewStatus,
)


def create_revision_asset(
    draft: GeneratedDraft,
    *,
    asset_id: str,
    version: int,
    source_id: str,
    platform: Platform | str,
    asset_format: AssetFormat | str,
    utm_url: str,
    target_metric: str,
    created_by_run_id: str,
    video_duration_seconds: float | None = None,
    aspect_ratio: str | None = None,
    final_file: str | None = None,
    editable_source_file: str | None = None,
) -> ContentAsset:
    """Build a pending ContentAsset from a generated draft and supplied metadata.

    The caller must provide real metadata. The adapter intentionally does not
    infer whether a static post is text or graphic, or invent video properties.
    """
    if not isinstance(draft, GeneratedDraft):
        raise TypeError("draft must be a validated GeneratedDraft.")

    normalized_format = AssetFormat(asset_format)
    normalized_platform = Platform(platform)
    generation_format = draft.content_format.value

    # Formats with an unambiguous asset representation must agree.
    if generation_format == "short_video" and normalized_format != AssetFormat.VIDEO:
        raise ValueError(
            "A short_video draft must use asset_format='video'."
        )
    if generation_format == "carousel" and normalized_format != AssetFormat.CAROUSEL:
        raise ValueError(
            "A carousel draft must use asset_format='carousel'."
        )
    if normalized_format == AssetFormat.VIDEO and generation_format != "short_video":
        raise ValueError(
            "A video asset must originate from a short_video draft."
        )
    if normalized_format == AssetFormat.CAROUSEL and generation_format != "carousel":
        raise ValueError(
            "A carousel asset must originate from a carousel draft."
        )

    return ContentAsset(
        asset_id=asset_id,
        version=version,
        source_id=source_id,
        platform=normalized_platform,
        format=normalized_format,
        angle=draft.angle,
        hook=draft.hook,
        caption=draft.caption,
        hashtags=draft.hashtags,
        cta=draft.call_to_action,
        utm_url=utm_url,
        target_metric=target_metric,
        final_file=final_file,
        editable_source_file=editable_source_file,
        product_claims=draft.product_claims,
        video_duration_seconds=video_duration_seconds,
        aspect_ratio=aspect_ratio,
        usefulness_review=ReviewStatus.PENDING,
        accuracy_review=ReviewStatus.PENDING,
        rights_review=ReviewStatus.PENDING,
        created_by_run_id=created_by_run_id,
        readiness_status=ReadinessStatus.DRAFT,
    )
