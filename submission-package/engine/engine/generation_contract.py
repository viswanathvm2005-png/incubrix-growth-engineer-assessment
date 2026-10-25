"""Provider-independent contract for future content generation.

This module defines and validates structured requests and responses only.
It does not call an AI provider, generate content, publish posts, or
establish that a capability is factually true.
"""
from enum import StrEnum
from typing import Self

from pydantic import ConfigDict, Field, field_validator, model_validator

from .content_brief import ContentBrief, ContentFormat
from .schemas import CapabilityReference, StrictModel


class GenerationStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class GenerationRequest(StrictModel):
    """Validated input sent to any future generation provider."""

    request_id: str = Field(min_length=1, max_length=100)
    brief: ContentBrief
    requested_draft_count: int = Field(default=3, ge=1, le=10)

    # These IDs must come from the candidate's validated capability register.
    # An empty list authorizes no product claims.
    authorized_capability_ids: list[str] = Field(default_factory=list)

    @field_validator("request_id")
    @classmethod
    def validate_request_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("request_id must not be blank.")
        return value.strip()

    @field_validator("authorized_capability_ids")
    @classmethod
    def validate_authorized_ids(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("Authorized capability IDs cannot be blank.")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("Authorized capability IDs must be unique.")
        return cleaned

    @model_validator(mode="after")
    def validate_brief_capabilities(self) -> Self:
        unauthorized = (
            set(self.brief.capability_ids)
            - set(self.authorized_capability_ids)
        )
        if unauthorized:
            raise ValueError(
                "Brief references capability IDs not present in the "
                "authorized capability list: "
                + ", ".join(sorted(unauthorized))
            )
        return self


class GeneratedDraft(StrictModel):
    """One proposed content draft. This is not an approved ContentAsset."""

    draft_id: str = Field(min_length=1, max_length=100)
    content_format: ContentFormat
    angle: str = Field(min_length=1, max_length=500)
    hook: str = Field(min_length=1, max_length=500)
    caption: str = Field(min_length=1, max_length=5000)
    call_to_action: str = Field(min_length=1, max_length=500)
    hashtags: list[str] = Field(default_factory=list)
    product_claims: list[CapabilityReference] = Field(default_factory=list)

    # Ordered spoken/narrated script beats, required for short-video drafts.
    video_script: list[str] | None = None

    @field_validator("draft_id", "angle", "hook", "caption", "call_to_action")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Text fields cannot be blank.")
        return value.strip()

    @field_validator("hashtags")
    @classmethod
    def validate_hashtags(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("Hashtags cannot contain blank values.")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("Hashtags must be unique.")
        return cleaned

    @field_validator("video_script")
    @classmethod
    def validate_script_beats(
        cls,
        values: list[str] | None,
    ) -> list[str] | None:
        if values is None:
            return None
        cleaned = [value.strip() for value in values]
        if not cleaned or any(not value for value in cleaned):
            raise ValueError("Video scripts need non-blank script beats.")
        return cleaned


class GenerationResult(StrictModel):
    """Structured provider response, not proof of factual accuracy."""

    brief_id: str = Field(min_length=1, max_length=100)
    status: GenerationStatus
    drafts: list[GeneratedDraft] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    # Optional metadata; unknown values remain null rather than invented.
    provider_name: str | None = None
    model_name: str | None = None

    @model_validator(mode="after")
    def validate_status_and_drafts(self) -> Self:
        if self.status == GenerationStatus.SUCCESS and not self.drafts:
            raise ValueError("A successful result must contain at least one draft.")
        if self.status == GenerationStatus.FAILED and self.drafts:
            raise ValueError("A failed result cannot contain publishable drafts.")
        return self


def validate_generation_result(
    request: GenerationRequest,
    result: GenerationResult,
) -> GenerationResult:
    """Check a response against its request and authorized capability IDs.

    This is a structural authorization check, not semantic fact verification.
    It does not prove that a claim is supported by the referenced evidence.
    """
    if result.brief_id != request.brief.brief_id:
        raise ValueError("Result brief_id does not match the request brief.")

    if len(result.drafts) > request.requested_draft_count:
        raise ValueError("Result contains more drafts than requested.")

    draft_ids = [draft.draft_id for draft in result.drafts]
    if len(draft_ids) != len(set(draft_ids)):
        raise ValueError("Result contains duplicate draft IDs.")

    for field_name in ("hook", "caption"):
        normalized_values = [
            " ".join(getattr(draft, field_name).casefold().split())
            for draft in result.drafts
        ]
        if len(normalized_values) != len(set(normalized_values)):
            raise ValueError(
                f"Result contains duplicate {field_name} content."
            )

    authorized = set(request.authorized_capability_ids)

    for draft in result.drafts:
        if draft.content_format != request.brief.content_format:
            raise ValueError(
                f"Draft {draft.draft_id} has a format different from the brief."
            )

        if request.brief.content_format == ContentFormat.SHORT_VIDEO:
            if not draft.video_script:
                raise ValueError(
                    f"Short-video draft {draft.draft_id} needs a video script."
                )
        elif draft.video_script is not None:
            raise ValueError(
                f"Non-video draft {draft.draft_id} cannot contain a video script."
            )

        for claim in draft.product_claims:
            claim_ids = set(claim.capability_ids)
            if not claim_ids.issubset(authorized):
                raise ValueError(
                    f"Draft {draft.draft_id} contains a claim referencing "
                    "unauthorized capability IDs: "
                    + ", ".join(sorted(claim_ids - authorized))
                )

            if not claim_ids.issubset(set(request.brief.capability_ids)):
                raise ValueError(
                    f"Draft {draft.draft_id} references capability IDs "
                    "not requested by the brief."
                )

    return result


