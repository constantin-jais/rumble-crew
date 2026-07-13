#!/usr/bin/env python3
"""Fail-closed, side-effect-free MissionRecord v1 transition engine.

This module mutates no remote system and executes no agent. It returns a new
validated record only after optimistic-revision and lifecycle checks pass.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import validate_mission_contracts as contracts

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads(
    (ROOT / "schemas" / "mission-record.v1.schema.json").read_text(encoding="utf-8")
)


class MissionRuntimeError(ValueError):
    """A command was rejected without changing the source MissionRecord."""


def validate_record(record: dict[str, Any]) -> None:
    errors = contracts.validate_schema(record, SCHEMA, SCHEMA) or contracts.validate(record, SCHEMA)
    if errors:
        raise MissionRuntimeError("invalid MissionRecord: " + "; ".join(errors))


def validate_actor(actor: Any, *, human_required: bool = False) -> None:
    errors = contracts.check_actor(actor, "$.command.actor")
    if human_required and (not isinstance(actor, dict) or actor.get("kind") != "human"):
        errors.append("$.command.actor: this decision requires a human")
    if errors:
        raise MissionRuntimeError("; ".join(errors))


def transition(
    record: dict[str, Any],
    *,
    expected_revision: int,
    target: str,
    actor: dict[str, Any],
    at: str,
    reason: str,
    blocker_description: str | None = None,
    result_summary: str | None = None,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Apply one lifecycle transition and return a separately validated copy."""
    validate_record(record)
    validate_actor(actor)
    if record["revision"] != expected_revision:
        raise MissionRuntimeError(
            f"stale revision: expected {expected_revision}, current {record['revision']}"
        )
    if not isinstance(reason, str) or len(reason.strip()) < 5:
        raise MissionRuntimeError("transition reason must contain at least five characters")
    timestamp_errors = contracts.check_timestamp(at, "$.command.at")
    if timestamp_errors:
        raise MissionRuntimeError("; ".join(timestamp_errors))

    current = record["state"]
    if target not in contracts.TRANSITIONS.get(current, set()):
        raise MissionRuntimeError(f"transition {current!r} -> {target!r} is not allowed")

    updated = copy.deepcopy(record)
    sequence = len(updated["events"]) + 1

    if target == "approved":
        validate_actor(actor, human_required=True)
        if updated["risk"]["level"] in {"high", "critical"} and actor["actor_id"] == updated["requested_by"]["actor_id"]:
            raise MissionRuntimeError("high/critical mission requires approval by a distinct human")
        updated["approvals"].append(
            {
                "approval_id": f"approval-{sequence:04d}",
                "decision": "approved",
                "actor": copy.deepcopy(actor),
                "at": at,
                "reason": reason,
            }
        )

    if target == "blocked":
        if not blocker_description or len(blocker_description.strip()) < 5:
            raise MissionRuntimeError("blocked transition requires a blocker description")
        updated["blockers"].append(
            {
                "blocker_id": f"blocker-{sequence:04d}",
                "status": "open",
                "description": blocker_description,
                "raised_by": copy.deepcopy(actor),
                "raised_at": at,
                "resolution": None,
            }
        )

    if current == "blocked" and target == "running":
        open_blockers = [item for item in updated["blockers"] if item.get("status") == "open"]
        if not open_blockers:
            raise MissionRuntimeError("resume requires an open blocker")
        for blocker in open_blockers:
            blocker["status"] = "resolved"
            blocker["resolution"] = reason

    if target == "result_submitted":
        refs = evidence_refs or []
        if not result_summary or len(result_summary.strip()) < 5:
            raise MissionRuntimeError("result submission requires a summary")
        if not refs or any(not isinstance(ref, str) or len(ref.strip()) < 3 for ref in refs):
            raise MissionRuntimeError("result submission requires non-empty evidence references")
        updated["result"] = {
            "summary": result_summary,
            "evidence_refs": list(refs),
            "submitted_by": copy.deepcopy(actor),
            "submitted_at": at,
        }

    if target in {"accepted", "refused"}:
        validate_actor(actor, human_required=True)
        updated["human_verdict"] = {
            "decision": target,
            "actor": copy.deepcopy(actor),
            "at": at,
            "reason": reason,
        }
        if target == "refused" and current == "awaiting_approval":
            updated["approvals"].append(
                {
                    "approval_id": f"approval-{sequence:04d}",
                    "decision": "refused",
                    "actor": copy.deepcopy(actor),
                    "at": at,
                    "reason": reason,
                }
            )

    updated["events"].append(
        {
            "sequence": sequence,
            "event_id": f"event-{sequence:04d}-{target.replace('_', '-')}",
            "from": current,
            "to": target,
            "actor": copy.deepcopy(actor),
            "at": at,
            "reason": reason,
        }
    )
    updated["state"] = target
    updated["revision"] += 1
    validate_record(updated)
    return updated


def report_activity(
    record: dict[str, Any],
    *,
    expected_revision: int,
    actor: dict[str, Any],
    at: str,
    summary: str,
) -> dict[str, Any]:
    """Record declared activity without turning it into a result or verdict."""
    validate_record(record)
    validate_actor(actor)
    if record["revision"] != expected_revision:
        raise MissionRuntimeError(
            f"stale revision: expected {expected_revision}, current {record['revision']}"
        )
    if record["state"] not in {"running", "blocked"}:
        raise MissionRuntimeError("activity can be reported only while running or blocked")
    if not isinstance(summary, str) or len(summary.strip()) < 5:
        raise MissionRuntimeError("activity summary must contain at least five characters")
    timestamp_errors = contracts.check_timestamp(at, "$.command.at")
    if timestamp_errors:
        raise MissionRuntimeError("; ".join(timestamp_errors))

    updated = copy.deepcopy(record)
    sequence = len(updated["reported_activity"]) + 1
    updated["reported_activity"].append(
        {
            "activity_id": f"activity-{sequence:04d}",
            "reported_by": copy.deepcopy(actor),
            "at": at,
            "summary": summary,
        }
    )
    updated["revision"] += 1
    validate_record(updated)
    return updated
