import json

from engine.asset_history import AssetHistory, text_fingerprint
from engine.schemas import ContentAsset


def test_saved_snapshot_contains_the_same_fingerprint_as_history(tmp_path):
    database = tmp_path / "fingerprint-test.sqlite3"
    history = AssetHistory(database)

    asset = ContentAsset.model_validate(
        {
            "asset_id": "fingerprint-regression-asset",
            "version": 1,
            "source_id": "fingerprint-test-source",
            "platform": "linkedin",
            "format": "text",
            "angle": "Test fingerprint consistency",
            "hook": "A sample hook for testing.",
            "caption": "A sample caption for testing.",
            "hashtags": ["#sample"],
            "cta": "Review the sample",
            "utm_url": "https://example.com/test",
            "target_metric": "clicks",
            "final_file": None,
            "editable_source_file": None,
            "product_claims": [],
            "video_duration_seconds": None,
            "aspect_ratio": None,
            "usefulness_review": "pending",
            "accuracy_review": "pending",
            "rights_review": "pending",
            "created_by_run_id": "fingerprint-regression-test",
            "readiness_status": "draft",
        }
    )

    saved = history.save(asset)
    versions = history.get_history(asset.asset_id)

    assert saved["status"] == "SAVED"
    assert len(versions) == 1

    version = versions[0]
    snapshot = version["snapshot"]
    expected = text_fingerprint(f"{asset.hook}\n{asset.caption}")

    assert version["fingerprint"] == expected
    assert snapshot["fingerprint"] == expected
    assert snapshot["fingerprint"] == version["fingerprint"]
