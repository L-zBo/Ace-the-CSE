import json
import unittest
from pathlib import Path


class XingceSpecTests(unittest.TestCase):
    def test_national_2025_and_2024_specs_exist(self):
        path = Path("scripts/config/xingce_exam_specs.json")
        self.assertTrue(path.exists(), "缺少规则文件：scripts/config/xingce_exam_specs.json")

        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["national"]["2025"]["fushengjia"]["total"], 135)
        self.assertEqual(data["national"]["2025"]["fushengjia"]["modules"]["changshi"], 35)
        self.assertEqual(data["national"]["2025"]["fushengjia"]["modules"]["yanyu"], 30)
        self.assertEqual(data["national"]["2025"]["dishi"]["modules"]["shuliang"], 10)
        self.assertEqual(data["national"]["2025"]["dishi"]["modules"]["panduan"], 35)
        self.assertEqual(data["national"]["2025"]["xingzhengzhifa"]["modules"]["ziliao"], 20)
        self.assertEqual(data["national"]["2025"]["xingzhengzhifa"]["modules"]["changshi"], 35)
        self.assertEqual(data["national"]["2024"]["xingzhengzhifa"]["modules"]["shuliang"], 10)

    def test_national_2016_and_2023_specs_exist(self):
        data = json.loads(
            Path("scripts/config/xingce_exam_specs.json").read_text(encoding="utf-8")
        )
        self.assertEqual(data["national"]["2016"]["dishi"]["total"], 130)
        self.assertEqual(data["national"]["2023"]["fushengjia"]["total"], 135)
        self.assertEqual(data["national"]["2023"]["xingzhengzhifa"]["modules"]["ziliao"], 20)

    def test_option_exceptions_file_exists(self):
        path = Path("scripts/config/xingce_option_exceptions.json")
        self.assertTrue(
            path.exists(),
            "缺少例外文件：scripts/config/xingce_option_exceptions.json",
        )


if __name__ == "__main__":
    unittest.main()
