"""
Diff Engine — Pure schema comparison module.

Zero Flask imports. Zero DB calls. Zero side effects.
Takes two dicts, returns a DiffResult dataclass.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from difflib import SequenceMatcher
from typing import Any


@dataclass
class Change:
    """Represents a single detected change between two schema versions."""

    path: str
    change_type: str  # "BREAKING" or "SAFE"
    reason: str
    old_value: Any
    new_value: Any

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary."""
        return asdict(self)


@dataclass
class DiffResult:
    """Aggregated result of comparing two schemas."""

    is_breaking: bool = False
    breaking_count: int = 0
    safe_count: int = 0
    total_changes: int = 0
    changes: list[Change] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary for storage."""
        return {
            "is_breaking": self.is_breaking,
            "breaking_count": self.breaking_count,
            "safe_count": self.safe_count,
            "total_changes": self.total_changes,
            "changes": [c.to_dict() for c in self.changes],
        }


def _is_similar_name(name_a: str, name_b: str, threshold: float = 0.6) -> bool:
    """Check if two field names are similar enough to suggest a rename."""
    return SequenceMatcher(None, name_a.lower(), name_b.lower()).ratio() >= threshold


def _compare_properties(
    old_props: dict,
    new_props: dict,
    old_required: list[str],
    new_required: list[str],
    base_path: str,
    changes: list[Change],
) -> None:
    """Recursively compare properties between two schema objects."""
    old_keys = set(old_props.keys())
    new_keys = set(new_props.keys())

    deleted_keys = old_keys - new_keys
    added_keys = new_keys - old_keys
    common_keys = old_keys & new_keys

    # Detect possible renames: a deleted field + an added field with similar name
    rename_pairs: set[tuple[str, str]] = set()
    for del_key in deleted_keys:
        for add_key in added_keys:
            if _is_similar_name(del_key, add_key):
                rename_pairs.add((del_key, add_key))

    flagged_deletes = {pair[0] for pair in rename_pairs}
    flagged_adds = {pair[1] for pair in rename_pairs}

    # Handle renames
    for del_key, add_key in rename_pairs:
        changes.append(Change(
            path=f"{base_path}.{del_key}",
            change_type="BREAKING",
            reason=f"Possible rename: '{del_key}' → '{add_key}'. Field deleted and similar field added.",
            old_value=old_props[del_key],
            new_value=new_props[add_key],
        ))

    # Handle deleted fields (not part of a rename)
    for key in sorted(deleted_keys - flagged_deletes):
        changes.append(Change(
            path=f"{base_path}.{key}",
            change_type="BREAKING",
            reason=f"Field '{key}' was deleted",
            old_value=old_props[key],
            new_value=None,
        ))

    # Handle added fields
    for key in sorted(added_keys - flagged_adds):
        is_now_required = key in new_required
        if is_now_required:
            changes.append(Change(
                path=f"{base_path}.{key}",
                change_type="BREAKING",
                reason=f"New required field '{key}' added",
                old_value=None,
                new_value=new_props[key],
            ))
        else:
            changes.append(Change(
                path=f"{base_path}.{key}",
                change_type="SAFE",
                reason=f"New optional field '{key}' added",
                old_value=None,
                new_value=new_props[key],
            ))

    # Handle common fields — check for type changes and nested differences
    for key in sorted(common_keys):
        old_val = old_props[key]
        new_val = new_props[key]
        field_path = f"{base_path}.{key}"

        if isinstance(old_val, dict) and isinstance(new_val, dict):
            _compare_field_objects(old_val, new_val, field_path, changes)
        elif old_val != new_val:
            changes.append(Change(
                path=field_path,
                change_type="SAFE",
                reason=f"Field '{key}' value changed",
                old_value=old_val,
                new_value=new_val,
            ))

    # Check required array changes
    _compare_required(old_required, new_required, old_keys, base_path, changes)


def _compare_field_objects(
    old_field: dict,
    new_field: dict,
    field_path: str,
    changes: list[Change],
) -> None:
    """Compare two field definition objects for type changes and nested properties."""
    old_type = old_field.get("type")
    new_type = new_field.get("type")

    # Type change detection
    if old_type and new_type and old_type != new_type:
        changes.append(Change(
            path=field_path,
            change_type="BREAKING",
            reason=f"Type changed from '{old_type}' to '{new_type}'",
            old_value=old_type,
            new_value=new_type,
        ))
        return

    # Description/title changes are safe
    for meta_key in ("description", "title"):
        old_meta = old_field.get(meta_key)
        new_meta = new_field.get(meta_key)
        if old_meta != new_meta and old_meta is not None:
            changes.append(Change(
                path=f"{field_path}.{meta_key}",
                change_type="SAFE",
                reason=f"'{meta_key}' changed",
                old_value=old_meta,
                new_value=new_meta,
            ))

    # Enum changes
    old_enum = old_field.get("enum")
    new_enum = new_field.get("enum")
    if old_enum is not None and new_enum is not None:
        old_set = set(old_enum)
        new_set = set(new_enum)
        removed = old_set - new_set
        added = new_set - old_set
        if removed:
            changes.append(Change(
                path=f"{field_path}.enum",
                change_type="BREAKING",
                reason=f"Enum values removed: {sorted(removed)}",
                old_value=old_enum,
                new_value=new_enum,
            ))
        if added:
            changes.append(Change(
                path=f"{field_path}.enum",
                change_type="SAFE",
                reason=f"New enum values added: {sorted(added)}",
                old_value=old_enum,
                new_value=new_enum,
            ))

    # Recurse into nested properties
    if "properties" in old_field or "properties" in new_field:
        nested_old = old_field.get("properties", {})
        nested_new = new_field.get("properties", {})
        nested_old_req = old_field.get("required", [])
        nested_new_req = new_field.get("required", [])
        _compare_properties(
            nested_old, nested_new, nested_old_req, nested_new_req,
            f"{field_path}.properties", changes,
        )


def _compare_required(
    old_required: list[str],
    new_required: list[str],
    existing_fields: set[str],
    base_path: str,
    changes: list[Change],
) -> None:
    """Detect required array changes."""
    old_set = set(old_required)
    new_set = set(new_required)

    # Fields that became required but already existed
    newly_required = (new_set - old_set) & existing_fields
    for field_name in sorted(newly_required):
        changes.append(Change(
            path=f"{base_path}.{field_name}",
            change_type="BREAKING",
            reason=f"Existing field '{field_name}' became required",
            old_value="optional",
            new_value="required",
        ))

    # Fields that became optional (was required, now not)
    became_optional = (old_set - new_set) & existing_fields
    for field_name in sorted(became_optional):
        changes.append(Change(
            path=f"{base_path}.{field_name}",
            change_type="SAFE",
            reason=f"Required field '{field_name}' became optional (loosening constraint)",
            old_value="required",
            new_value="optional",
        ))


def _compare_paths(
    old_paths: dict,
    new_paths: dict,
    changes: list[Change],
) -> None:
    """Compare OpenAPI-style paths between two schemas."""
    old_endpoints = set(old_paths.keys())
    new_endpoints = set(new_paths.keys())

    # Removed endpoints
    for endpoint in sorted(old_endpoints - new_endpoints):
        changes.append(Change(
            path=f"$.paths.{endpoint}",
            change_type="BREAKING",
            reason=f"Endpoint '{endpoint}' was removed",
            old_value=old_paths[endpoint],
            new_value=None,
        ))

    # New endpoints
    for endpoint in sorted(new_endpoints - old_endpoints):
        changes.append(Change(
            path=f"$.paths.{endpoint}",
            change_type="SAFE",
            reason=f"New endpoint '{endpoint}' added",
            old_value=None,
            new_value=new_paths[endpoint],
        ))

    # Changed endpoints — compare methods
    for endpoint in sorted(old_endpoints & new_endpoints):
        old_methods = old_paths[endpoint] if isinstance(old_paths[endpoint], dict) else {}
        new_methods = new_paths[endpoint] if isinstance(new_paths[endpoint], dict) else {}

        for method in sorted(set(old_methods.keys()) - set(new_methods.keys())):
            changes.append(Change(
                path=f"$.paths.{endpoint}.{method}",
                change_type="BREAKING",
                reason=f"Method '{method}' removed from endpoint '{endpoint}'",
                old_value=old_methods[method],
                new_value=None,
            ))

        for method in sorted(set(new_methods.keys()) - set(old_methods.keys())):
            changes.append(Change(
                path=f"$.paths.{endpoint}.{method}",
                change_type="SAFE",
                reason=f"New method '{method}' added to endpoint '{endpoint}'",
                old_value=None,
                new_value=new_methods[method],
            ))


def compare_schemas(old_schema: dict, new_schema: dict) -> DiffResult:
    """
    Compare two API schemas and produce a DiffResult.

    This is the main entry point. It handles both property-based
    schemas and OpenAPI-style path-based schemas. Returns an empty
    DiffResult for identical schemas or unexpected input.
    """
    try:
        return _compare_schemas_safely(old_schema, new_schema)
    except Exception:
        return DiffResult()


def _compare_schemas_safely(old_schema: dict, new_schema: dict) -> DiffResult:
    """Compare schemas after defensive type checks have passed."""
    if not isinstance(old_schema, dict) or not isinstance(new_schema, dict):
        return DiffResult()

    if old_schema == new_schema:
        return DiffResult()

    changes: list[Change] = []

    old_props = old_schema.get("properties", {})
    new_props = new_schema.get("properties", {})
    old_required = old_schema.get("required", [])
    new_required = new_schema.get("required", [])

    if (old_props or new_props) and isinstance(old_props, dict) and isinstance(new_props, dict):
        _compare_properties(
            old_props, new_props, old_required, new_required,
            "$.properties", changes,
        )

    old_paths = old_schema.get("paths", {})
    new_paths = new_schema.get("paths", {})

    if (old_paths or new_paths) and isinstance(old_paths, dict) and isinstance(new_paths, dict):
        _compare_paths(old_paths, new_paths, changes)

    breaking = [c for c in changes if c.change_type == "BREAKING"]
    safe = [c for c in changes if c.change_type == "SAFE"]

    return DiffResult(
        is_breaking=len(breaking) > 0,
        breaking_count=len(breaking),
        safe_count=len(safe),
        total_changes=len(changes),
        changes=changes,
    )
