from __future__ import annotations

import argparse
from collections import defaultdict
import re
from pathlib import Path

from pypinyin import Style, lazy_pinyin


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
INPUT_PATH = DATA_DIR / "names.txt"
OUTPUT_PATH = DATA_DIR / "names_pinyin.txt"
MAPPING_PATH = DATA_DIR / "pinyin_to_hanzi_names.txt"
STRUCTURED_OUTPUT_PATH = DATA_DIR / "names_pinyin_structured.txt"
STRUCTURED_MAPPING_PATH = DATA_DIR / "pinyin_structured_to_hanzi_names.txt"
COMPONENT_OUTPUT_PATH = DATA_DIR / "names_pinyin_components.txt"
COMPONENT_MAPPING_PATH = DATA_DIR / "pinyin_components_to_hanzi_names.txt"
COMPONENT_CHAR_MAPPING_PATH = DATA_DIR / "pinyin_components_to_hanzi_chars.txt"

SURNAME_PINYIN_OVERRIDES = {
    "曾": "zeng",
    "单": "shan",
    "解": "xie",
    "查": "zha",
    "仇": "qiu",
    "朴": "piao",
    "区": "ou",
    "乐": "yue",
    "盖": "ge",
    "长孙": "zhangsun",
    "万俟": "moqi",
    "尉迟": "yuchi",
}
SURNAME_SYLLABLE_OVERRIDES = {
    "曾": ["zeng"],
    "单": ["shan"],
    "解": ["xie"],
    "查": ["zha"],
    "仇": ["qiu"],
    "朴": ["piao"],
    "区": ["ou"],
    "乐": ["yue"],
    "盖": ["ge"],
    "长孙": ["zhang", "sun"],
    "万俟": ["mo", "qi"],
    "尉迟": ["yu", "chi"],
}
PINYIN_INITIALS = (
    "zh", "ch", "sh",
    "b", "p", "m", "f", "d", "t", "n", "l", "g", "k", "h",
    "j", "q", "x", "r", "z", "c", "s", "y", "w",
)


def chinese_to_pinyin(text: str) -> str:
    pinyin = "".join(lazy_pinyin(text, style=Style.NORMAL, strict=False))
    pinyin = pinyin.lower().replace("ü", "v").replace("u:", "v")
    pinyin = re.sub(r"[^a-z]", "", pinyin)
    if not pinyin:
        raise ValueError(f"Could not convert to pinyin: {text!r}")
    return pinyin


def normalize_pinyin(text: str) -> str:
    return text.lower().replace("ü", "v").replace("u:", "v")


def pinyin_syllable_to_structured(syllable: str) -> str:
    normalized = normalize_pinyin(syllable)
    for initial in PINYIN_INITIALS:
        if normalized.startswith(initial) and len(normalized) > len(initial):
            return f"{initial}:{normalized[len(initial):]}"
    return f"_:{normalized}"


def structured_token_to_components(token: str) -> list[str]:
    initial, final = token.split(":", 1)
    return [initial, final]


def chinese_char_to_structured_pinyin(char: str) -> str:
    initial = normalize_pinyin(lazy_pinyin(char, style=Style.INITIALS, strict=False)[0])
    final = normalize_pinyin(lazy_pinyin(char, style=Style.FINALS, strict=False)[0])
    initial = initial or "_"
    initial = re.sub(r"[^a-z_]", "", initial)
    final = re.sub(r"[^a-z]", "", final)
    if not final:
        raise ValueError(f"Could not convert to structured pinyin: {char!r}")
    return f"{initial}:{final}"


def text_to_structured_pinyin(text: str) -> str:
    return " ".join(chinese_char_to_structured_pinyin(char) for char in text)


def surname_to_pinyin(surname: str) -> str:
    if surname in SURNAME_PINYIN_OVERRIDES:
        return SURNAME_PINYIN_OVERRIDES[surname]
    return chinese_to_pinyin(surname)


def surname_to_structured_pinyin(surname: str) -> str:
    if surname in SURNAME_SYLLABLE_OVERRIDES:
        return " ".join(
            pinyin_syllable_to_structured(syllable)
            for syllable in SURNAME_SYLLABLE_OVERRIDES[surname]
        )
    return text_to_structured_pinyin(surname)


def structured_side_to_components(side: str) -> str:
    components: list[str] = []
    for token in side.split():
        components.extend(structured_token_to_components(token))
    return " ".join(components)


def convert_training_name(line: str) -> str:
    if line.count("|") != 1:
        raise ValueError(f"Expected a single '|' separator: {line!r}")
    surname, given_name = line.split("|", 1)
    if not surname or not given_name:
        raise ValueError(f"Expected non-empty surname and given name: {line!r}")
    return f"{surname_to_pinyin(surname)}|{chinese_to_pinyin(given_name)}"


def convert_training_name_structured(line: str) -> str:
    if line.count("|") != 1:
        raise ValueError(f"Expected a single '|' separator: {line!r}")
    surname, given_name = line.split("|", 1)
    if not surname or not given_name:
        raise ValueError(f"Expected non-empty surname and given name: {line!r}")
    return f"{surname_to_structured_pinyin(surname)}|{text_to_structured_pinyin(given_name)}"


