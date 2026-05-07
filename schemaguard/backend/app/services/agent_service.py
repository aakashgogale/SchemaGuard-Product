"""Service functions for SchemaGuard AI Agent context building."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.models.registry import APIRegistry
from app.models.user import User


def build_user_agent_context(user: User) -> tuple[str, dict[str, Any]]:
    """Build a structured context string and stats for the current user."""
    registries = APIRegistry.query.filter_by(owner_id=user.id).all()
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=7)
    total_versions = 0
    total_breaking = 0
    total_safe = 0
    recent_diffs: list[dict[str, Any]] = []
    api_lines: list[str] = []
    last_upload: datetime | None = None

    for registry in registries:
        versions = list(registry.versions)
        total_versions += len(versions)
        api_lines.append(
            f"- API: {registry.name} | description: {registry.description or 'None'} | "
            f"created_at: {registry.created_at.isoformat()} | version_count: {len(versions)}"
        )
        for version in versions:
            if last_upload is None or version.uploaded_at > last_upload:
                last_upload = version.uploaded_at
            diff = version.diff_result or {}
            breaking = int(diff.get("breaking_count") or 0)
            safe = int(diff.get("safe_count") or 0)
            total_breaking += breaking
            total_safe += safe
            api_lines.append(
                f"  - Version {version.version} | status: {version.status.value} | "
                f"uploaded_at: {version.uploaded_at.isoformat()} | "
                f"change_reason: {version.change_reason or 'None'} | "
                f"breaking: {breaking} | safe: {safe} | is_breaking: {bool(diff.get('is_breaking'))}"
            )
            if diff:
                recent_diffs.append(
                    {
                        "api": registry.name,
                        "version": version.version,
                        "uploaded_at": version.uploaded_at,
                        "change_reason": version.change_reason,
                        "diff": diff,
                    }
                )

    recent_diffs.sort(key=lambda item: item["uploaded_at"], reverse=True)
    recent_diffs = recent_diffs[:10]
    breaking_this_week = sum(
        int(item["diff"].get("breaking_count") or 0)
        for item in recent_diffs
        if _as_aware(item["uploaded_at"]) >= week_start
    )
    recent_lines = [_format_recent_diff(item) for item in recent_diffs]
    context = "\n".join(
        [
            f"User: {user.email}",
            f"Total APIs: {len(registries)}",
            f"Total versions: {total_versions}",
            f"Total breaking changes: {total_breaking}",
            f"Total safe changes: {total_safe}",
            "",
            "APIs and versions:",
            "\n".join(api_lines) if api_lines else "No APIs registered yet.",
            "",
            "Most recent 10 diff results:",
            "\n".join(recent_lines) if recent_lines else "No diff results yet.",
        ]
    )
    stats = {
        "total_apis": len(registries),
        "total_versions": total_versions,
        "total_breaking_changes": total_breaking,
        "total_safe_changes": total_safe,
        "breaking_changes_this_week": breaking_this_week,
        "last_upload_time": last_upload.isoformat() if last_upload else None,
    }
    return context, stats


def build_system_prompt(context: str) -> str:
    """Build the Claude system prompt with the user's real SchemaGuard data."""
    return f"""You are SchemaGuard's AI Agent — a specialized assistant for API schema management and release safety.
You have access to this user's complete SchemaGuard data:
{context}

Your job is to:
Answer questions about the user's specific APIs and schema changes
Give release safety recommendations based on actual diff data
Explain what breaking changes mean in practical terms
Suggest how to communicate changes to downstream teams
Help the user understand versioning best practices

Rules you must follow:
Always reference the user's actual API names and version numbers when relevant
Never give generic advice when you have real data to work with
If a user asks about deploying a specific version, check the diff_result for that version
If there are breaking changes, always recommend notifying subscribers before deploying
Keep responses concise — 3 to 5 sentences maximum unless the user asks for detail
Use simple language — avoid jargon unless the user uses it first
If the user has no APIs yet, guide them to register one and explain the benefit
Format responses with clear line breaks — no markdown headers, just plain conversational text
Never make up API names or version numbers that are not in the provided data
If asked something unrelated, politely redirect to API schemas, diffs, release safety, or SchemaGuard."""


def _format_recent_diff(item: dict[str, Any]) -> str:
    """Format one recent diff entry for prompt context."""
    diff = item["diff"]
    changes = diff.get("changes", [])[:8]
    change_text = "; ".join(
        f"{change.get('change_type')} {change.get('path')}: {change.get('reason')}"
        for change in changes
    )
    return (
        f"- {item['api']} {item['version']} uploaded_at {item['uploaded_at'].isoformat()} | "
        f"reason: {item['change_reason'] or 'None'} | breaking_count: {diff.get('breaking_count', 0)} | "
        f"safe_count: {diff.get('safe_count', 0)} | changes: {change_text or 'No changes'}"
    )


def _as_aware(value: datetime) -> datetime:
    """Ensure datetimes are timezone-aware for comparisons."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
