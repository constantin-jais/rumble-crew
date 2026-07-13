#!/usr/bin/env python3
"""Dependency-free semantic validator for MissionRecord v1 fixtures."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "mission-record.v1.schema.json"
FIXTURE_DIR = ROOT / "fixtures" / "mission-record"
FORMAT = "libre-ai.agent-board.mission-record.v1"
STATES = {
    "proposed",
    "awaiting_approval",
    "approved",
    "running",
    "blocked",
    "result_submitted",
    "accepted",
    "refused",
    "abandoned",
}
TRANSITIONS = {
    None: {"proposed"},
    "proposed": {"awaiting_approval", "approved", "abandoned"},
    "awaiting_approval": {"approved", "refused", "abandoned"},
    "approved": {"running", "abandoned"},
    "running": {"blocked", "result_submitted", "abandoned"},
    "blocked": {"running", "refused", "abandoned"},
    "result_submitted": {"accepted", "refused", "running"},
    "accepted": set(),
    "refused": set(),
    "abandoned": set(),
}
FORBIDDEN_KEYS = {
    "agent_profile",
    "agent_rank",
    "agent_score",
    "email",
    "secret",
    "token",
    "private_key",
    "raw_prompt",
}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{path}: invalid JSON: {error}") from error


def schema_type_matches(value: Any, expected: str) -> bool:
    checks = {
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "boolean": lambda item: isinstance(item, bool),
        "null": lambda item: item is None,
    }
    return expected in checks and checks[expected](value)


def validate_schema(value: Any, node: dict[str, Any], root: dict[str, Any], path: str = "$") -> list[str]:
    """Validate the JSON Schema keywords used by MissionRecord v1."""
    if "$ref" in node:
        reference = node["$ref"]
        if not isinstance(reference, str) or not reference.startswith("#/$defs/"):
            return [f"{path}: unsupported schema reference"]
        target = root.get("$defs", {}).get(reference.removeprefix("#/$defs/"))
        if not isinstance(target, dict):
            return [f"{path}: unresolved schema reference {reference}"]
        return validate_schema(value, target, root, path)

    if "oneOf" in node:
        matches = [
            validate_schema(value, candidate, root, path)
            for candidate in node["oneOf"]
        ]
        if sum(not errors for errors in matches) != 1:
            return [f"{path}: expected exactly one schema alternative"]
        return []

    errors: list[str] = []
    expected = node.get("type")
    expected_types = expected if isinstance(expected, list) else [expected] if expected else []
    if expected_types and not any(schema_type_matches(value, item) for item in expected_types):
        return [f"{path}: expected type {' or '.join(expected_types)}"]
    if "const" in node and value != node["const"]:
        errors.append(f"{path}: value does not match const")
    if "enum" in node and value not in node["enum"]:
        errors.append(f"{path}: value is outside the closed vocabulary")

    if isinstance(value, str):
        if len(value) < node.get("minLength", 0):
            errors.append(f"{path}: string is too short")
        if "maxLength" in node and len(value) > node["maxLength"]:
            errors.append(f"{path}: string is too long")
        if "pattern" in node and re.fullmatch(node["pattern"], value) is None:
            errors.append(f"{path}: string does not match the required pattern")
        if node.get("format") == "date-time":
            errors.extend(check_timestamp(value, path))

    if isinstance(value, list):
        if len(value) < node.get("minItems", 0):
            errors.append(f"{path}: array has too few items")
        item_schema = node.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(validate_schema(item, item_schema, root, f"{path}[{index}]"))

    if isinstance(value, dict):
        properties = node.get("properties", {})
        required = node.get("required", [])
        errors.extend(f"{path}.{key}: required field missing" for key in required if key not in value)
        if node.get("additionalProperties") is False:
            errors.extend(f"{path}.{key}: unexpected field" for key in value if key not in properties)
        for key, child in value.items():
            child_schema = properties.get(key)
            if isinstance(child_schema, dict):
                errors.extend(validate_schema(child, child_schema, root, f"{path}.{key}"))

    return errors


def walk_keys(value: Any, prefix: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS:
                errors.append(f"{prefix}.{key}: forbidden field")
            errors.extend(walk_keys(child, f"{prefix}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(walk_keys(child, f"{prefix}[{index}]"))
    return errors


def check_actor(actor: Any, path: str) -> list[str]:
    if not isinstance(actor, dict):
        return [f"{path}: actor must be an object"]
    errors = []
    actor_id = actor.get("actor_id")
    kind = actor.get("kind")
    if kind not in {"human", "service"}:
        errors.append(f"{path}.kind: expected human or service")
    if not isinstance(actor_id, str) or not actor_id.startswith(f"{kind}:"):
        errors.append(f"{path}.actor_id: prefix must match actor kind")
    if set(actor) - {"actor_id", "kind"}:
        errors.append(f"{path}: unexpected actor fields")
    return errors


def check_timestamp(value: Any, path: str) -> list[str]:
    if not isinstance(value, str):
        return [f"{path}: timestamp must be a string"]
    if re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",
        value,
    ) is None:
        return [f"{path}: invalid RFC3339 timestamp"]
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return [f"{path}: invalid RFC3339 timestamp"]
    if parsed.tzinfo is None:
        return [f"{path}: timestamp must include an offset"]
    return []


def require_nonempty_text(record: dict[str, Any], key: str, path: str) -> list[str]:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        return [f"{path}.{key}: non-empty text required"]
    return []


def duplicate_errors(items: Any, key: str, path: str) -> list[str]:
    if not isinstance(items, list):
        return [f"{path}: expected an array"]
    values = [item.get(key) for item in items if isinstance(item, dict)]
    return [f"{path}: duplicate {key}"] if len(values) != len(set(values)) else []


def validate(record: Any, schema: dict[str, Any]) -> list[str]:
    if not isinstance(record, dict):
        return ["$: MissionRecord must be an object"]

    errors = walk_keys(record)
    allowed = set(schema["properties"])
    required = set(schema["required"])
    missing = sorted(required - set(record))
    extra = sorted(set(record) - allowed)
    errors.extend(f"$.{key}: required field missing" for key in missing)
    errors.extend(f"$.{key}: unexpected field" for key in extra)

    if record.get("format") != FORMAT:
        errors.append("$.format: unsupported MissionRecord format")
    mission_id = record.get("mission_id")
    if not isinstance(mission_id, str) or not re.fullmatch(r"mission-[a-z0-9][a-z0-9-]{2,63}", mission_id):
        errors.append("$.mission_id: invalid mission identifier")
    if not isinstance(record.get("revision"), int) or record.get("revision", 0) < 1:
        errors.append("$.revision: positive integer required")
    state = record.get("state")
    if state not in STATES:
        errors.append("$.state: unknown state")
    errors.extend(require_nonempty_text(record, "intent", "$"))
    errors.extend(check_actor(record.get("requested_by"), "$.requested_by"))

    scope = record.get("scope")
    if not isinstance(scope, dict) or not isinstance(scope.get("in_scope"), list) or not scope.get("in_scope"):
        errors.append("$.scope.in_scope: at least one bounded item required")

    risk = record.get("risk")
    risk_level = risk.get("level") if isinstance(risk, dict) else None
    if risk_level not in {"low", "medium", "high", "critical"}:
        errors.append("$.risk.level: invalid risk level")
    if not isinstance(risk, dict) or not isinstance(risk.get("reasons"), list) or not risk.get("reasons"):
        errors.append("$.risk.reasons: at least one reason required")

    conditions = record.get("acceptance_conditions")
    if not isinstance(conditions, list) or not conditions:
        errors.append("$.acceptance_conditions: at least one condition required")
    errors.extend(duplicate_errors(conditions, "condition_id", "$.acceptance_conditions"))

    approvals = record.get("approvals")
    errors.extend(duplicate_errors(approvals, "approval_id", "$.approvals"))
    if isinstance(approvals, list):
        for index, approval in enumerate(approvals):
            path = f"$.approvals[{index}]"
            if not isinstance(approval, dict):
                errors.append(f"{path}: approval must be an object")
                continue
            actor = approval.get("actor")
            errors.extend(check_actor(actor, f"{path}.actor"))
            if not isinstance(actor, dict) or actor.get("kind") != "human":
                errors.append(f"{path}.actor: approvals require a human")
            errors.extend(check_timestamp(approval.get("at"), f"{path}.at"))
            errors.extend(require_nonempty_text(approval, "reason", path))

    events = record.get("events")
    errors.extend(duplicate_errors(events, "event_id", "$.events"))
    if not isinstance(events, list) or not events:
        errors.append("$.events: at least one event required")
    else:
        previous = None
        for index, event in enumerate(events):
            path = f"$.events[{index}]"
            if not isinstance(event, dict):
                errors.append(f"{path}: event must be an object")
                continue
            expected_sequence = index + 1
            if event.get("sequence") != expected_sequence:
                errors.append(f"{path}.sequence: expected {expected_sequence}")
            if event.get("from") != previous:
                errors.append(f"{path}.from: must equal previous state {previous!r}")
            target = event.get("to")
            if target not in TRANSITIONS.get(previous, set()):
                errors.append(f"{path}: transition {previous!r} -> {target!r} is not allowed")
            errors.extend(check_actor(event.get("actor"), f"{path}.actor"))
            errors.extend(check_timestamp(event.get("at"), f"{path}.at"))
            errors.extend(require_nonempty_text(event, "reason", path))
            previous = target
        if previous != state:
            errors.append("$.state: must equal the final event target")

    blockers = record.get("blockers")
    errors.extend(duplicate_errors(blockers, "blocker_id", "$.blockers"))
    if state == "blocked" and isinstance(blockers, list):
        if not any(item.get("status") == "open" for item in blockers if isinstance(item, dict)):
            errors.append("$.blockers: blocked mission requires an open blocker")

    activities = record.get("reported_activity")
    errors.extend(duplicate_errors(activities, "activity_id", "$.reported_activity"))
    if isinstance(activities, list):
        for index, activity in enumerate(activities):
            if isinstance(activity, dict):
                errors.extend(check_actor(activity.get("reported_by"), f"$.reported_activity[{index}].reported_by"))

    requested_by = record.get("requested_by")
    requester = requested_by.get("actor_id") if isinstance(requested_by, dict) else None
    if risk_level in {"high", "critical"} and state in {"approved", "running", "blocked", "result_submitted", "accepted"}:
        distinct_human_approvals = [
            approval
            for approval in approvals or []
            if isinstance(approval, dict)
            and approval.get("decision") == "approved"
            and isinstance(approval.get("actor"), dict)
            and approval["actor"].get("kind") == "human"
            and approval["actor"].get("actor_id") != requester
        ]
        if not distinct_human_approvals:
            errors.append("$.approvals: high/critical mission requires approval by a distinct human")

    result = record.get("result")
    verdict = record.get("human_verdict")
    final_origin = events[-1].get("from") if isinstance(events, list) and events and isinstance(events[-1], dict) else None
    if state in {"result_submitted", "accepted"} and not isinstance(result, dict):
        errors.append("$.result: result required for submitted or accepted states")
    if state == "refused" and final_origin == "result_submitted" and not isinstance(result, dict):
        errors.append("$.result: refused submitted result requires the submitted result")
    if state in {"accepted", "refused"}:
        if not isinstance(verdict, dict):
            errors.append("$.human_verdict: terminal verdict requires a human verdict")
        else:
            actor = verdict.get("actor")
            errors.extend(check_actor(actor, "$.human_verdict.actor"))
            if not isinstance(actor, dict) or actor.get("kind") != "human":
                errors.append("$.human_verdict.actor: verdict requires a human")
            if verdict.get("decision") != state:
                errors.append("$.human_verdict.decision: must match terminal state")
            errors.extend(check_timestamp(verdict.get("at"), "$.human_verdict.at"))
            errors.extend(require_nonempty_text(verdict, "reason", "$.human_verdict"))

    return errors


def validate_path(path: Path, schema: dict[str, Any]) -> list[str]:
    try:
        record = load_json(path)
        schema_errors = validate_schema(record, schema, schema)
        return schema_errors or validate(record, schema)
    except ValueError as error:
        return [str(error)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()

    schema = load_json(SCHEMA_PATH)
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        print("schema must use JSON Schema 2020-12", file=sys.stderr)
        return 1
    if schema.get("properties", {}).get("format", {}).get("const") != FORMAT:
        print("schema format does not match validator format", file=sys.stderr)
        return 1

    paths = args.paths or sorted(FIXTURE_DIR.glob("*.json"))
    failed = False
    for path in paths:
        errors = validate_path(path, schema)
        expected_valid = path.name.endswith(".valid.json") and not path.name.endswith(".invalid.json")
        if expected_valid and errors:
            failed = True
            print(f"FAIL valid fixture {path}")
            for error in errors:
                print(f"  - {error}")
        elif not expected_valid and not errors:
            failed = True
            print(f"FAIL invalid fixture accepted {path}")
        else:
            expectation = "valid" if expected_valid else "invalid"
            print(f"PASS {expectation}: {path.relative_to(ROOT)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
