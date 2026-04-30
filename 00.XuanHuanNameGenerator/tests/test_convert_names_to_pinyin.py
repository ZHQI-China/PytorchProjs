from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_converter():
    script_path = PROJECT_ROOT / "data" / "scripts" / "convert_names_to_pinyin.py"
    spec = importlib.util.spec_from_file_location("convert_names_to_pinyin", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_converts_separated_chinese_name_to_pinyin():
    converter = load_converter()

    assert converter.convert_training_name("韩|立") == "han|li"
    assert converter.convert_training_name("南宫|婉") == "nangong|wan"
    assert converter.convert_training_name("萧|薰儿") == "xiao|xuner"


def test_converts_lines_and_preserves_uniqueness():
    converter = load_converter()

    lines = ["韩|立", "南宫|婉", "", "韩|立"]

    assert converter.convert_lines(lines) == ["han|li", "nangong|wan"]


def test_rejects_line_without_single_separator():
    converter = load_converter()

    try:
        converter.convert_training_name("韩立")
    except ValueError as exc:
        assert "single '|'" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_uses_surname_pronunciation_for_polyphonic_surnames():
    converter = load_converter()

    assert converter.convert_training_name("曾|书书") == "zeng|shushu"
    assert converter.convert_training_name("单|修") == "shan|xiu"
    assert converter.convert_training_name("长孙|无忌") == "zhangsun|wuji"


def test_builds_one_to_many_pinyin_mapping():
    converter = load_converter()

    mapping = converter.build_pinyin_mapping(["韩|立", "寒|立", "南宫|婉", "韩|立"])

    assert mapping == {
        "han|li": ["韩|立", "寒|立"],
        "nangong|wan": ["南宫|婉"],
    }


def test_serializes_mapping_as_tab_separated_rows():
    converter = load_converter()
    mapping = {
        "han|li": ["韩|立", "寒|立"],
        "nangong|wan": ["南宫|婉"],
    }

    assert converter.serialize_mapping(mapping) == [
        "han|li\t韩|立 寒|立",
        "nangong|wan\t南宫|婉",
    ]


def test_converts_separated_chinese_name_to_structured_pinyin():
    converter = load_converter()

    assert converter.convert_training_name_structured("韩|立") == "h:an|l:i"
    assert converter.convert_training_name_structured("南宫|婉") == "n:an g:ong|w:an"
    assert converter.convert_training_name_structured("欧阳|修") == "_:ou y:ang|x:iu"
    assert converter.convert_training_name_structured("吕|清玄") == "l:v|q:ing x:uan"


def test_structured_pinyin_uses_polyphonic_surname_overrides():
    converter = load_converter()

    assert converter.convert_training_name_structured("曾|书书") == "z:eng|sh:u sh:u"
    assert converter.convert_training_name_structured("单|修") == "sh:an|x:iu"
    assert converter.convert_training_name_structured("长孙|无忌") == "zh:ang s:un|w:u j:i"


def test_builds_one_to_many_structured_pinyin_mapping():
    converter = load_converter()

    mapping = converter.build_pinyin_mapping(
        ["韩|立", "寒|立", "南宫|婉", "韩|立"],
        structured=True,
    )

    assert mapping == {
        "h:an|l:i": ["韩|立", "寒|立"],
        "n:an g:ong|w:an": ["南宫|婉"],
    }


def test_converts_separated_chinese_name_to_component_pinyin():
    converter = load_converter()

    assert converter.convert_training_name_components("韩|立") == "h an | l i"
    assert converter.convert_training_name_components("南宫|婉") == "n an g ong | w an"
    assert converter.convert_training_name_components("欧阳|修") == "_ ou y ang | x iu"
    assert converter.convert_training_name_components("吕|清玄") == "l v | q ing x uan"


def test_component_pinyin_mapping_keeps_hanzi_collisions():
    converter = load_converter()

    mapping = converter.build_pinyin_mapping(
        ["韩|立", "寒|立", "南宫|婉", "韩|立"],
        mode="components",
    )

    assert mapping == {
        "h an | l i": ["韩|立", "寒|立"],
        "n an g ong | w an": ["南宫|婉"],
    }


def test_builds_component_syllable_to_hanzi_mapping():
    converter = load_converter()

    mapping = converter.build_component_syllable_mapping(
        ["韩|立", "寒|立", "南宫|婉", "韩|立"]
    )

    assert mapping == {
        "h an": ["韩", "寒"],
        "l i": ["立"],
        "n an": ["南"],
        "g ong": ["宫"],
        "w an": ["婉"],
    }
