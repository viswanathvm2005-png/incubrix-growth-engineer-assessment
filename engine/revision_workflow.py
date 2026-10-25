"""Save generated drafts as explicitly versioned, review-pending assets.

This workflow does not approve, publish, or overwrite existing asset history.
All required campaign metadata must be supplied by the caller.
"""

from pathlib import Path

from .asset_history import AssetHistory
from .generation_contract import GeneratedDraft
from .revision_adapter import create_revision_asset
from .schemas import AssetFormat, ContentAsset, Platform


def save_generated_draft(
    draft: GeneratedDraft,
    *,
    database_path: str | Path,
    asset_id: str,
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
) -> dict[str, object]:
    """Create and append the next version of a generated draft.

    A new asset starts at version 1. Existing assets use the next version
    found in the database. Existing snapshots are never modified.
    """
    if not isinstance(draft, GeneratedDraft):
        raise TypeError("draft must be a validated GeneratedDraft.")

    history = AssetHistory(database_path)
    existing_versions = history.get_history(asset_id)
    next_version = (
        int(existing_versions[-1]["version"]) + 1
        if existing_versions
        else 1
    )

    asset: ContentAsset = create_revision_asset(
        draft,
        asset_id=asset_id,
        version=next_version,
        source_id=source_id,
        platform=platform,
        asset_format=asset_format,
        utm_url=utm_url,
        target_metric=target_metric,
        created_by_run_id=created_by_run_id,
        video_duration_seconds=video_duration_seconds,
        aspect_ratio=aspect_ratio,
        final_file=final_file,
        editable_source_file=editable_source_file,
    )

    saved = history.save(asset)
    return {
        **saved,
        "draft_id": draft.draft_id,
        "readiness_status": asset.readiness_status.value,
        "usefulness_review": asset.usefulness_review.value,
        "accuracy_review": asset.accuracy_review.value,
        "rights_review": asset.rights_review.value,
        "message": (
            "Asset version saved as a draft. Human review is still required; "
            "this action does not approve or publish the content."
        ),
    }
