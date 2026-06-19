import json
import subprocess
import sys
import unittest
from pathlib import Path


class AuditXingceTests(unittest.TestCase):
    def test_audit_generates_manifest(self):
        manifest = Path("src/data/meta/xingce_exam_manifest.json")
        if manifest.exists():
          manifest.unlink()

        result = subprocess.run(
            [
                sys.executable,
                "scripts/audit_xingce.py",
                "--source",
                "national",
                "--write-manifest"
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(manifest.exists(), "未生成Manifest文件")

        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertIn("generatedAt", data)
        self.assertIn("exams", data)
        self.assertIsInstance(data["exams"], list)
        self.assertGreater(len(data["exams"]), 0)


if __name__ == "__main__":
    unittest.main()
