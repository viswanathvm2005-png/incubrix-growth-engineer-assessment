"""Structured input contract for future marketing content generation.

This module defines campaign inputs only. It does not generate content,
verify product facts, or call an AI provider.
"""
from enum import StrEnum
import re
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Platform(StrEnum):
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    X = "x"
    OTHER = "other"


class ContentFormat(StrEnum):
    STATIC_POST = "static_post"
    CAROUSEL = "carousel"
    SHORT_VIDEO = "short_video"
    STORY = "story"
    TEXT_POST = "text_post"


class ContentBrief(BaseModel):
    """Validated brief describing one requested marketing asset."""

    model_config = ConfigDict(extra="forbid")

    brief_id: str = Field(min_length=1, max_length=100)
    campaign_objective: str = Field(min_length=3, max_length=500)
    target_audience: str = Field(min_length=3, max_length=500)
    platform: Platform
    content_format: ContentFormat

    # IDs refer to candidate-provided source documents and capabilities.
    # This model does not establish that those sources or capabilities exist.
    source_ids: list[str] = Field(min_length=1)
    capability_ids: list[str] = Field(default_factory=list)

    key_message: str | None = Field(default=None, max_length=1000)
    tone: str | None = Field(default=None, max_length=200)
    call_to_action: str | None = Field(default=None, max_length=300)
    avoid_topics: list[str] = Field(default_factory=list)

    # Short-video deliverables must specify duration and aspect ratio.
    # The assessment's agreed short-video limit is 60 seconds.
    requested_duration_seconds: int | None = Field(
        default=None,
        ge=1,
        le=60,
    )
    aspect_ratio: str | None = None

    @field_validator("brief_id", "campaign_objective", "target_audience")
    @classmethod
    def reject_blank_required_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("This field must not be blank.")
        return value.strip()

    @field_validator("source_ids", "capability_ids", "avoid_topics")
    @classmethod
    def normalize_string_lists(cls, values: list[str]) -> list[str]:
        cleaned = []
        for value in values:
            item = value.strip()
            if not item:
                raise ValueError("List entries must not be blank.")
            cleaned.append(item)

        if len(cleaned) != len(set(cleaned)):
            raise ValueError("Duplicate list entries are not allowed.")

        return cleaned

    @field_validator("aspect_ratio")
    @classmethod
    def validate_aspect_ratio(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()
        if not re.fullmatch(r"[1-9]\d*:[1-9]\d*", value):
            raise ValueError(
                "Aspect ratio must use a positive width:height form, "
                "such as 9:16, 1:1, or 16:9."
            )
        return value

    @model_validator(mode="after")
    def validate_video_requirements(self) -> Self:
        if self.content_format == ContentFormat.SHORT_VIDEO:
            if self.requested_duration_seconds is None:
                raise ValueError(
                    "Short videos require requested_duration_seconds."
                )
            if self.aspect_ratio is None:
                raise ValueError("Short videos require aspect_ratio.")
        elif self.requested_duration_seconds is not None:
            raise ValueError(
                "requested_duration_seconds is only for short_video."
            )

        return self
