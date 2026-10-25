import json
from pathlib import Path

import pytest

from engine.asset_history import (
    AssetHistory,
    DEFAULT_DUPLICATE_THRESHOLD,
    similarity_score,
    stable_asset_id,
    text_fingerprint,
)
from engine.schemas import AssetFormat, ContentAsset, Platform


def make_asset(
    *,
    asset_id="asset-test-001",
    version=1,
    source_id="source-test-001",
    platform=Platform.LINKEDIN,
    angle="educational explanation",
    hook="A verified sample hook",
    caption="A sample caption explaining a general concept.",
):
    return ContentAsset(
        asset_id=asset_id,
        version=version,
        source_id=source_id,
        platform=platform,
        format=AssetFormat.TEXT,
        angle=angle,
        hook=hook,
        caption=caption,
        cta="Learn more",
        utm_url="https://example.com/?utm_source=asset_history_test",
        target_metric="clicks",
        created_by_run_id=f"run-test-{version}",
    )


def test_stable_asset_id_is_deterministic():
    first = stable_asset_id("source-1", "LinkedIn", "Educational angle")
    second = stable_asset_id("source-1", "linkedin", "Educational angle")
    assert first == second
    assert first.startswith("asset-")


def test_stable_asset_id_changes_when_source_platform_or_angle_changes():
    baseline = stable_asset_id("source-1", "linkedin", "education")
    assert stable_asset_id("source-2", "linkedin", "education") != baseline
    assert stable_asset_id("source-1", "instagram", "education") != baseline
    assert stable_asset_id("source-1", "linkedin", "case study") != baseline


@pytest.mark.parametrize(
    "source_id,platform,angle",
    [
        ("", "linkedin", "education"),
        ("source", "", "education"),
        ("source", "linkedin", "   "),
    ],
)
def test_stable_asset_id_rejects_empty_identity_fields(source_id, platform, angle):
    with pytest.raises(ValueError):
        stable_asset_id(source_id, platform, angle)


def test_text_fingerprint_ignores_case_and_punctuation():
    assert text_fingerprint("Hello, WORLD!") == text_fingerprint("hello world")


def test_similarity_score_boundaries():
    assert similarity_score("same text", "same text") == 1.0
    assert similarity_score("", "some text") == 0.0
    assert 0.0 <= similarity_score("alpha beta", "alpha gamma") <= 1.0


def test_save_and_retrieve_one_asset(tmp_path):
    history = AssetHistory(tmp_path / "history.sqlite3")
    asset = make_asset()

    result = history.save(asset)
    records = history.get_history(asset.asset_id)

    assert result["status"] == "SAVED"
    assert result["version"] == 1
    assert len(records) == 1
    assert records[0]["snapshot"]["asset_id"] == asset.asset_id
    assert records[0]["snapshot"]["version"] == 1


def test_history_survives_reopening_database(tmp_path):
    database = tmp_path / "persistent-history.sqlite3"
    AssetHistory(database).save(make_asset())

    reopened = AssetHistory(database)
    records = reopened.get_history("asset-test-001")

    assert len(records) == 1
    assert records[0]["caption"] == "A sample caption explaining a general concept."


def test_revisions_append_and_preserve_earlier_snapshot(tmp_path):
    history = AssetHistory(tmp_path / "history.sqlite3")
    original = make_asset()
    revised = make_asset(
        version=2,
        hook="A revised verified sample hook",
        caption="A revised sample caption with additional explanation.",
    )

    history.save(original)
    history.save(revised)
    records = history.get_history(original.asset_id)

    assert [item["version"] for item in records] == [1, 2]
    assert records[0]["hook"] == "A verified sample hook"
    assert records[1]["hook"] == "A revised verified sample hook"


@pytest.mark.parametrize(
    "first_version,next_version",
    [(2, 3), (1, 1), (1, 3)],
)
def test_save_rejects_invalid_version_sequence(tmp_path, first_version, next_version):
    history = AssetHistory(tmp_path / "history.sqlite3")
    first = make_asset(version=first_version)

    if first_version != 1:
        with pytest.raises(ValueError, match="first saved version"):
            history.save(first)
        return

    history.save(first)
    next_asset = make_asset(version=next_version)
    with pytest.raises(ValueError, match="Expected version"):
        history.save(next_asset)


def test_latest_assets_returns_only_latest_version(tmp_path):
    history = AssetHistory(tmp_path / "history.sqlite3")
    history.save(make_asset())
    history.save(make_asset(version=2, hook="A revised hook"))

    latest = history.latest_assets()

    assert len(latest) == 1
    assert latest[0]["version"] == 2


def test_exact_duplicate_is_flagged_for_human_review(tmp_path):
    history = AssetHistory(tmp_path / "history.sqlite3")
    original = make_asset()
    history.save(original)

    candidate = make_asset(
        asset_id="asset-test-002",
        source_id="source-test-002",
    )
    report = history.check_duplicates(candidate)

    assert report.status == "REVIEW_REQUIRED"
    assert len(report.matches) == 1
    assert report.matches[0].score == 1.0
    assert "Human review" in report.message
    assert len(history.get_history(original.asset_id)) == 1


def test_different_content_does_not_match_high_threshold(tmp_path):
    history = AssetHistory(tmp_path / "history.sqlite3")
    history.save(make_asset())

    candidate = make_asset(
        asset_id="asset-test-002",
        hook="How to plan an entirely different project",
        caption="A distinct explanation about a different topic.",
    )
    report = history.check_duplicates(candidate, threshold=0.99)

    assert report.status == "NO_MATCH_FOUND"
    assert report.matches == ()


def test_duplicate_check_excludes_same_logical_asset(tmp_path):
    history = AssetHistory(tmp_path / "history.sqlite3")
    history.save(make_asset())

    revised = make_asset(version=2, hook="A revised hook")
    report = history.check_duplicates(revised)

    assert all(match.asset_id != revised.asset_id for match in report.matches)


def test_duplicate_threshold_must_be_between_zero_and_one(tmp_path):
    history = AssetHistory(tmp_path / "history.sqlite3")
    with pytest.raises(ValueError, match="threshold"):
        history.check_duplicates(make_asset(asset_id="candidate"), threshold=1.1)


def test_empty_history_returns_no_match(tmp_path):
    history = AssetHistory(tmp_path / "history.sqlite3")
    report = history.check_duplicates(make_asset())

    assert report.status == "NO_MATCH_FOUND"
    assert report.matches == ()


def test_duplicate_report_does_not_mutate_or_delete_assets(tmp_path):
    history = AssetHistory(tmp_path / "history.sqlite3")
    history.save(make_asset())
    history.save(
        make_asset(
            asset_id="asset-test-002",
            source_id="source-test-002",
        )
    )

    report = history.check_duplicates(
        make_asset(asset_id="asset-test-003", source_id="source-test-003")
    )

    assert report.status == "REVIEW_REQUIRED"
    assert len(history.get_history("asset-test-001")) == 1
    assert len(history.get_history("asset-test-002")) == 1


def test_default_duplicate_threshold_is_explicit():
    assert DEFAULT_DUPLICATE_THRESHOLD == 0.85
