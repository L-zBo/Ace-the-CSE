import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path("scripts/extract_questions.py").resolve()
SPEC = importlib.util.spec_from_file_location("extract_questions", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class ExtractQuestionOptionTests(unittest.TestCase):
    def test_extract_options_handles_split_dual_column_labels(self):
        raw = """
国家主席习近平在二〇二四年新年贺词中指出，下列与之相关的说法不准确的是：

A.“良渚”遗址中出土了大量的玉器
.“殷墟甲骨”中包含了大量的卜辞
B
C.“蚕丛及鱼凫”与“二里头”遗址有关
.青铜神树是“三星堆的文化瑰宝”之一
D
"""
        options = MODULE.extract_options(raw)

        self.assertEqual([item["label"] for item in options], ["A", "B", "C", "D"])
        self.assertEqual(options[0]["content"], "“良渚”遗址中出土了大量的玉器")
        self.assertEqual(options[1]["content"], "“殷墟甲骨”中包含了大量的卜辞")
        self.assertEqual(options[2]["content"], "“蚕丛及鱼凫”与“二里头”遗址有关")
        self.assertEqual(options[3]["content"], "青铜神树是“三星堆的文化瑰宝”之一")

    def test_extract_options_handles_inline_and_following_segment(self):
        raw = """
下列不属于完善市场经济基础制度内容的是：

A.完善财政转移支付体系 B.完善市场信息披露制度 C.完善市场准入制度
.完善产权制度
D
"""
        options = MODULE.extract_options(raw)

        self.assertEqual([item["label"] for item in options], ["A", "B", "C", "D"])
        self.assertEqual(options[3]["content"], "完善产权制度")

    def test_dedupe_questions_prefers_non_noise_duplicate(self):
        questions = [
            {"number": 7, "content": "11 12 3 6 12 3", "options": [], "category": "panduan"},
            {"number": 7, "content": "关于高质量充分就业的表述正确的是", "options": [{"label": "A", "content": "①②"}], "category": "changshi"},
        ]
        deduped = MODULE.dedupe_questions(questions)

        self.assertEqual(len(deduped), 1)
        self.assertIn("高质量充分就业", deduped[0]["content"])

    def test_manual_option_override_applies_in_build(self):
        questions = [
            {
                "number": 66,
                "content": "张某8：00开车从A地出发……问AC距离是BC距离的多少倍？",
                "options": [{"label": "A", "content": "坏数据"}],
                "category": "shuliang",
            }
        ]
        answers = {66: {"answer": "C", "explanation": "略"}}
        built = MODULE.build_questions_json(questions, answers, "national", 2025, "dishi", "")
        item = built["shuliang"][0]

        self.assertEqual(len(item["options"]), 4)
        self.assertEqual(item["options"][0]["content"], "10/13")
        self.assertEqual(item["options"][2]["content"], "20/13")


if __name__ == "__main__":
    unittest.main()
