"""Registry request and response schemas."""

from datetime import datetime

import re

from pydantic import BaseModel, Field, field_validator


class CreateRegistryRequest(BaseModel):
    """Schema for creating an API registry."""

    name: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9_-]+$")
    description: str | None = Field(default=None, max_length=500)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        """Normalize API names into a safe slug before validation."""
        if not isinstance(value, str):
            return value
        normalized = value.strip().lower()
        normalized = re.sub(r"\s+", "-", normalized)
        normalized = re.sub(r"[^a-z0-9_-]", "-", normalized)
        normalized = re.sub(r"-{2,}", "-", normalized)
        return normalized.strip("-_")


class RegistryResponse(BaseModel):
    """Schema for a single registry in API responses."""

    id: str
    name: str
    description: str | None
    public_token: str
    created_at: datetime
    version_count: int


class RegistryListResponse(BaseModel):
    """Schema for a list of registries."""

    registries: list[RegistryResponse]
    total: int