def convert_training_name_components(line: str) -> str:
    structured = convert_training_name_structured(line)
    surname, given_name = structured.split("|", 1)
    return f"{structured_side_to_components(surname)} | {structured_side_to_components(given_name)}"


def component_syllables_for_name(line: str) -> list[tuple[str, str]]:
    if line.count("|") != 1:
        raise ValueError(f"Expected a single '|' separator: {line!r}")
    surname, given_name = line.split("|", 1)
    if not surname or not given_name:
        raise ValueError(f"Expected non-empty surname and given name: {line!r}")

    syllables: list[tuple[str, str]] = []
    surname_structured = surname_to_structured_pinyin(surname).split()
    if len(surname_structured) != len(surname):
        raise ValueError(f"Surname syllable count does not match characters: {line!r}")
    for char, structured_token in zip(surname, surname_structured):
        syllables.append((" ".join(structured_token_to_components(structured_token)), char))

    given_structured = text_to_structured_pinyin(given_name).split()
    if len(given_structured) != len(given_name):
        raise ValueError(f"Given-name syllable count does not match characters: {line!r}")
    for char, structured_token in zip(given_name, given_structured):
        syllables.append((" ".join(structured_token_to_components(structured_token)), char))
    return syllables


def convert_lines(lines: list[str]) -> list[str]:
    converted: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        converted_name = convert_training_name(stripped)
        converted.append(converted_name)
    return converted


def convert_lines_structured(lines: list[str]) -> list[str]:
    converted: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        converted_name = convert_training_name_structured(stripped)
        converted.append(converted_name)
    return converted


def convert_lines_components(lines: list[str]) -> list[str]:
    converted: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        converted_name = convert_training_name_components(stripped)
        converted.append(converted_name)
    return converted


def convert_line_by_mode(line: str, mode: str) -> str:
    if mode == "continuous":
        return convert_training_name(line)
    if mode == "structured":
        return convert_training_name_structured(line)
    if mode == "components":
        return convert_training_name_components(line)
    raise ValueError(f"Unknown pinyin conversion mode: {mode}")


def build_pinyin_mapping(
    lines: list[str],
    *,
    structured: bool = False,
    mode: str | None = None,
) -> dict[str, list[str]]:
    conversion_mode = mode or ("structured" if structured else "continuous")
    mapping: dict[str, list[str]] = defaultdict(list)
    seen_pairs: set[tuple[str, str]] = set()
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        pinyin_name = convert_line_by_mode(stripped, conversion_mode)
        pair = (pinyin_name, stripped)
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        mapping[pinyin_name].append(stripped)
    return dict(mapping)


def build_component_syllable_mapping(lines: list[str]) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = defaultdict(list)
    seen_pairs: set[tuple[str, str]] = set()
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        for component_syllable, char in component_syllables_for_name(stripped):
            pair = (component_syllable, char)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            mapping[component_syllable].append(char)
    return dict(mapping)


def serialize_mapping(mapping: dict[str, list[str]]) -> list[str]:
    return [f"{pinyin_name}\t{' '.join(names)}" for pinyin_name, names in mapping.items()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert separated Chinese names to pinyin.")
    parser.add_argument("--input", type=Path, default=INPUT_PATH)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--mapping-output", type=Path)
    parser.add_argument("--char-mapping-output", type=Path)
    parser.add_argument("--structured", action="store_true")
    parser.add_argument("--components", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.structured and args.components:
        raise ValueError("Choose only one of --structured or --components")
    lines = args.input.read_text(encoding="utf-8").splitlines()
    if args.components:
        mode = "components"
        default_output_path = COMPONENT_OUTPUT_PATH
        default_mapping_path = COMPONENT_MAPPING_PATH
        converted = convert_lines_components(lines)
    elif args.structured:
        mode = "structured"
        default_output_path = STRUCTURED_OUTPUT_PATH
        default_mapping_path = STRUCTURED_MAPPING_PATH
        converted = convert_lines_structured(lines)
    else:
        mode = "continuous"
        default_output_path = OUTPUT_PATH
        default_mapping_path = MAPPING_PATH
        converted = convert_lines(lines)
    output_path = args.output or default_output_path
    mapping_path = args.mapping_output or default_mapping_path
    mapping = build_pinyin_mapping(lines, mode=mode)

    output_path.write_text("\n".join(converted) + "\n", encoding="utf-8")
    mapping_path.write_text("\n".join(serialize_mapping(mapping)) + "\n", encoding="utf-8")
    print(f"Wrote {len(converted)} pinyin names to {output_path}")
    print(f"Wrote {len(mapping)} pinyin-to-hanzi rows to {mapping_path}")
    if args.components:
        char_mapping_path = args.char_mapping_output or COMPONENT_CHAR_MAPPING_PATH
        char_mapping = build_component_syllable_mapping(lines)
        char_mapping_path.write_text(
            "\n".join(serialize_mapping(char_mapping)) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {len(char_mapping)} pinyin-to-hanzi-char rows to {char_mapping_path}")


if __name__ == "__main__":
    main()
