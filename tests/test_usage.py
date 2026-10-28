import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("usage", ROOT / "scripts/summarize_usage.py")
USAGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(USAGE)


class UsageTests(unittest.TestCase):
    def setUp(self):
        self.example = json.loads((ROOT / "examples/usage-summary.json").read_text(encoding="utf-8"))

    def test_example_excludes_child_counts(self):
        value = USAGE.summarize(self.example)
        self.assertEqual(value["arms"]["A"]["recorded_field_sum"], 200)
        self.assertEqual(value["arms"]["B"]["recorded_field_sum"], 100)
        self.assertEqual(value["exact_reduction_percent"], 50)
        self.assertTrue(value["synthetic"])

    def test_missing_is_unknown_not_zero(self):
        self.example["arms"]["B"]["root_calls"].append(None)
        value = USAGE.summarize(self.example)
        self.assertEqual(value["arms"]["B"]["missing_calls"], 1)
        self.assertIsNone(value["exact_reduction_percent"])

    def test_incomplete_or_failed_quality_cannot_pass(self):
        for field in ("complete", "quality_passed"):
            example = copy.deepcopy(self.example)
            if field == "complete":
                example["arms"]["B"][field] = False
            else:
                example[field] = False
            self.assertIsNone(USAGE.summarize(example)["exact_reduction_percent"])

    def test_empty_or_zero_baseline_cannot_claim_saving(self):
        self.example["arms"]["A"]["root_calls"] = []
        self.assertIsNone(USAGE.summarize(self.example)["exact_reduction_percent"])

    def test_rejects_extra_metadata(self):
        self.example["arms"]["A"]["endpoint"] = "not-allowed"
        with self.assertRaises(ValueError):
            USAGE.summarize(self.example)

    def test_rejects_negative_nonfinite_and_boolean_counts(self):
        for invalid in (-1, float("inf"), float("nan"), True, 1.5):
            example = copy.deepcopy(self.example)
            example["arms"]["A"]["root_calls"][0]["input"] = invalid
            with self.assertRaises(ValueError):
                USAGE.summarize(example)


if __name__ == "__main__":
    unittest.main()
