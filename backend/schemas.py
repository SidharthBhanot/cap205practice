from datetime import date, datetime, timezone
from typing import Annotated
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .constants import ObligationStatus, ObligationType, ReviewStatus, SourceType

PositiveID = Annotated[int, Field(gt=0)]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("reference_url", check_fields=False)
    @classmethod
    def safe_url(cls, value):
        if not value:
            return None
        value = value.strip()
        parsed = urlsplit(value)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username:
            raise ValueError("Use an absolute http:// or https:// URL without credentials.")
        return value


class CourseCreate(InputModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=160)

    @field_validator("code", "name")
    @classmethod
    def not_blank(cls, value, info):
        value = value.strip()
        if not value:
            raise ValueError("Must not be blank.")
        return value.upper() if info.field_name == "code" else value


class SourceWrite(InputModel):
    name: str = Field(min_length=1, max_length=120)
    source_type: SourceType
    description: str = Field(default="", max_length=10000)
    reference_url: str | None = Field(default=None, max_length=2048)
    last_checked_at: datetime | None = None

    @field_validator("name")
    @classmethod
    def not_blank(cls, value):
        if not value.strip():
            raise ValueError("Source name must not be blank.")
        return value.strip()

    @field_validator("last_checked_at")
    @classmethod
    def utc_timestamp(cls, value):
        if value:
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
            if value > datetime.now(timezone.utc).replace(tzinfo=None):
                raise ValueError("Last checked cannot be in the future.")
        return value


class ObligationWrite(InputModel):
    course_id: PositiveID | None = None
    source_id: PositiveID
    # Blank titles and missing course/type are permitted as incomplete source records.
    title: str = Field(default="", max_length=240)
    description: str = Field(default="", max_length=20000)
    obligation_type: ObligationType | None = None
    deadline: date | None = None
    status: ObligationStatus = ObligationStatus.PLANNED
    reference_url: str | None = Field(default=None, max_length=2048)


class ReviewUpdate(InputModel):
    status: ReviewStatus
    resolution_notes: str = Field(default="", max_length=10000)
