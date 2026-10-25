"""Schema contracts for the IncuBrix Option 2 content engine.

This module validates data structures only. It does not call an LLM,
read source documents, generate assets, publish posts, or write to a database.
"""
from datetime import datetime
from enum import StrEnum
from typing import Annotated
import re

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

NonEmptyText = Annotated[str, Field(min_length=1)]
PositiveInt = Annotated[int, Field(ge=1)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, validate_assignment=True)


class Platform(StrEnum):
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    YOUTUBE_SHORTS = "youtube_shorts"
    TIKTOK = "tiktok"
    X = "x"
    THREADS = "threads"
    FACEBOOK = "facebook"
    REDDIT = "reddit"


class AssetFormat(StrEnum):
    TEXT = "text"
    GRAPHIC = "graphic"
    CAROUSEL = "carousel"
    VIDEO = "video"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class CheckStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    NEEDS_HUMAN_REVIEW = "needs_human_review"


class CheckKind(StrEnum):
    AUTOMATED = "automated"
    HUMAN = "human"


class ReadinessStatus(StrEnum):
    DRAFT = "draft"
    BLOCKED = "blocked"
    READY = "ready"


class RunStatus(StrEnum):
    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PARTIAL = "partial"


class SourceDocument(StrictModel):
    source_id: NonEmptyText
    input_path: NonEmptyText
    file_type: str
    sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    received_at: datetime

    @field_validator("file_type")
    @classmethod
    def supported_extension(cls, value: str) -> str:
        normalized = value.lower().lstrip(".")
        if normalized not in {"txt", "md"}:
            raise ValueError("Only .txt and .md inputs are supported.")
        return normalized


class CapabilityReference(StrictModel):
    claim_text: NonEmptyText
    capability_ids: list[NonEmptyText] = Field(min_length=1)

    @field_validator("capability_ids")
    @classmethod
    def unique_capability_ids(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("Duplicate capability IDs are not allowed.")
        return value


class ContentAsset(StrictModel):
    asset_id: NonEmptyText
    version: PositiveInt = 1
    source_id: NonEmptyText
    platform: Platform
    format: AssetFormat
    angle: NonEmptyText
    hook: NonEmptyText
    caption: NonEmptyText
    hashtags: list[str] = Field(default_factory=list)
    cta: NonEmptyText
    utm_url: HttpUrl
    target_metric: NonEmptyText
    scheduled_slot: datetime | None = None
    final_file: str | None = None
    editable_source_file: str | None = None
    product_claims: list[CapabilityReference] = Field(default_factory=list)
    video_duration_seconds: float | None = Field(default=None, gt=0, le=60)
    aspect_ratio: str | None = None
    usefulness_review: ReviewStatus = ReviewStatus.PENDING
    accuracy_review: ReviewStatus = ReviewStatus.PENDING
    rights_review: ReviewStatus = ReviewStatus.PENDING
    fingerprint: str | None = None
    created_by_run_id: NonEmptyText
    readiness_status: ReadinessStatus = ReadinessStatus.DRAFT

    @field_validator("hashtags")
    @classmethod
    def validate_hashtags(cls, values: list[str]) -> list[str]:
        values = [item.strip() for item in values]
        if any(not item for item in values):
            raise ValueError("Hashtags cannot contain empty values.")
        return values

    @field_validator("aspect_ratio")
    @classmethod
    def validate_aspect_ratio(cls, value: str | None) -> str | None:
        if value is not None:
            if not re.fullmatch(r"\d+:\d+", value):
                raise ValueError("Use an aspect ratio such as '9:16'.")
            left, right = map(int, value.split(":"))
            if left <= 0 or right <= 0:
                raise ValueError("Aspect ratio components must be positive.")
        return value

    @model_validator(mode="after")
    def validate_video_fields(self):
        if self.format == AssetFormat.VIDEO:
            if self.video_duration_seconds is None:
                raise ValueError("Video assets require video_duration_seconds.")
            if self.aspect_ratio is None:
                raise ValueError("Video assets require aspect_ratio.")
        elif self.video_duration_seconds is not None:
            raise ValueError("video_duration_seconds is only valid for video assets.")
        return self


class ValidationCheck(StrictModel):
    check_id: NonEmptyText
    kind: CheckKind
    status: CheckStatus
    description: NonEmptyText
    evidence_path: str | None = None
    checked_at: datetime | None = None
    reviewer: str | None = None


class AssetValidationReport(StrictModel):
    asset_id: NonEmptyText
    version: PositiveInt
    checks: list[ValidationCheck] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_human_checks(self):
        for check in self.checks:
            if check.kind == CheckKind.HUMAN and check.status == CheckStatus.PASS:
                if not check.reviewer or not check.checked_at:
                    raise ValueError("Passing human checks require reviewer and checked_at.")
        return self

    @property
    def all_checks_passed(self) -> bool:
        return bool(self.checks) and all(c.status == CheckStatus.PASS for c in self.checks)


class RunRecord(StrictModel):
    run_id: NonEmptyText
    input_path: NonEmptyText
    source_sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    started_at: datetime
    finished_at: datetime | None = None
    status: RunStatus = RunStatus.STARTED
    assets_generated: int = Field(default=0, ge=0)
    assets_validated: int = Field(default=0, ge=0)
    assets_rejected: int = Field(default=0, ge=0)
    runtime_seconds: float | None = Field(default=None, ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    actual_cost_usd: float | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)
    cost_basis: str | None = None
    error_codes: list[str] = Field(default_factory=list)
    log_path: str | None = None

    @model_validator(mode="after")
    def validate_timing(self):
        if self.finished_at is not None and self.finished_at < self.started_at:
            raise ValueError("finished_at cannot precede started_at.")
        return self


class CapabilityEntry(StrictModel):
    capability_id: NonEmptyText
    feature_name: NonEmptyText
    what_I_observed: NonEmptyText
    how_to_reproduce: NonEmptyText
    date_observed: datetime
    evidence_file: NonEmptyText
    confidence: NonEmptyText
    limitations: NonEmptyText
    allowed_claim_wording: list[NonEmptyText] = Field(min_length=1)
    forbidden_wording: list[NonEmptyText] = Field(min_length=1)


class CapabilityRegister(StrictModel):
    capabilities: list[CapabilityEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_unique_ids(self):
        ids = [item.capability_id for item in self.capabilities]
        if len(ids) != len(set(ids)):
            raise ValueError("Capability IDs must be unique.")
        return self
