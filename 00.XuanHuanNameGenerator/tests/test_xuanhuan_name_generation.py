from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    script_path = PROJECT_ROOT / "data" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_generation_paths_point_to_project_data_directory():
    generator = load_script("generate_xuanhuan_names")
    sampler = load_script("sample_names")

    assert generator.DATA_DIR == PROJECT_ROOT / "data"
    assert sampler.DATA_DIR == PROJECT_ROOT / "data"


def test_given_name_pool_is_curated_not_exhaustive_cross_product():
    generator = load_script("generate_xuanhuan_names")

    second_names = generator.build_second_names()

    assert len(second_names) < 600
    assert "清玄" in second_names
    assert "明远" in second_names
    assert "蛟巽" not in second_names
    assert "兑魄" not in second_names
    assert "坎宁" not in second_names


def test_sampled_names_are_unique_short_and_mostly_surname_based():
    sampler = load_script("sample_names")

    first_names = ["李", "王", "沈", "顾", "韩", "厉", "南宫"]
    second_names = ["立", "宁", "清玄", "明远", "听雪", "怀瑾"]
    special_names = ["韩立", "南宫婉", "厉飞雨"]

    names = sampler.build_sampled_names(
        first_names=first_names,
        second_names=second_names,
        special_names=special_names,
        target_count=20,
        special_ratio=0.1,
        seed=7,
    )

    assert len(names) == 20
    assert len(names) == len(set(names))
    assert all(name.count("|") == 1 for name in names)
    assert all(surname and given for surname, given in (name.split("|") for name in names))
    assert all(2 <= len(name.replace("|", "")) <= 4 for name in names)
    assert sum(name in {"韩|立", "南宫|婉", "厉|飞雨"} for name in names) == 2


def test_format_training_name_separates_longest_matching_surname():
    sampler = load_script("sample_names")

    surnames = ["欧", "欧阳", "南宫", "韩"]

    assert sampler.format_training_name("欧阳修", surnames) == "欧阳|修"
    assert sampler.format_training_name("南宫婉", surnames) == "南宫|婉"
    assert sampler.format_training_name("韩立", surnames) == "韩|立"
