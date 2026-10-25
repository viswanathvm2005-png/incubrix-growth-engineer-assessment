"""Local asset identity, revision history, and duplicate review utilities.

This module does not generate content, publish assets, or delete duplicates.
Duplicate matches are suggestions for human review only.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable

from .schemas import ContentAsset


DEFAULT_DUPLICATE_THRESHOLD = 0.85


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_text(value: str) -> str:
    """Normalize text for deterministic identity and similarity comparisons."""
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.findall(r"\w+", value, flags=re.UNICODE))


def stable_asset_id(
    source_id: str,
    platform: str,
    angle: str,
) -> str:
    """Return a stable ID for a source/platform/angle combination."""
    parts = (
        source_id.strip(),
        platform.strip().casefold(),
        _canonical_text(angle),
    )
    if any(not part for part in parts):
        raise ValueError("source_id, platform, and angle must be non-empty.")

    canonical = json.dumps(parts, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]
    return f"asset-{digest}"


def text_fingerprint(text: str) -> str:
    """Return a deterministic SHA-256 fingerprint of normalized text."""
    normalized = _canonical_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def similarity_score(left: str, right: str) -> float:
    """Compute normalized character-sequence similarity in the range 0..1."""
    a = _canonical_text(left)
    b = _canonical_text(right)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


@dataclass(frozen=True)
class DuplicateMatch:
    asset_id: str
    version: int
    score: float
    reason: str


@dataclass(frozen=True)
class DuplicateReport:
    status: str
    threshold: float
    matches: tuple[DuplicateMatch, ...]
    message: str


class AssetHistory:
    """SQLite-backed history of asset snapshots.

    Each save appends a snapshot. Revisions of the same asset_id must use a
    strictly increasing version. Existing snapshots are never overwritten.
    """

    def __init__(self, database_path: str | Path):
        self.database_path = str(database_path)
        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS asset_history (
                    asset_id TEXT NOT NULL,
                    version INTEGER NOT NULL CHECK (version >= 1),
                    source_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    angle TEXT NOT NULL,
                    hook TEXT NOT NULL,
                    caption TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    snapshot_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (asset_id, version)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_asset_history_fingerprint
                ON asset_history(fingerprint)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_asset_history_source
                ON asset_history(source_id, platform, angle)
                """
            )

    @staticmethod
    def _asset_text(asset: ContentAsset) -> str:
        return f"{asset.hook}\n{asset.caption}"

    def save(self, asset: ContentAsset) -> dict[str, object]:
        """Append one asset version; reject duplicate version writes."""
        payload = asset.model_dump(mode="json")
        fingerprint = text_fingerprint(self._asset_text(asset))

        # Keep the serialized snapshot consistent with the indexed fingerprint.
        payload["fingerprint"] = fingerprint
        snapshot_json = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        with self._connect() as connection:
            latest = connection.execute(
                """
                SELECT MAX(version) AS latest_version
                FROM asset_history WHERE asset_id = ?
                """,
                (asset.asset_id,),
            ).fetchone()
            latest_version = latest["latest_version"]

            if latest_version is None and asset.version != 1:
                raise ValueError(
                    "The first saved version of an asset must be version 1."
                )
            if latest_version is not None and asset.version != latest_version + 1:
                raise ValueError(
                    f"Expected version {latest_version + 1} for asset "
                    f"{asset.asset_id!r}, received {asset.version}."
                )

            connection.execute(
                """
                INSERT INTO asset_history (
                    asset_id, version, source_id, platform, angle, hook,
                    caption, fingerprint, snapshot_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    asset.asset_id,
                    asset.version,
                    asset.source_id,
                    asset.platform.value,
                    asset.angle,
                    asset.hook,
                    asset.caption,
                    fingerprint,
                    snapshot_json,
                    _utc_now(),
                ),
            )

        return {
            "status": "SAVED",
            "asset_id": asset.asset_id,
            "version": asset.version,
            "fingerprint": fingerprint,
        }

    def get_history(self, asset_id: str) -> list[dict[str, object]]:
        """Return all snapshots for one logical asset, oldest first."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT asset_id, version, source_id, platform, angle, hook,
                       caption, fingerprint, snapshot_json, created_at
                FROM asset_history
                WHERE asset_id = ?
                ORDER BY version ASC
                """,
                (asset_id,),
            ).fetchall()

        return [
            {
                "asset_id": row["asset_id"],
                "version": row["version"],
                "source_id": row["source_id"],
                "platform": row["platform"],
                "angle": row["angle"],
                "hook": row["hook"],
                "caption": row["caption"],
                "fingerprint": row["fingerprint"],
                "snapshot": json.loads(row["snapshot_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def latest_assets(self, exclude_asset_id: str | None = None) -> list[dict[str, object]]:
        """Return only each logical asset's latest saved version."""
        query = """
            SELECT h.asset_id, h.version, h.source_id, h.platform, h.angle,
                   h.hook, h.caption, h.fingerprint, h.created_at
            FROM asset_history h
            JOIN (
                SELECT asset_id, MAX(version) AS max_version
                FROM asset_history
                GROUP BY asset_id
            ) latest
              ON latest.asset_id = h.asset_id
             AND latest.max_version = h.version
        """
        parameters: tuple[object, ...] = ()
        if exclude_asset_id is not None:
            query += " WHERE h.asset_id != ?"
            parameters = (exclude_asset_id,)
        query += " ORDER BY h.asset_id"

        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()

        return [dict(row) for row in rows]

    def check_duplicates(
        self,
        asset: ContentAsset,
        *,
        threshold: float = DEFAULT_DUPLICATE_THRESHOLD,
    ) -> DuplicateReport:
        """Flag similar latest assets for review; never deletes or blocks them."""
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be between 0.0 and 1.0.")

        candidate_text = self._asset_text(asset)
        candidate_fingerprint = text_fingerprint(candidate_text)
        matches: list[DuplicateMatch] = []

        for existing in self.latest_assets(exclude_asset_id=asset.asset_id):
            existing_text = f"{existing['hook']}\n{existing['caption']}"
            existing_fingerprint = str(existing["fingerprint"])
            score = (
                1.0
                if candidate_fingerprint == existing_fingerprint
                else similarity_score(candidate_text, existing_text)
            )
            if score >= threshold:
                reason = (
                    "Exact normalized text fingerprint match."
                    if score == 1.0
                    else "Text similarity met or exceeded the review threshold."
                )
                matches.append(
                    DuplicateMatch(
                        asset_id=str(existing["asset_id"]),
                        version=int(existing["version"]),
                        score=round(score, 4),
                        reason=reason,
                    )
                )

        matches.sort(key=lambda item: (-item.score, item.asset_id))
        if matches:
            return DuplicateReport(
                status="REVIEW_REQUIRED",
                threshold=threshold,
                matches=tuple(matches),
                message=(
                    "Potential duplicates found. Human review is required; "
                    "no content was deleted or automatically rejected."
                ),
            )

        return DuplicateReport(
            status="NO_MATCH_FOUND",
            threshold=threshold,
            matches=(),
            message=(
                "No saved latest asset met the similarity threshold. "
                "This does not guarantee that the content is unique."
            ),
        )

