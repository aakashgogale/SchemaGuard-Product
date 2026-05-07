"""Tests for the diff engine — 12 test cases covering all change types."""

from app.services.diff_engine import compare_schemas


def test_identical_schemas_returns_zero_changes():
    """Identical schemas should produce no changes."""
    schema = {"properties": {"id": {"type": "string"}}, "required": ["id"]}
    result = compare_schemas(schema, schema)
    assert result.total_changes == 0
    assert result.is_breaking is False
    assert result.changes == []


def test_deleted_field_is_breaking():
    """Removing a field from the schema is a breaking change."""
    old = {"properties": {"name": {"type": "string"}, "age": {"type": "integer"}}}
    new = {"properties": {"name": {"type": "string"}}}
    result = compare_schemas(old, new)
    assert result.is_breaking is True
    breaking = [c for c in result.changes if c.change_type == "BREAKING"]
    assert any("age" in c.path and "deleted" in c.reason for c in breaking)


def test_type_change_string_to_integer_is_breaking():
    """Changing a field type from string to integer is breaking."""
    old = {"properties": {"status": {"type": "string"}}}
    new = {"properties": {"status": {"type": "integer"}}}
    result = compare_schemas(old, new)
    assert result.is_breaking is True
    breaking = [c for c in result.changes if c.change_type == "BREAKING"]
    assert any("Type changed" in c.reason for c in breaking)


def test_type_change_integer_to_number_is_breaking():
    """Changing a field type from integer to number is breaking."""
    old = {"properties": {"amount": {"type": "integer"}}}
    new = {"properties": {"amount": {"type": "number"}}}
    result = compare_schemas(old, new)
    assert result.is_breaking is True
    breaking = [c for c in result.changes if c.change_type == "BREAKING"]
    assert len(breaking) == 1
    assert "integer" in breaking[0].reason and "number" in breaking[0].reason


def test_new_required_field_is_breaking():
    """Adding a new field that is immediately required is breaking."""
    old = {"properties": {"name": {"type": "string"}}, "required": ["name"]}
    new = {
        "properties": {"name": {"type": "string"}, "email": {"type": "string"}},
        "required": ["name", "email"],
    }
    result = compare_schemas(old, new)
    assert result.is_breaking is True
    breaking = [c for c in result.changes if c.change_type == "BREAKING"]
    assert any("email" in c.path and "required" in c.reason.lower() for c in breaking)


def test_optional_field_added_is_safe():
    """Adding a new optional field is a safe change."""
    old = {"properties": {"name": {"type": "string"}}}
    new = {"properties": {"name": {"type": "string"}, "bio": {"type": "string"}}}
    result = compare_schemas(old, new)
    assert result.is_breaking is False
    safe = [c for c in result.changes if c.change_type == "SAFE"]
    assert any("bio" in c.path and "optional" in c.reason.lower() for c in safe)


def test_description_change_is_safe():
    """Changing a field's description is safe."""
    old = {"properties": {"name": {"type": "string", "description": "User name"}}}
    new = {"properties": {"name": {"type": "string", "description": "Full name of user"}}}
    result = compare_schemas(old, new)
    assert result.is_breaking is False
    safe = [c for c in result.changes if c.change_type == "SAFE"]
    assert any("description" in c.path for c in safe)


def test_required_to_optional_is_safe():
    """Making a required field optional is safe (loosening constraint)."""
    old = {
        "properties": {"name": {"type": "string"}, "email": {"type": "string"}},
        "required": ["name", "email"],
    }
    new = {
        "properties": {"name": {"type": "string"}, "email": {"type": "string"}},
        "required": ["name"],
    }
    result = compare_schemas(old, new)
    assert result.is_breaking is False
    safe = [c for c in result.changes if c.change_type == "SAFE"]
    assert any("email" in c.path and "optional" in c.reason.lower() for c in safe)


def test_nested_field_deletion_is_breaking():
    """Deleting a nested field is a breaking change."""
    old = {
        "properties": {
            "address": {
                "type": "object",
                "properties": {"city": {"type": "string"}, "zip": {"type": "string"}},
            }
        }
    }
    new = {
        "properties": {
            "address": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
            }
        }
    }
    result = compare_schemas(old, new)
    assert result.is_breaking is True
    breaking = [c for c in result.changes if c.change_type == "BREAKING"]
    assert any("zip" in c.path for c in breaking)


def test_multiple_changes_counts_correctly():
    """Multiple changes should have correct breaking and safe counts."""
    old = {
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
        "required": ["name"],
    }
    new = {
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "number"},
            "bio": {"type": "string"},
        },
        "required": ["name"],
    }
    result = compare_schemas(old, new)
    assert result.breaking_count >= 1  # age type changed
    assert result.safe_count >= 1  # bio added
    assert result.total_changes == result.breaking_count + result.safe_count


def test_empty_to_schema_all_safe():
    """Going from empty properties to a full schema should be all safe changes."""
    old = {"properties": {}}
    new = {
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
        }
    }
    result = compare_schemas(old, new)
    assert result.is_breaking is False
    assert result.safe_count >= 2
    assert all(c.change_type == "SAFE" for c in result.changes)


def test_possible_rename_flagged_as_breaking():
    """A deleted field + similar named added field should flag as possible rename."""
    old = {"properties": {"user_name": {"type": "string"}}}
    new = {"properties": {"username": {"type": "string"}}}
    result = compare_schemas(old, new)
    assert result.is_breaking is True
    breaking = [c for c in result.changes if c.change_type == "BREAKING"]
    assert any("rename" in c.reason.lower() for c in breaking)


def test_malformed_nested_schema_returns_empty_result():
    """Unexpected schema shapes should not raise exceptions."""
    old = {"properties": {"profile": {"type": "object", "properties": []}}}
    new = {"properties": {"profile": {"type": "object", "properties": {}}}}
    result = compare_schemas(old, new)
    assert result.total_changes == 0
    assert result.changes == []
