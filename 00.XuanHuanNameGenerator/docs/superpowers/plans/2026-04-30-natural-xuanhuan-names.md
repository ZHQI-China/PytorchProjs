# Natural Xuanhuan Names Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace noisy random fantasy-character name generation with a smaller, higher-quality dataset of realistic Chinese names with light xianxia flavor.

**Architecture:** Keep the existing script layout under `data/scripts/`. `generate_xuanhuan_names.py` owns source surname and given-name pools; `sample_names.py` owns weighted sampling and writes `data/names.txt`. Tests import the scripts directly and verify path handling, removal of exhaustive random pair generation, and output quality constraints.

**Tech Stack:** Python standard library, pytest, UTF-8 text data files.

---

### Task 1: Add Quality Tests

**Files:**
- Create: `tests/test_xuanhuan_name_generation.py`
- Modify: none

- [ ] **Step 1: Write tests for project-root paths and name pool quality**

```python
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


def test_sampled_names_are_unique_short_and_mostly_surname_based(tmp_path):
    sampler = load_script("sample_names")

    first_names = ["李", "王", "沈", "顾", "南宫"]
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
    assert all(2 <= len(name) <= 4 for name in names)
    assert sum(name in special_names for name in names) == 2
```

- [ ] **Step 2: Run tests and verify failures**

Run: `python -m pytest tests/test_xuanhuan_name_generation.py -v`

Expected: FAIL because paths point to `data/data`, the given-name pool contains exhaustive pair combinations, and `build_sampled_names` is not defined.

### Task 2: Refactor Generation Scripts

**Files:**
- Modify: `data/scripts/generate_xuanhuan_names.py`
- Modify: `data/scripts/sample_names.py`

- [ ] **Step 1: Fix `DATA_DIR` to point at project `data/`**

Set `PROJECT_ROOT = Path(__file__).resolve().parents[2]` and `DATA_DIR = PROJECT_ROOT / "data"` in both scripts.

- [ ] **Step 2: Replace exhaustive given-name combinations with curated pools**

Keep common real surnames, add realistic common given names, keep a small xianxia-flavored pool, and make `build_second_names()` return only curated one- and two-character given names.

- [ ] **Step 3: Extract `build_sampled_names()`**

Move sampling into a testable function that accepts name lists, target count, special ratio, and seed, then returns unique names.

- [ ] **Step 4: Run unit tests**

Run: `python -m pytest tests/test_xuanhuan_name_generation.py -v`

Expected: PASS.

### Task 3: Regenerate Data and Verify Dataset Shape

**Files:**
- Update generated data: `data/first_names.txt`
- Update generated data: `data/second_names.txt`
- Update generated data: `data/special_names.txt`
- Update generated data: `data/names.txt`

- [ ] **Step 1: Regenerate source pools**

Run: `python data/scripts/generate_xuanhuan_names.py`

Expected: writes curated source files under `data/`.

- [ ] **Step 2: Regenerate training names**

Run: `python data/scripts/sample_names.py`

Expected: writes `data/names.txt`.

- [ ] **Step 3: Verify sample distribution**

Run: PowerShell length distribution and sample preview.

Expected: names are 2-4 Chinese characters, with natural examples such as common surnames plus real or lightly xianxia-style given names.
