import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "mission_validator", ROOT / "scripts" / "validate_mission_contracts.py"
)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)
SCHEMA = json.loads((ROOT / "schemas" / "mission-record.v1.schema.json").read_text())


class MissionContractTests(unittest.TestCase):
    def fixture(self, name: str):
        return json.loads((ROOT / "fixtures" / "mission-record" / name).read_text())

    def test_valid_fixtures_are_accepted(self):
        for name in ("accepted.valid.json", "critical-approved.valid.json"):
            with self.subTest(name=name):
                self.assertEqual(validator.validate(self.fixture(name), SCHEMA), [])

    def test_agent_profile_is_refused(self):
        errors = validator.validate(self.fixture("agent-profile.invalid.json"), SCHEMA)
        self.assertTrue(any("agent_profile" in error for error in errors))

    def test_critical_self_approval_is_refused(self):
        errors = validator.validate(
            self.fixture("critical-without-review.invalid.json"), SCHEMA
        )
        self.assertTrue(any("distinct human" in error for error in errors))

    def test_activity_is_not_a_result(self):
        errors = validator.validate(
            self.fixture("accepted-without-result.invalid.json"), SCHEMA
        )
        self.assertTrue(any("result required" in error for error in errors))

    def test_event_chain_cannot_skip_approval_to_acceptance(self):
        record = self.fixture("accepted.valid.json")
        record["events"][3]["to"] = "accepted"
        errors = validator.validate(record, SCHEMA)
        self.assertTrue(any("not allowed" in error for error in errors))

    def test_json_schema_is_applied_to_nested_records(self):
        record = self.fixture("critical-approved.valid.json")
        record["approvals"][0]["unexpected"] = True
        errors = validator.validate_schema(record, SCHEMA, SCHEMA)
        self.assertTrue(any("unexpected field" in error for error in errors))

    def test_malformed_actor_fails_closed_without_crashing(self):
        record = self.fixture("critical-approved.valid.json")
        record["approvals"][0]["actor"] = "human:reviewer"
        schema_errors = validator.validate_schema(record, SCHEMA, SCHEMA)
        semantic_errors = validator.validate(record, SCHEMA)
        self.assertTrue(any("expected type object" in error for error in schema_errors))
        self.assertTrue(any("approvals require a human" in error for error in semantic_errors))

    def test_timestamp_requires_rfc3339_t_separator(self):
        errors = validator.check_timestamp("2026-07-13 00:00:00+00:00", "$.at")
        self.assertTrue(any("RFC3339" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
