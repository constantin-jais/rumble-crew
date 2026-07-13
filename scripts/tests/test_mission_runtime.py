import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import mission_runtime as runtime  # noqa: E402


class MissionRuntimeTests(unittest.TestCase):
    def fixture(self, name: str):
        return json.loads((ROOT / "fixtures" / "mission-record" / name).read_text())

    def test_full_approved_blocked_resumed_and_accepted_lifecycle(self):
        source = self.fixture("critical-approved.valid.json")
        original = copy.deepcopy(source)
        service = {"actor_id": "service:agent-factory", "kind": "service"}
        reviewer = {"actor_id": "human:security-reviewer", "kind": "human"}

        running = runtime.transition(
            source,
            expected_revision=2,
            target="running",
            actor=service,
            at="2026-07-13T09:06:00Z",
            reason="Agent Factory starts the approved planning-only mission.",
        )
        active = runtime.report_activity(
            running,
            expected_revision=3,
            actor=service,
            at="2026-07-13T09:07:00Z",
            summary="Checked the declared rotation-plan inputs.",
        )
        blocked = runtime.transition(
            active,
            expected_revision=4,
            target="blocked",
            actor=service,
            at="2026-07-13T09:08:00Z",
            reason="A required public policy reference is unavailable.",
            blocker_description="The public key-rotation policy cannot be read locally.",
        )
        resumed = runtime.transition(
            blocked,
            expected_revision=5,
            target="running",
            actor=reviewer,
            at="2026-07-13T09:10:00Z",
            reason="The policy was restored from the approved local mirror.",
        )
        submitted = runtime.transition(
            resumed,
            expected_revision=6,
            target="result_submitted",
            actor=service,
            at="2026-07-13T09:12:00Z",
            reason="The bounded plan and rollback checklist are attached.",
            result_summary="Planning-only rotation and rollback documents produced.",
            evidence_refs=["sha256:plan-local-evidence"],
        )
        accepted = runtime.transition(
            submitted,
            expected_revision=7,
            target="accepted",
            actor=reviewer,
            at="2026-07-13T09:15:00Z",
            reason="The evidence satisfies the planning-only acceptance condition.",
        )

        self.assertEqual(source, original, "runtime must not mutate its source record")
        self.assertEqual(accepted["state"], "accepted")
        self.assertEqual(accepted["revision"], 8)
        self.assertIsNotNone(accepted["result"])
        self.assertEqual(accepted["human_verdict"]["decision"], "accepted")
        self.assertTrue(all(item["status"] == "resolved" for item in accepted["blockers"]))
        runtime.validate_record(accepted)

    def test_stale_revision_is_rejected_without_mutation(self):
        source = self.fixture("critical-approved.valid.json")
        original = copy.deepcopy(source)
        with self.assertRaisesRegex(runtime.MissionRuntimeError, "stale revision"):
            runtime.transition(
                source,
                expected_revision=1,
                target="running",
                actor={"actor_id": "service:agent-factory", "kind": "service"},
                at="2026-07-13T09:06:00Z",
                reason="Attempt with stale state must fail closed.",
            )
        self.assertEqual(source, original)

    def test_critical_requester_cannot_self_approve(self):
        awaiting = self.fixture("critical-approved.valid.json")
        awaiting["state"] = "awaiting_approval"
        awaiting["revision"] = 1
        awaiting["approvals"] = []
        awaiting["events"] = awaiting["events"][:2]
        runtime.validate_record(awaiting)
        with self.assertRaisesRegex(runtime.MissionRuntimeError, "distinct human"):
            runtime.transition(
                awaiting,
                expected_revision=1,
                target="approved",
                actor=awaiting["requested_by"],
                at="2026-07-13T09:04:00Z",
                reason="Requester attempts to approve their own critical mission.",
            )

    def test_human_can_refuse_before_result_without_inventing_one(self):
        awaiting = self.fixture("critical-approved.valid.json")
        awaiting["state"] = "awaiting_approval"
        awaiting["revision"] = 1
        awaiting["approvals"] = []
        awaiting["events"] = awaiting["events"][:2]
        refused = runtime.transition(
            awaiting,
            expected_revision=1,
            target="refused",
            actor={"actor_id": "human:security-reviewer", "kind": "human"},
            at="2026-07-13T09:04:00Z",
            reason="The scope does not yet provide a safe rollback boundary.",
        )
        self.assertEqual(refused["state"], "refused")
        self.assertIsNone(refused["result"])
        self.assertEqual(refused["approvals"][-1]["decision"], "refused")
        runtime.validate_record(refused)

    def test_reported_activity_never_becomes_a_result(self):
        running = self.fixture("critical-approved.valid.json")
        running = runtime.transition(
            running,
            expected_revision=2,
            target="running",
            actor={"actor_id": "service:agent-factory", "kind": "service"},
            at="2026-07-13T09:06:00Z",
            reason="Start the already approved planning-only mission.",
        )
        active = runtime.report_activity(
            running,
            expected_revision=3,
            actor={"actor_id": "service:agent-factory", "kind": "service"},
            at="2026-07-13T09:07:00Z",
            summary="Read the public planning inputs.",
        )
        self.assertEqual(len(active["reported_activity"]), 1)
        self.assertIsNone(active["result"])
        self.assertIsNone(active["human_verdict"])

    def test_service_cannot_issue_a_terminal_verdict(self):
        accepted = self.fixture("accepted.valid.json")
        submitted = copy.deepcopy(accepted)
        submitted["state"] = "result_submitted"
        submitted["revision"] = 2
        submitted["human_verdict"] = None
        submitted["events"] = submitted["events"][:-1]
        runtime.validate_record(submitted)
        with self.assertRaisesRegex(runtime.MissionRuntimeError, "requires a human"):
            runtime.transition(
                submitted,
                expected_revision=2,
                target="accepted",
                actor={"actor_id": "service:agent-factory", "kind": "service"},
                at="2026-07-13T08:10:00Z",
                reason="A service cannot accept its own submitted result.",
            )


if __name__ == "__main__":
    unittest.main()
