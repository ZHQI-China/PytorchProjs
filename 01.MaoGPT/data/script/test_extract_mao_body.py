import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("extract_mao_body.py")


def load_module():
    spec = importlib.util.spec_from_file_location("extract_mao_body", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ExtractMaoBodyTests(unittest.TestCase):
    def test_extracts_body_merges_lines_and_deduplicates_titles(self):
        module = load_module()
        source = "\n".join(
            [
                "毛泽东选集",
                "=====第1页=====",
                "目录",
                "第一卷",
                "中国社会各阶级的分析",
                "湖南农民运动考察报告",
                "=====第21页=====",
                "中国社会各阶级的分析*",
                "（一九二五年十二月一日）",
                "谁是我们的敌人？谁是我们的朋友？这个问题是革命的首要问",
                "题。",
                "一",
                "这是第一节的第一",
                "段。",
                "注释",
                "* 这里是注释，应该删除。",
                "（2）戴季陶",
                "（一八九一———一九四九）",
                "注释人名不应输出。",
                "=====第26页=====",
                "湖南农民运动考察报告*",
                "（一九二七年三月）",
                "农民问题的严重性",
                "我这回到湖南，实地考察了湘潭、湘乡、衡山、醴陵、长沙五",
                "县的情况。",
                "注释",
                "（1）这里是注释。",
                "=====第100页=====",
                "中国社会各阶级的分析*",
                "（一九二五年十二月一日）",
                "重复文章不应输出。",
                "",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.txt"
            output_path = Path(tmp) / "Mao.txt"
            input_path.write_text(source, encoding="utf-8")

            stats = module.extract_file(input_path, output_path, dedupe=True)
            result = output_path.read_text(encoding="utf-8")

        self.assertEqual(stats.article_count, 2)
        self.assertEqual(stats.duplicate_count, 1)
        self.assertIn("中国社会各阶级的分析", result)
        self.assertIn("（一九二五年十二月一日）", result)
        self.assertIn("谁是我们的敌人？谁是我们的朋友？这个问题是革命的首要问题。", result)
        self.assertIn("这是第一节的第一段。", result)
        self.assertIn("湖南农民运动考察报告", result)
        self.assertIn("我这回到湖南，实地考察了湘潭、湘乡、衡山、醴陵、长沙五县的情况。", result)
        self.assertNotIn("目录", result)
        self.assertNotIn("=====第", result)
        self.assertNotIn("注释", result)
        self.assertNotIn("戴季陶", result)
        self.assertNotIn("注释人名不应输出", result)
        self.assertNotIn("重复文章不应输出", result)

    def test_handles_ascii_dates_inline_titles_and_source_notes(self):
        module = load_module()
        source = "\n".join(
            [
                "前一篇文章",
                "(1964年4月16日）",
                "这是一段正文。",
                "根据中央文献出版社、世界知识出版社一九九四年出版的",
                "《毛泽东外交文选》刊印。",
                "毛泽东选集第一、二、三、四卷（一九九一年版)",
                "革命单搞军事不行",
                "(1964年5月25日）",
                "革命单搞军事不行，如不建立根据地，跟群众没有密切联系。",
                "草堂闲人 整理",
                "注释:",
                "[1] 这条注释应删除。",
                "谈学生健康问题(一九五八年一月三十日）要使学生身体好。",
                "*这是题解，应删除。注释：[1] 注释也应删除。",
                "",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.txt"
            output_path = Path(tmp) / "Mao.txt"
            input_path.write_text(source, encoding="utf-8")

            stats = module.extract_file(input_path, output_path, dedupe=True)
            result = output_path.read_text(encoding="utf-8")

        self.assertEqual(stats.article_count, 3)
        self.assertIn("前一篇文章", result)
        self.assertIn("（1964年4月16日）", result)
        self.assertIn("革命单搞军事不行", result)
        self.assertIn("（1964年5月25日）", result)
        self.assertIn("谈学生健康问题", result)
        self.assertIn("（一九五八年一月三十日）", result)
        self.assertIn("要使学生身体好。", result)
        self.assertNotIn("根据一九六四年四月十七日", result)
        self.assertNotIn("毛泽东选集第一、二、三、四卷", result)
        self.assertNotIn("草堂闲人 整理", result)
        self.assertNotIn("注释", result)
        self.assertNotIn("这条注释应删除", result)
        self.assertNotIn("题解", result)


if __name__ == "__main__":
    unittest.main()
