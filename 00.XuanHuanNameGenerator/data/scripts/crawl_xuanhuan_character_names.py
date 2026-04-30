from __future__ import annotations

from collections import Counter
import html
import json
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
FIRST_NAMES_PATH = DATA_DIR / "first_names.txt"
SECOND_NAMES_PATH = DATA_DIR / "second_names.txt"
FALLBACK_FIRST_NAMES_PATH = DATA_DIR / "script_gen" / "first_names.txt"
FALLBACK_SECOND_NAMES_PATH = DATA_DIR / "script_gen" / "second_names.txt"
OUTPUT_PATH = DATA_DIR / "names.txt"
CRAWLED_NAMES_PATH = DATA_DIR / "crawled_character_names.txt"
SOURCE_REPORT_PATH = DATA_DIR / "crawled_character_name_sources.json"
LOCAL_SEED_PATHS = [
    DATA_DIR / "fanren" / "fanren_extracted_names.txt",
]
TARGET_COUNT = 15_000
RANDOM_SEED = 20260430
REQUEST_DELAY_SECONDS = 0.8

SOURCES = [
    {
        "title": "斗破苍穹",
        "url": "https://zh.wikipedia.org/wiki/%E6%96%97%E7%A0%B4%E8%8B%8D%E7%A9%B9",
    },
    {
        "title": "凡人修仙传",
        "url": "https://zh.wikipedia.org/wiki/%E5%87%A1%E4%BA%BA%E4%BF%AE%E4%BB%99%E4%BC%A0",
    },
    {
        "title": "凡人修仙之仙界篇",
        "url": "https://zh.wikipedia.org/wiki/%E5%87%A1%E4%BA%BA%E4%BF%AE%E4%BB%99%E4%B9%8B%E4%BB%99%E7%95%8C%E7%AF%87",
    },
    {
        "title": "诛仙",
        "url": "https://zh.wikipedia.org/wiki/%E8%AA%85%E4%BB%99",
    },
    {
        "title": "星辰变",
        "url": "https://zh.wikipedia.org/wiki/%E6%98%9F%E8%BE%B0%E8%AE%8A",
    },
    {
        "title": "雪中悍刀行",
        "url": "https://zh.wikipedia.org/wiki/%E9%9B%AA%E4%B8%AD%E6%82%8D%E5%88%80%E8%A1%8C",
    },
    {
        "title": "斗罗大陆",
        "url": "https://zh.wikipedia.org/wiki/%E6%96%97%E7%BE%85%E5%A4%A7%E9%99%B8",
    },
    {
        "title": "凡人修仙传角色指南",
        "url": "https://www.im-mortal.cn/game_wiki/normal_character",
    },
]

MANUAL_SEED_NAMES = [
    "萧炎", "萧薰儿", "药尘", "韩立", "南宫婉", "厉飞雨", "陈巧倩", "辛如音",
    "齐云霄", "元瑶", "风希", "白素", "林动", "牧尘", "云韵", "林清玄",
    "顾怀瑾", "沈听雪", "陆观澜", "谢知秋", "秦执明", "楚承影", "叶无尘",
    "许长安", "周明远", "苏清和", "温若曦", "洛云澈", "江墨渊", "唐青玄",
    "宁无咎", "程惊鸿", "陆照夜", "张小凡", "陆雪琪", "碧瑶", "林惊羽",
    "田灵儿", "曾书书", "秦羽", "姜立", "侯费", "黑羽", "徐凤年", "徐脂虎",
    "徐渭熊", "姜泥", "南宫仆射", "陈芝豹", "李淳罡", "王仙芝", "石昊",
    "柳神", "火灵儿", "云曦", "叶凡", "姬紫月", "庞博", "安妙依", "狠人大帝",
    "唐三", "小舞", "戴沐白", "朱竹清", "宁荣荣", "奥斯卡", "马红俊",
]

