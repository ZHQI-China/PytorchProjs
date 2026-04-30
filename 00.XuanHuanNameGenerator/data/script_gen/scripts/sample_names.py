from __future__ import annotations

import random
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
FIRST_NAMES_PATH = DATA_DIR / "first_names.txt"
SECOND_NAMES_PATH = DATA_DIR / "second_names.txt"
SPECIAL_NAMES_PATH = DATA_DIR / "special_names.txt"
OUTPUT_PATH = DATA_DIR / "names.txt"
TARGET_COUNT = 12_000
SPECIAL_RATIO = 0.02
RANDOM_SEED = 20260430

COMMON_SURNAMES = {
    "李", "王", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴", "徐", "孙",
    "胡", "朱", "高", "林", "何", "郭", "马", "罗", "梁", "宋", "郑", "谢",
    "韩", "唐", "冯", "于", "董", "萧", "程", "曹", "袁", "邓", "许", "傅",
    "沈", "曾", "彭", "吕", "苏", "卢", "蒋", "蔡", "贾", "丁", "魏", "薛",
    "叶", "余", "潘", "杜", "戴", "夏", "钟", "汪", "田", "任", "姜", "顾",
}
COMMON_SURNAME_WEIGHT = 4


def read_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def weighted_surnames(first_names: list[str]) -> list[str]:
    weighted: list[str] = []
    for surname in first_names:
        weight = COMMON_SURNAME_WEIGHT if surname in COMMON_SURNAMES else 1
        weighted.extend([surname] * weight)
    return weighted


def format_training_name(name: str, first_names: list[str]) -> str:
    for surname in sorted(first_names, key=len, reverse=True):
        if name.startswith(surname) and len(name) > len(surname):
            return f"{surname}|{name[len(surname):]}"
    return name


def build_sampled_names(
    *,
    first_names: list[str],
    second_names: list[str],
    special_names: list[str],
    target_count: int,
    special_ratio: float,
    seed: int,
) -> list[str]:
    if target_count <= 0:
        return []
    if not first_names:
        raise ValueError("first_names must not be empty")
    if not second_names:
        raise ValueError("second_names must not be empty")

    rng = random.Random(seed)
    weighted_first_names = weighted_surnames(first_names)
    special_count = min(int(target_count * special_ratio), len(special_names), target_count)
    selected_special_names = [
        format_training_name(name, first_names) for name in rng.sample(special_names, special_count)
    ]

    names = list(selected_special_names)
    seen = set(names)
    max_combinations = len(set(first_names)) * len(set(second_names)) + len(set(special_names))
    if target_count > max_combinations:
        raise ValueError(
            f"target_count={target_count} exceeds available unique names={max_combinations}"
        )

    while len(names) < target_count:
        surname = rng.choice(weighted_first_names)
        given_name = rng.choice(second_names)
        plain_name = surname + given_name
        name = f"{surname}|{given_name}"
        if name not in seen and 2 <= len(plain_name) <= 4:
            seen.add(name)
            names.append(name)

    rng.shuffle(names)
    return names


def main() -> None:
    first_names = read_lines(FIRST_NAMES_PATH)
    second_names = read_lines(SECOND_NAMES_PATH)
    special_names = read_lines(SPECIAL_NAMES_PATH)

    names = build_sampled_names(
        first_names=first_names,
        second_names=second_names,
        special_names=special_names,
        target_count=TARGET_COUNT,
        special_ratio=SPECIAL_RATIO,
        seed=RANDOM_SEED,
    )

    OUTPUT_PATH.write_text("\n".join(names) + "\n", encoding="utf-8")
    print(f"Wrote {len(names)} names to {OUTPUT_PATH}")
    special_training_names = {format_training_name(name, first_names) for name in special_names}
    print(f"Included {sum(name in special_training_names for name in names)} special names")


if __name__ == "__main__":
    main()
