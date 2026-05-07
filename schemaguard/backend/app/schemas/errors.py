"""Shared Pydantic validation error formatting."""

from pydantic import ValidationError


def format_validation_errors(error: ValidationError) -> list[dict]:
    """Format Pydantic validation errors for HTTP 422 responses."""
    return [
        {
            "field": ".".join(str(loc) for loc in item["loc"]),
            "message": item["msg"],
            "type": item["type"],
        }
        for item in error.errors()
    ]
