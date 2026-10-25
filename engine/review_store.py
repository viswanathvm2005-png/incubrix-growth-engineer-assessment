"""Persistent human review workflow for generated content drafts."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from .generation_contract import GenerationResult, GenerationStatus


REVIEW_STATUSES = {"pending", "approved", "rejected"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_result(path: str | Path) -> GenerationResult:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        result = GenerationResult.model_validate(raw)
    except (OSError, UnicodeError, json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(
            "Generation output could not be read or does not match its schema."
        ) from exc

    if result.status != GenerationStatus.SUCCESS:
        raise ValueError("Only successful generation results can enter review.")
    if not result.drafts:
        raise ValueError("Generation output contains no drafts.")
    return result


def _draft_payload(draft) -> dict:
    return draft.model_dump(mode="json")


def _draft_hash(draft_json: str) -> str:
    return hashlib.sha256(draft_json.encode("utf-8")).hexdigest()


class ReviewStore:
    """Store immutable draft submissions and their human review decisions."""

    def __init__(self, database_path: str | Path = "data/content-reviews.sqlite3"):
        self.database_path = str(database_path)
        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS content_reviews (
                    brief_id TEXT NOT NULL,
                    draft_id TEXT NOT NULL,
                    content_sha256 TEXT NOT NULL,
                    draft_json TEXT NOT NULL,
                    status TEXT NOT NULL
                        CHECK (status IN ('pending', 'approved', 'rejected')),
                    reviewer TEXT,
                    feedback TEXT,
                    submitted_at TEXT NOT NULL,
                    decided_at TEXT,
                    PRIMARY KEY (brief_id, draft_id)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_content_reviews_status
                ON content_reviews(status, submitted_at)
                """
            )

    def submit_output(self, output_path: str | Path) -> dict:
        """Submit all drafts from one saved successful generation result."""
        result = _read_result(output_path)
        submitted: list[dict] = []

        with self._connect() as connection:
            for draft in result.drafts:
                payload = _draft_payload(draft)
                draft_json = json.dumps(
                    payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                )
                digest = _draft_hash(draft_json)

                existing = connection.execute(
                    """
                    SELECT content_sha256, status
                    FROM content_reviews
                    WHERE brief_id = ? AND draft_id = ?
                    """,
                    (result.brief_id, draft.draft_id),
                ).fetchone()

                if existing is not None:
                    if existing["content_sha256"] != digest:
                        raise ValueError(
                            f"Draft identity collision for {draft.draft_id!r}: "
                            "content changed. Use a new draft_id for a revision."
                        )
                    submitted.append({
                        "draft_id": draft.draft_id,
                        "status": existing["status"],
                        "action": "already_submitted",
                    })
                    continue

                connection.execute(
                    """
                    INSERT INTO content_reviews (
                        brief_id, draft_id, content_sha256, draft_json, status,
                        reviewer, feedback, submitted_at, decided_at
                    ) VALUES (?, ?, ?, ?, 'pending', NULL, NULL, ?, NULL)
                    """,
                    (result.brief_id, draft.draft_id, digest, draft_json, _now()),
                )
                submitted.append({
                    "draft_id": draft.draft_id,
                    "status": "pending",
                    "action": "submitted",
                })

        return {
            "status": "SUBMITTED",
            "brief_id": result.brief_id,
            "drafts": submitted,
            "message": "Submission is not approval. Human review is still required.",
        }

    def list_reviews(self, status: str | None = None) -> dict:
        """List review records, optionally filtered by review status."""
        if status is not None and status not in REVIEW_STATUSES:
            raise ValueError("status must be pending, approved, or rejected.")

        query = """
            SELECT brief_id, draft_id, status, reviewer, feedback,
                   submitted_at, decided_at
            FROM content_reviews
        """
        parameters: tuple = ()
        if status is not None:
            query += " WHERE status = ?"
            parameters = (status,)
        query += " ORDER BY submitted_at, brief_id, draft_id"

        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()

        return {"count": len(rows), "reviews": [dict(row) for row in rows]}

    def show_review(self, brief_id: str, draft_id: str) -> dict:
        """Show the stored draft and its review record."""
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT brief_id, draft_id, content_sha256, draft_json, status,
                       reviewer, feedback, submitted_at, decided_at
                FROM content_reviews
                WHERE brief_id = ? AND draft_id = ?
                """,
                (brief_id, draft_id),
            ).fetchone()

        if row is None:
            raise ValueError("Review record was not found.")

        record = dict(row)
        record["draft"] = json.loads(record.pop("draft_json"))
        return record

    def decide(
        self,
        brief_id: str,
        draft_id: str,
        decision: str,
        reviewer: str,
        feedback: str = "",
    ) -> dict:
        """Record one final decision; decisions cannot silently be overwritten."""
        if decision not in {"approved", "rejected"}:
            raise ValueError("decision must be approved or rejected.")
        if not reviewer.strip():
            raise ValueError("A non-empty reviewer identity is required.")
        if decision == "rejected" and not feedback.strip():
            raise ValueError("Feedback is required when rejecting a draft.")

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT status FROM content_reviews
                WHERE brief_id = ? AND draft_id = ?
                """,
                (brief_id, draft_id),
            ).fetchone()

            if row is None:
                raise ValueError("Review record was not found.")
            if row["status"] != "pending":
                raise ValueError(
                    f"This review is already {row['status']}; "
                    "create a new draft revision for another review."
                )

            decided_at = _now()
            connection.execute(
                """
                UPDATE content_reviews
                SET status = ?, reviewer = ?, feedback = ?, decided_at = ?
                WHERE brief_id = ? AND draft_id = ? AND status = 'pending'
                """,
                (
                    decision,
                    reviewer.strip(),
                    feedback.strip(),
                    decided_at,
                    brief_id,
                    draft_id,
                ),
            )

        return {
            "status": decision,
            "brief_id": brief_id,
            "draft_id": draft_id,
            "reviewer": reviewer.strip(),
            "feedback": feedback.strip(),
            "decided_at": decided_at,
        }
