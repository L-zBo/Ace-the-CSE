import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path("scripts/compare_pdf_engines.py").resolve()
SPEC = importlib.util.spec_from_file_location("compare_pdf_engines", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class ComparePdfEnginesTests(unittest.TestCase):
    def test_summarize_extracted_text_counts_questions_and_options(self):
        sample_text = """
一. 常识判断：
1.
题干一
A. 选项A
B. 选项B
C. 选项C
D. 选项D
2.
题干二
A. 选项A
B. 选项B
C. 选项C
"""
        summary = MODULE.summarize_extracted_text(sample_text, expected_total=2)

        self.assertEqual(summary["candidateQuestionCount"], 2)
        self.assertEqual(summary["candidateMaxQuestionNumber"], 2)
        self.assertEqual(summary["parsedQuestionCount"], 2)
        self.assertEqual(summary["parsedFullOptionCount"], 1)
        self.assertEqual(summary["parsedOptionHistogram"]["4"], 1)
        self.assertEqual(summary["parsedOptionHistogram"]["3"], 1)
        self.assertEqual(summary["candidateMissingNumbers"], [])

    def test_build_missing_numbers_handles_expected_total(self):
        missing = MODULE.build_missing_numbers([1, 2, 4], expected_total=5)
        self.assertEqual(missing, [3, 5])


if __name__ == "__main__":
    unittest.main()
