"""Version request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UploadVersionRequest(BaseModel):
    """Schema for uploading a new schema version."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    schema_data: dict = Field(alias="schema_json")
    change_reason: str | None = Field(default=None, max_length=500)

    @field_validator("schema_data")
    @classmethod
    def must_be_object(cls, v: dict) -> dict:
        """Validate that schema_json is a valid schema object."""
        if not isinstance(v, dict):
            raise ValueError("schema_json must be a JSON object")
        if "properties" not in v and "paths" not in v:
            raise ValueError("schema must have properties or paths key")
        return v


class VersionResponse(BaseModel):
    """Schema for a version in API responses."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: str
    version: str
    status: str
    schema_data: dict = Field(alias="schema_json")
    change_reason: str | None
    diff_result: dict | None
    uploaded_at: datetime
