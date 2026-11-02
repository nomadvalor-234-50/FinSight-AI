"""Regression tests for import-safe T07 and CSV categorization."""

import contextlib
import importlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

try:
    from .categorization import categorize_transaction
except ImportError:
    from categorization import categorize_transaction


class CategorizationTests(unittest.TestCase):
    def test_existing_category_mapping_is_preserved(self):
        cases = {
            "Zomato payment": "Food",
            "Amazon purchase": "Shopping",
            "Netflix subscription": "Subscription",
            "Uber ride": "Transportation",
            "BESCOM electricity bill": "Utilities",
            "House rent": "Housing",
            "Monthly Salary": "Income",
            "Unrecognized merchant": "Other",
        }
        for description, expected in cases.items():
            with self.subTest(description=description):
                self.assertEqual(categorize_transaction(description), expected)

    def test_importing_categorizer_is_silent(self):
        project_root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "-c", "import ai_engine.categorization"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(result.stdout, "")

    def test_csv_module_import_does_not_read_or_write_files(self):
        try:
            import_path = "ai_engine.csv_categorization"
        except ImportError:
            import_path = "csv_categorization"
        with patch("pandas.read_csv", side_effect=AssertionError("read_csv ran during import")), \
                patch.object(pd.DataFrame, "to_csv", side_effect=AssertionError("to_csv ran during import")), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            importlib.import_module(import_path)
        self.assertEqual(output.getvalue(), "")

    def test_csv_categorizer_uses_supplied_paths_and_saves_results(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.csv"
            destination = Path(directory) / "output.csv"
            pd.DataFrame({
                "date": ["2026-01-01"], "description": ["Zomato order"],
                "amount": [100], "type": ["debit"],
            }).to_csv(source, index=False)
            try:
                from .csv_categorization import categorize_csv
            except ImportError:
                from csv_categorization import categorize_csv
            result = categorize_csv(source, destination)
            self.assertEqual(result.loc[0, "category"], "Food")
            saved = pd.read_csv(destination)
            self.assertEqual(saved.loc[0, "category"], "Food")


if __name__ == "__main__":
    unittest.main()
