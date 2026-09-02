import tempfile
import unittest
import zipfile
from pathlib import Path

from opendps_config.engine import ConfigurationModel, evaluate_expression, parse_rpos, write_bundle


ROOT = Path(__file__).resolve().parents[1]
XML = ROOT / "tests" / "fixtures" / "synthetic_config.xml"


class ExpressionTests(unittest.TestCase):
    def test_boolean_expressions(self):
        present = {"EF7", "IO6"}
        self.assertTrue(evaluate_expression("(EF7)", present))
        self.assertTrue(evaluate_expression("EF7 & IO6", present))
        self.assertTrue(evaluate_expression("EF7 | KSG", present))
        self.assertTrue(evaluate_expression("!KSG", present))
        self.assertFalse(evaluate_expression("KSG", present))
        self.assertFalse(evaluate_expression("!EF7 & IO6", present))

    def test_rpo_parser(self):
        self.assertEqual(parse_rpos("# car\nEF7, io6 UE1"), {"EF7", "IO6", "UE1"})


class ElrIpcTests(unittest.TestCase):
    def test_summary(self):
        summary = ConfigurationModel.load(XML).summary()
        self.assertEqual(summary["ecu_name"], "SYNTHETIC_TEST_MODULE")
        self.assertEqual(summary["diagnostic_address"], "60")
        self.assertEqual(summary["parameter_count"], 2)
        self.assertEqual(summary["rpo_count"], 3)

    def test_plan(self):
        plan = ConfigurationModel.load(XML).generate_plan({"OPT", "USA"})
        self.assertEqual(len(plan["payloads"]), 1)
        self.assertGreater(plan["matched_rule_count"], 0)
        self.assertFalse(plan["readback_coverage"]["complete"])

    def test_decode_and_compare(self):
        model = ConfigurationModel.load(XML)
        decoded = model.decode_did("00F0", "0101")
        fields = {x["parameter"]: x for x in decoded["fields"]}
        self.assertEqual(fields["P_TEST_OPTION"]["interpretation"], "On")
        self.assertEqual(fields["P_TEST_REGION"]["interpretation"], "USA")
        compared = model.compare({"OPT", "USA"}, {"00F0": "0000"})
        self.assertTrue(compared["readback_coverage"]["complete"])
        self.assertEqual(compared["change_only"][0]["calculated_payload_hex"], "0101")

    def test_current_payload_is_preserved_outside_calculated_fields(self):
        plan = ConfigurationModel.load(XML).generate_plan({"OPT"}, {"00F0": "80FC"})
        self.assertEqual(plan["payloads"][0]["calculated_payload_hex"], "81FC")

    def test_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "bundle.zip"
            write_bundle(XML, {"OPT"}, output)
            with zipfile.ZipFile(output) as z:
                self.assertEqual(set(z.namelist()), {
                    "synthetic_config.xml", "build-record.txt", "configuration-plan.json", "manifest.json"
                })


if __name__ == "__main__":
    unittest.main()
