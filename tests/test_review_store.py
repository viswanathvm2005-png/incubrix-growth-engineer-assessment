import json

import pytest

from engine.review_store import ReviewStore


def make_output(path, *, brief_id="brief-1", draft_id="draft-1", caption="Sample caption"):
    path.write_text(
        json.dumps({
            "brief_id": brief_id,
            "status": "success",
            "provider_name": "mock",
            "model_name": None,
            "warnings": [],
            "drafts": [{
                "draft_id": draft_id,
                "content_format": "static_post",
                "angle": "A sample angle",
                "hook": "A sample hook",
                "caption": caption,
                "call_to_action": "Review this sample",
                "hashtags": [],
                "product_claims": [],
                "video_script": None
            }]
        }),
        encoding="utf-8",
    )
    return path


def test_submit_creates_pending_review(tmp_path):
    output = make_output(tmp_path / "output.json")
    store = ReviewStore(tmp_path / "reviews.sqlite3")

    result = store.submit_output(output)

    assert result["status"] == "SUBMITTED"
    assert result["drafts"][0]["status"] == "pending"
    assert result["drafts"][0]["action"] == "submitted"
    assert store.list_reviews("pending")["count"] == 1


def test_resubmitting_same_draft_is_idempotent(tmp_path):
    output = make_output(tmp_path / "output.json")
    store = ReviewStore(tmp_path / "reviews.sqlite3")

    store.submit_output(output)
    result = store.submit_output(output)

    assert result["drafts"][0]["action"] == "already_submitted"
    assert store.list_reviews()["count"] == 1


def test_changed_content_cannot_reuse_draft_identity(tmp_path):
    output = make_output(tmp_path / "output.json")
    store = ReviewStore(tmp_path / "reviews.sqlite3")
    store.submit_output(output)

    make_output(output, caption="Changed caption")

    with pytest.raises(ValueError, match="identity collision"):
        store.submit_output(output)


def test_failed_generation_cannot_enter_review(tmp_path):
    output = make_output(tmp_path / "output.json")
    data = json.loads(output.read_text(encoding="utf-8"))
    data["status"] = "failed"
    data["drafts"] = []
    output.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="successful"):
        ReviewStore(tmp_path / "reviews.sqlite3").submit_output(output)


def test_approve_records_reviewer_and_timestamp(tmp_path):
    output = make_output(tmp_path / "output.json")
    store = ReviewStore(tmp_path / "reviews.sqlite3")
    store.submit_output(output)

    result = store.decide("brief-1", "draft-1", "approved", "Reviewer A")

    assert result["status"] == "approved"
    assert result["reviewer"] == "Reviewer A"
    assert result["decided_at"]
    assert store.list_reviews("approved")["count"] == 1


def test_rejection_requires_feedback(tmp_path):
    output = make_output(tmp_path / "output.json")
    store = ReviewStore(tmp_path / "reviews.sqlite3")
    store.submit_output(output)

    with pytest.raises(ValueError, match="Feedback is required"):
        store.decide("brief-1", "draft-1", "rejected", "Reviewer A")


def test_decision_requires_reviewer(tmp_path):
    output = make_output(tmp_path / "output.json")
    store = ReviewStore(tmp_path / "reviews.sqlite3")
    store.submit_output(output)

    with pytest.raises(ValueError, match="reviewer identity"):
        store.decide("brief-1", "draft-1", "approved", " ")


def test_final_decision_cannot_be_overwritten(tmp_path):
    output = make_output(tmp_path / "output.json")
    store = ReviewStore(tmp_path / "reviews.sqlite3")
    store.submit_output(output)
    store.decide("brief-1", "draft-1", "approved", "Reviewer A")

    with pytest.raises(ValueError, match="already approved"):
        store.decide(
            "brief-1", "draft-1", "rejected", "Reviewer B", "Changed mind"
        )


def test_show_returns_stored_draft_and_review(tmp_path):
    output = make_output(tmp_path / "output.json", caption="Exact stored caption")
    store = ReviewStore(tmp_path / "reviews.sqlite3")
    store.submit_output(output)

    record = store.show_review("brief-1", "draft-1")

    assert record["draft"]["caption"] == "Exact stored caption"
    assert record["status"] == "pending"
    assert len(record["content_sha256"]) == 64


def test_missing_review_raises_error(tmp_path):
    store = ReviewStore(tmp_path / "reviews.sqlite3")

    with pytest.raises(ValueError, match="not found"):
        store.show_review("missing", "missing")


def test_invalid_status_filter_is_rejected(tmp_path):
    store = ReviewStore(tmp_path / "reviews.sqlite3")

    with pytest.raises(ValueError, match="status must be"):
        store.list_reviews("ready")


def test_review_survives_reopening_database(tmp_path):
    output = make_output(tmp_path / "output.json")
    database = tmp_path / "reviews.sqlite3"
    ReviewStore(database).submit_output(output)

    reopened = ReviewStore(database)

    assert reopened.list_reviews("pending")["count"] == 1
