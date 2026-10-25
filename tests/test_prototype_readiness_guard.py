import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestPrototypeReadinessGuard(unittest.TestCase):
    def test_capability_register_has_no_authorized_claims(self):
        path = PROJECT_ROOT / "config" / "capability-register.yaml"
        content = path.read_text(encoding="utf-8-sig")

        self.assertIn("capabilities: []", content)

    def test_platform_rules_remain_proposed(self):
        path = PROJECT_ROOT / "config" / "platform-rules.yaml"
        content = path.read_text(encoding="utf-8-sig")

        self.assertIn('status: "proposed"', content)

    def test_similarity_threshold_remains_explicitly_unset(self):
        path = PROJECT_ROOT / "config" / "platform-rules.yaml"
        content = path.read_text(encoding="utf-8-sig")

        self.assertIn(
            "UNSET - select and test during implementation",
            content,
        )

    def test_sample_brief_has_no_product_capability_ids(self):
        path = PROJECT_ROOT / "inputs" / "sample-brief.json"
        brief = json.loads(path.read_text(encoding="utf-8-sig"))

        self.assertEqual(brief.get("capability_ids"), [])

    def test_sample_brief_identifies_itself_as_a_workflow_test(self):
        path = PROJECT_ROOT / "inputs" / "sample-brief.json"
        brief = json.loads(path.read_text(encoding="utf-8-sig"))

        self.assertIn(
            "sample message used to test the content workflow",
            brief.get("key_message", ""),
        )

    def test_candidate_checklist_preserves_unknowns_and_no_publishing(self):
        path = PROJECT_ROOT / "inputs" / "candidate-readiness-checklist.md"
        content = path.read_text(encoding="utf-8-sig")

        self.assertIn(
            "UNKNOWN - needs input from candidate",
            content,
        )
        self.assertIn(
            "No publishing or external contact is authorized",
            content,
        )

    def test_official_workbook_schema_still_has_23_columns(self):
        path = PROJECT_ROOT / "config" / "workbook-schema.json"
        schema = json.loads(path.read_text(encoding="utf-8-sig"))

        self.assertEqual(len(schema["columns"]), 23)


if __name__ == "__main__":
    unittest.main()
