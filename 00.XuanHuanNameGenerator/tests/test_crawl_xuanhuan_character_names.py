from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_crawler():
    script_path = PROJECT_ROOT / "data" / "scripts" / "crawl_xuanhuan_character_names.py"
    spec = importlib.util.spec_from_file_location("crawl_xuanhuan_character_names", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_extracts_character_names_from_html_without_titles():
    crawler = load_crawler()
    html = """
    <table>
      <tr><th>角色</th><th>介绍</th></tr>
      <tr><td>萧炎</td><td>斗破苍穹主角</td></tr>
      <tr><td>韩立</td><td>凡人修仙传主角</td></tr>
      <tr><td>大衍神君</td><td>称号，不应作为普通姓名</td></tr>
      <tr><td>南宫婉</td><td>人物</td></tr>
    </table>
    """

    names = crawler.extract_character_names(html)

    assert {"萧炎", "韩立", "南宫婉"} <= set(names)
    assert "大衍神君" not in names


def test_format_name_uses_longest_surname_match():
    crawler = load_crawler()
    surnames = ["欧", "欧阳", "南宫", "韩"]

    assert crawler.format_training_name("欧阳克", surnames) == "欧阳|克"
    assert crawler.format_training_name("南宫婉", surnames) == "南宫|婉"
    assert crawler.format_training_name("韩立", surnames) == "韩|立"


def test_expand_training_names_keeps_separator_uniqueness_and_length():
    crawler = load_crawler()
    surnames = ["萧", "韩", "林", "牧", "南宫"]
    seed_names = ["萧炎", "韩立", "林动", "牧尘", "南宫婉"]
    fallback_given_names = ["清玄", "听雪", "明远", "怀瑾", "云澈"]

    names = crawler.expand_training_names(
        seed_names=seed_names,
        surnames=surnames,
        fallback_given_names=fallback_given_names,
        target_count=30,
        seed=11,
    )

    assert len(names) == 30
    assert len(names) == len(set(names))
    assert all(name.count("|") == 1 for name in names)
    assert all(2 <= len(name.replace("|", "")) <= 4 for name in names)
    assert {"萧|炎", "韩|立", "林|动", "牧|尘", "南宫|婉"} <= set(names)


def test_read_source_lines_uses_fallback_when_primary_is_missing(tmp_path):
    crawler = load_crawler()
    primary = tmp_path / "missing.txt"
    fallback = tmp_path / "fallback.txt"
    fallback.write_text("韩\n南宫\n", encoding="utf-8")

    assert crawler.read_source_lines(primary, fallback) == ["韩", "南宫"]


def test_filter_seed_names_removes_webpage_noise():
    crawler = load_crawler()
    surnames = ["韩", "南宫", "关", "萧"]
    fallback_given_names = ["立", "婉", "炎", "清玄"]
    seed_names = ["韩立", "南宫婉", "萧炎", "关于维基", "韩立引诱", "萧炎曾是"]

    filtered = crawler.filter_seed_names(
        seed_names=seed_names,
        surnames=surnames,
        fallback_given_names=fallback_given_names,
    )

    assert filtered == ["韩立", "南宫婉", "萧炎"]


def test_extract_expandable_given_names_rejects_unhelpful_single_chars():
    crawler = load_crawler()
    surnames = ["韩", "萧", "柳", "徐"]
    seed_names = ["韩立", "萧炎", "柳神", "徐凤年"]
    fallback_given_names = ["立", "清玄", "听雪"]

    given_names = crawler.extract_expandable_given_names(
        seed_names=seed_names,
        surnames=surnames,
        fallback_given_names=fallback_given_names,
    )

    assert "立" in given_names
    assert "炎" in given_names
    assert "凤年" in given_names
    assert "神" not in given_names
