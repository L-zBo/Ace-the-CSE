import json
import subprocess
import sys
import unittest
from pathlib import Path


class Audit2025ZeroIssueTests(unittest.TestCase):
    def test_national_2025_has_zero_issues(self):
        report_path = Path("tmp/national_2025_zero_test.json")
        if report_path.exists():
            report_path.unlink()

        result = subprocess.run(
            [
                sys.executable,
                "scripts/audit_xingce.py",
                "--source",
                "national",
                "--year",
                "2025",
                "--report-json",
                str(report_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["summary"]["issueCount"], 0, report)


if __name__ == "__main__":
    unittest.main()
