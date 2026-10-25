import pytest

from engine.asset_history import AssetHistory
from engine.content_brief import ContentFormat
from engine.generation_contract import GeneratedDraft
from engine.revision_workflow import save_generated_draft
from engine.schemas import AssetFormat, ReadinessStatus, ReviewStatus


def make_draft(
    *,
    draft_id="draft-test-001",
    hook="A sample hook",
    caption="A sample caption for testing.",
    content_format=ContentFormat.STATIC_POST,
):
    return GeneratedDraft(
        draft_id=draft_id,
        content_format=content_format,
        angle="Sample educational angle",
        hook=hook,
        caption=caption,
        call_to_action="Review the sample",
        hashtags=["sample"],
        product_claims=[],
    )


def save_args(database_path, **overrides):
    args = {
        "database_path": database_path,
        "asset_id": "asset-test-001",
        "source_id": "source-test-001",
        "platform": "linkedin",
        "asset_format": "graphic",
        "utm_url": "https://example.com/?utm_source=test",
        "target_metric": "clicks",
        "created_by_run_id": "run-test-001",
    }
    args.update(overrides)
    return args


def test_first_draft_is_saved_as_version_one(tmp_path):
    database = tmp_path / "history.sqlite3"

    result = save_generated_draft(
        make_draft(),
        **save_args(database),
    )

    assert result["status"] == "SAVED"
    assert result["version"] == 1
    assert result["draft_id"] == "draft-test-001"


def test_second_save_appends_next_version(tmp_path):
    database = tmp_path / "history.sqlite3"

    first = save_generated_draft(
        make_draft(),
        **save_args(database),
    )
    second = save_generated_draft(
        make_draft(
            draft_id="draft-test-002",
            hook="A revised sample hook",
        ),
        **save_args(database),
    )

    assert first["version"] == 1
    assert second["version"] == 2

    snapshots = AssetHistory(database).get_history("asset-test-001")
    assert [item["version"] for item in snapshots] == [1, 2]
    assert snapshots[0]["hook"] == "A sample hook"
    assert snapshots[1]["hook"] == "A revised sample hook"


def test_new_asset_id_starts_at_version_one(tmp_path):
    database = tmp_path / "history.sqlite3"

    save_generated_draft(make_draft(), **save_args(database))

    result = save_generated_draft(
        make_draft(draft_id="draft-other"),
        **save_args(database, asset_id="asset-test-002"),
    )

    assert result["version"] == 1


def test_saved_asset_remains_unapproved_draft(tmp_path):
    database = tmp_path / "history.sqlite3"

    result = save_generated_draft(
        make_draft(),
        **save_args(database),
    )

    assert result["readiness_status"] == ReadinessStatus.DRAFT.value
    assert result["usefulness_review"] == ReviewStatus.PENDING.value
    assert result["accuracy_review"] == ReviewStatus.PENDING.value
    assert result["rights_review"] == ReviewStatus.PENDING.value


def test_invalid_metadata_does_not_save_history(tmp_path):
    database = tmp_path / "history.sqlite3"

    with pytest.raises(ValueError):
        save_generated_draft(
            make_draft(),
            **save_args(database, utm_url="not-a-url"),
        )

    assert AssetHistory(database).get_history("asset-test-001") == []


def test_short_video_requires_video_asset_format(tmp_path):
    database = tmp_path / "history.sqlite3"
    draft = make_draft(content_format=ContentFormat.SHORT_VIDEO)

    with pytest.raises(ValueError, match="short_video"):
        save_generated_draft(
            draft,
            **save_args(database, asset_format="graphic"),
        )

    assert AssetHistory(database).get_history("asset-test-001") == []


def test_non_draft_input_is_rejected(tmp_path):
    with pytest.raises(TypeError, match="GeneratedDraft"):
        save_generated_draft(
            {"draft_id": "not-validated"},
            **save_args(tmp_path / "history.sqlite3"),
        )


def test_missing_required_metadata_is_rejected(tmp_path):
    database = tmp_path / "history.sqlite3"
    args = save_args(database)
    args.pop("source_id")

    with pytest.raises(TypeError, match="source_id"):
        save_generated_draft(make_draft(), **args)

    assert AssetHistory(database).get_history("asset-test-001") == []


def test_video_asset_requires_explicit_duration_and_aspect_ratio(tmp_path):
    database = tmp_path / "history.sqlite3"
    draft = make_draft(content_format=ContentFormat.SHORT_VIDEO)

    with pytest.raises(ValueError, match="video_duration_seconds"):
        save_generated_draft(
            draft,
            **save_args(
                database,
                asset_format="video",
            ),
        )

    assert AssetHistory(database).get_history("asset-test-001") == []


def test_video_asset_saves_when_video_metadata_is_supplied(tmp_path):
    database = tmp_path / "history.sqlite3"
    draft = make_draft(content_format=ContentFormat.SHORT_VIDEO)

    result = save_generated_draft(
        draft,
        **save_args(
            database,
            asset_format="video",
            video_duration_seconds=20,
            aspect_ratio="9:16",
        ),
    )

    assert result["status"] == "SAVED"
    assert result["version"] == 1

    snapshot = AssetHistory(database).get_history("asset-test-001")[0]
    assert snapshot["snapshot"]["video_duration_seconds"] == 20
    assert snapshot["snapshot"]["aspect_ratio"] == "9:16"