TITLE_SUFFIXES = (
    "神君", "圣女", "道人", "老祖", "师祖", "真人", "居士", "上人", "夫人",
    "长老", "老怪", "老魔", "童子", "仙子", "大师", "魔尊", "圣祖", "妖王",
)
NON_NAME_WORDS = {
    "玄幻小说", "网络小说", "中国大陆", "主要角色", "登场人物", "角色介绍",
    "作者", "动画", "漫画", "电视剧", "网络动画", "小说", "改编", "起点中文",
    "修仙小说", "目录", "外部链接", "参考资料", "责任编辑", "更新时间",
}
ALLOW_UNSURNAMED_NAMES = {
    "碧瑶", "黑羽", "小舞", "奥斯卡", "药尘", "柳神", "云曦",
}


def read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_source_lines(primary_path: Path, fallback_path: Path) -> list[str]:
    lines = read_lines(primary_path)
    if lines:
        return lines
    return read_lines(fallback_path)


def unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def fetch_url(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "FantasyNameGenerator/0.1 (+local research; contact: none)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        content_type = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(content_type, errors="ignore")


def strip_html(raw_html: str) -> str:
    without_scripts = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw_html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", "\n", without_scripts)
    return html.unescape(text)


def is_probable_name(candidate: str) -> bool:
    if not 2 <= len(candidate) <= 4:
        return False
    if candidate in NON_NAME_WORDS:
        return False
    if any(candidate.endswith(suffix) for suffix in TITLE_SUFFIXES):
        return False
    return bool(re.fullmatch(r"[\u4e00-\u9fff]+", candidate))


def extract_character_names(raw_html: str) -> list[str]:
    text = strip_html(raw_html)
    candidates = re.findall(r"[\u4e00-\u9fff]{2,4}", text)
    return unique([candidate for candidate in candidates if is_probable_name(candidate)])


def format_training_name(name: str, surnames: list[str]) -> str | None:
    for surname in sorted(surnames, key=len, reverse=True):
        if name.startswith(surname) and len(name) > len(surname):
            return f"{surname}|{name[len(surname):]}"
    if name in ALLOW_UNSURNAMED_NAMES and len(name) >= 2:
        return f"{name[0]}|{name[1:]}"
    return None


def extract_given_names(seed_names: list[str], surnames: list[str]) -> list[str]:
    given_names: list[str] = []
    for name in seed_names:
        formatted = format_training_name(name, surnames)
        if formatted:
            _, given_name = formatted.split("|", 1)
            if 1 <= len(given_name) <= 2:
                given_names.append(given_name)
    return unique(given_names)


def extract_expandable_given_names(
    seed_names: list[str],
    surnames: list[str],
    fallback_given_names: list[str],
) -> list[str]:
    fallback_single_chars = {name for name in fallback_given_names if len(name) == 1}
    extra_single_chars = {
        "炎", "尘", "动", "韵", "羽", "昊", "凡", "博", "舞", "蝉", "凝",
        "蕴", "晗", "悦", "霞", "蝶", "灵", "越", "玉", "兰", "瑶",
    }
    expandable: list[str] = []
    for given_name in extract_given_names(seed_names, surnames):
        if len(given_name) == 2:
            expandable.append(given_name)
        elif given_name in fallback_single_chars or given_name in extra_single_chars:
            expandable.append(given_name)
    return unique(expandable)


def filter_seed_names(
    *,
    seed_names: list[str],
    surnames: list[str],
    fallback_given_names: list[str],
    trusted_names: list[str] | None = None,
) -> list[str]:
    trusted_name_set = set(trusted_names or [])
    allowed_given_names = set(fallback_given_names)
    allowed_given_names.update(extract_given_names(MANUAL_SEED_NAMES, surnames))
    filtered: list[str] = []
    for name in seed_names:
        formatted = format_training_name(name, surnames)
        if not formatted:
            continue
        _, given_name = formatted.split("|", 1)
        if name in MANUAL_SEED_NAMES or name in trusted_name_set or given_name in allowed_given_names:
            filtered.append(name)
    return unique(filtered)


def expand_training_names(
    *,
    seed_names: list[str],
    surnames: list[str],
    fallback_given_names: list[str],
    target_count: int,
    seed: int,
) -> list[str]:
    rng = random.Random(seed)
    formatted_seed_names = [
        formatted
        for formatted in (format_training_name(name, surnames) for name in seed_names)
        if formatted is not None and 2 <= len(formatted.replace("|", "")) <= 4
    ]
    seed_given_names = extract_expandable_given_names(seed_names, surnames, fallback_given_names)
    given_names = unique(seed_given_names + fallback_given_names)
    if not surnames:
        raise ValueError("surnames must not be empty")
    if not given_names:
        raise ValueError("given_names must not be empty")

    max_count = len(set(surnames)) * len(set(given_names)) + len(set(formatted_seed_names))
    if target_count > max_count:
        raise ValueError(f"target_count={target_count} exceeds available unique names={max_count}")

    names = unique(formatted_seed_names)
    seen = set(names)
    weighted_surnames = list(surnames) + list(surnames[:80]) * 2
    weighted_given_names = seed_given_names * 4 + fallback_given_names

    while len(names) < target_count:
        surname = rng.choice(weighted_surnames)
        given_name = rng.choice(weighted_given_names)
        plain_name = surname + given_name
        formatted = f"{surname}|{given_name}"
        if formatted not in seen and 2 <= len(plain_name) <= 4:
            seen.add(formatted)
            names.append(formatted)

    rng.shuffle(names)
    return names


def collect_seed_names() -> tuple[list[str], list[dict[str, object]]]:
    all_names = list(MANUAL_SEED_NAMES)
    report: list[dict[str, object]] = []
    for path in LOCAL_SEED_PATHS:
        names = read_lines(path)
        all_names.extend(names)
        report.append({
            "title": path.stem,
            "url": str(path),
            "status": "ok" if names else "missing",
            "count": len(names),
        })
    for source in SOURCES:
        title = source["title"]
        url = source["url"]
        try:
            raw_html = fetch_url(url)
            names = extract_character_names(raw_html)
            all_names.extend(names)
            report.append({"title": title, "url": url, "status": "ok", "count": len(names)})
        except (urllib.error.URLError, TimeoutError, UnicodeError) as exc:
            report.append({"title": title, "url": url, "status": "error", "error": str(exc)})
        time.sleep(REQUEST_DELAY_SECONDS)
    return unique(all_names), report


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    surnames = read_source_lines(FIRST_NAMES_PATH, FALLBACK_FIRST_NAMES_PATH)
    fallback_given_names = read_source_lines(SECOND_NAMES_PATH, FALLBACK_SECOND_NAMES_PATH)
    seed_names, report = collect_seed_names()
    trusted_names = []
    for path in LOCAL_SEED_PATHS:
        trusted_names.extend(read_lines(path))
    seed_names = filter_seed_names(
        seed_names=seed_names,
        surnames=surnames,
        fallback_given_names=fallback_given_names,
        trusted_names=trusted_names,
    )
    formatted_seed_names = [
        formatted
        for formatted in (format_training_name(name, surnames) for name in seed_names)
        if formatted is not None and 2 <= len(formatted.replace("|", "")) <= 4
    ]
    training_names = expand_training_names(
        seed_names=seed_names,
        surnames=surnames,
        fallback_given_names=fallback_given_names,
        target_count=TARGET_COUNT,
        seed=RANDOM_SEED,
    )

    CRAWLED_NAMES_PATH.write_text("\n".join(unique(formatted_seed_names)) + "\n", encoding="utf-8")
    OUTPUT_PATH.write_text("\n".join(training_names) + "\n", encoding="utf-8")
    SOURCE_REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lengths = Counter(len(name.replace("|", "")) for name in training_names)
    print(f"Wrote {len(unique(formatted_seed_names))} formatted crawled seed names to {CRAWLED_NAMES_PATH}")
    print(f"Wrote {len(training_names)} training names to {OUTPUT_PATH}")
    print("Length distribution:", dict(sorted(lengths.items())))


if __name__ == "__main__":
    main()
