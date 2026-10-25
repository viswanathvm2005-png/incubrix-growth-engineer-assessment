"""CLI tests for the human review commands."""

import json

import pytest

from engine import __main__ as cli


class FakeReviewStore:
    """Isolate CLI argument handling from SQLite storage tests."""

    last_instance = None

    def __init__(self, database_path):
        self.database_path = database_path
        self.calls = []
        FakeReviewStore.last_instance = self

    def submit_output(self, output_path):
        self.calls.append(("submit_output", output_path))
        return {
            "status": "SUBMITTED",
            "output": output_path,
            "drafts": [],
        }

    def list_reviews(self, status=None):
        self.calls.append(("list_reviews", status))
        return {"count": 0, "reviews": []}

    def show_review(self, brief_id, draft_id):
        self.calls.append(("show_review", brief_id, draft_id))
        return {
            "brief_id": brief_id,
            "draft_id": draft_id,
            "status": "pending",
        }

    def decide(self, brief_id, draft_id, decision, reviewer, feedback=""):
        self.calls.append(
            ("decide", brief_id, draft_id, decision, reviewer, feedback)
        )
        return {
            "brief_id": brief_id,
            "draft_id": draft_id,
            "status": decision,
            "reviewer": reviewer,
            "feedback": feedback,
        }


@pytest.fixture
def fake_store(monkeypatch):
    FakeReviewStore.last_instance = None
    monkeypatch.setattr(cli, "ReviewStore", FakeReviewStore)
    return FakeReviewStore


def invoke_cli(args, capsys):
    exit_code = cli.main(args)
    output = capsys.readouterr().out
    return exit_code, json.loads(output)


def test_review_submit(fake_store, capsys):
    code, result = invoke_cli(
        ["review", "submit", "--output", "outputs/example.json",
         "--database", "tmp/reviews.sqlite3"],
        capsys,
    )
    assert code == 0
    assert result["status"] == "SUBMITTED"
    assert FakeReviewStore.last_instance.database_path == "tmp/reviews.sqlite3"
    assert FakeReviewStore.last_instance.calls == [
        ("submit_output", "outputs/example.json")
    ]


def test_review_list_all(fake_store, capsys):
    code, result = invoke_cli(["review", "list"], capsys)
    assert code == 0
    assert result["count"] == 0
    assert FakeReviewStore.last_instance.calls == [("list_reviews", None)]


def test_review_list_pending(fake_store, capsys):
    code, result = invoke_cli(
        ["review", "list", "--status", "pending"], capsys
    )
    assert code == 0
    assert result["reviews"] == []
    assert FakeReviewStore.last_instance.calls == [("list_reviews", "pending")]


def test_review_list_rejects_unknown_status(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["review", "list", "--status", "unknown"])
    assert exc.value.code == 2


def test_review_show(fake_store, capsys):
    code, result = invoke_cli(
        ["review", "show", "--brief-id", "brief-1",
         "--draft-id", "draft-1"],
        capsys,
    )
    assert code == 0
    assert result["status"] == "pending"
    assert FakeReviewStore.last_instance.calls == [
        ("show_review", "brief-1", "draft-1")
    ]


def test_review_approve(fake_store, capsys):
    code, result = invoke_cli(
        ["review", "decide", "--brief-id", "brief-1",
         "--draft-id", "draft-1", "--decision", "approved",
         "--reviewer", "Candidate"],
        capsys,
    )
    assert code == 0
    assert result["status"] == "approved"
    assert FakeReviewStore.last_instance.calls == [
        ("decide", "brief-1", "draft-1", "approved", "Candidate", "")
    ]


def test_review_reject_with_feedback(fake_store, capsys):
    code, result = invoke_cli(
        ["review", "decide", "--brief-id", "brief-1",
         "--draft-id", "draft-1", "--decision", "rejected",
         "--reviewer", "Candidate", "--feedback", "Unsupported wording"],
        capsys,
    )
    assert code == 0
    assert result["status"] == "rejected"
    assert result["feedback"] == "Unsupported wording"


def test_review_reject_requires_feedback(fake_store, capsys):
    code, result = invoke_cli(
        ["review", "decide", "--brief-id", "brief-1",
         "--draft-id", "draft-1", "--decision", "rejected",
         "--reviewer", "Candidate"],
        capsys,
    )
    assert code == 1
    assert result["status"] == "ERROR"
    assert "Feedback is required" in result["message"]
    assert FakeReviewStore.last_instance.calls == []


def test_review_decision_requires_reviewer(fake_store, capsys):
    code, result = invoke_cli(
        ["review", "decide", "--brief-id", "brief-1",
         "--draft-id", "draft-1", "--decision", "approved",
         "--reviewer", "   "],
        capsys,
    )
    assert code == 1
    assert result["status"] == "ERROR"
    assert "reviewer identity" in result["message"]
    assert FakeReviewStore.last_instance.calls == []


def test_review_decision_requires_required_arguments():
    with pytest.raises(SystemExit) as exc:
        cli.main(["review", "decide", "--decision", "approved"])
    assert exc.value.code == 2


def test_existing_commands_remain_available():
    parser = cli.build_parser()
    choices = parser._subparsers._group_actions[0].choices
    assert {"intake", "history", "generate", "review"} <= set(choices)
