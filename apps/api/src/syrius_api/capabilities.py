"""EngineeringCapability contract + approval gates (plan §7.2, §13).

The capability contract is the unit the departments execute: a versioned,
validated, permission-checked, resource-limited piece of work with
provenance and completion criteria. ``validate_input`` / ``validate_output``
use the declared JSON Schemas (via Pydantic-free structural checks kept
deliberately small — see ``validate_against_schema``).

Human approval boundaries (plan §13) are recorded here as data, not
buried in code paths: actions in ``REQUIRES_HUMAN_APPROVAL`` never
execute without an explicit approval record, and paid-compute paths do
not exist in v0.1 at all — ``PAID_COMPUTE_ACTIONS`` documents the
boundary so a future implementation cannot add one silently.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CapabilityExecutionContext(BaseModel):
    """Runtime context handed to a capability execution."""

    actor: str = "system"
    workspace_id: str | None = None
    project_id: str | None = None
    run_id: str | None = None
    permissions: list[str] = Field(default_factory=list)
    cancelled: bool = False


def validate_against_schema(payload: Any, schema: dict) -> list[str]:
    """Structural JSON-Schema check (subset: type, required, properties,
    enum, minimum/maximum, items). Returns a list of error strings."""
    errors: list[str] = []
    _check(payload, schema, "$", errors)
    return errors


def _check(value: Any, schema: dict, path: str, errors: list[str]) -> None:
    if not isinstance(schema, dict):
        return
    expected = schema.get("type")
    if expected == "object":
        if not isinstance(value, dict):
            errors.append(f"{path}: expected object")
            return
        for field in schema.get("required", []):
            if field not in value:
                errors.append(f"{path}.{field}: required field missing")
        for name, sub in (schema.get("properties") or {}).items():
            if name in value:
                _check(value[name], sub, f"{path}.{name}", errors)
    elif expected == "array":
        if not isinstance(value, list):
            errors.append(f"{path}: expected array")
        elif "items" in schema:
            for i, item in enumerate(value):
                _check(item, schema["items"], f"{path}[{i}]", errors)
    elif expected == "string":
        if not isinstance(value, str):
            errors.append(f"{path}: expected string")
    elif expected == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{path}: expected integer")
    elif expected == "number":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"{path}: expected number")
    elif expected == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{path}: expected boolean")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value {value!r} not in enum {schema['enum']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: {value} < minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: {value} > maximum {schema['maximum']}")


class EngineeringCapability(BaseModel):
    """Capability contract (plan §7.2)."""

    id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    permissions: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    resource_limits: dict[str, Any] = Field(default_factory=dict)
    validators: list[str] = Field(default_factory=list)
    completion_criteria: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    artifact_types: list[str] = Field(default_factory=list)

    def validate_input(self, payload: dict) -> list[str]:
        return validate_against_schema(payload, self.input_schema)

    def validate_output(self, payload: dict) -> list[str]:
        return validate_against_schema(payload, self.output_schema)

    def check_permissions(self, context: CapabilityExecutionContext) -> list[str]:
        """Missing permissions for *context* (empty = allowed)."""
        return [p for p in self.permissions if p not in context.permissions]

    def check_resource_limits(self, usage: dict[str, Any]) -> list[str]:
        """Resource-limit violations for *usage* (empty = within limits)."""
        violations = []
        for key, limit in self.resource_limits.items():
            if key in usage and isinstance(usage[key], (int, float)):
                if usage[key] > limit:
                    violations.append(
                        f"{key}: usage {usage[key]} exceeds limit {limit}"
                    )
        return violations


# ---------------------------------------------------------------------------
# Human approval boundaries (plan §13). Recorded as data; enforced by
# callers via requires_human_approval(). No code path in v0.1 executes
# a paid-compute action — the set exists so the boundary is explicit.
# ---------------------------------------------------------------------------

REQUIRES_HUMAN_APPROVAL: frozenset[str] = frozenset(
    {
        "deploy_policy_to_production",
        "share_artifact_externally",
        "spend_paid_compute",
        "publish_dataset",
        "delete_project_data",
    }
)

PAID_COMPUTE_ACTIONS: frozenset[str] = frozenset(
    {
        "spend_paid_compute",
        "provision_gpu_instance",
        "run_paid_training",
    }
)


def requires_human_approval(action: str) -> bool:
    return action in REQUIRES_HUMAN_APPROVAL


def is_paid_compute(action: str) -> bool:
    """True for actions that would spend money — not implemented in v0.1."""
    return action in PAID_COMPUTE_ACTIONS
