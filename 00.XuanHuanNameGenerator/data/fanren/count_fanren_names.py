from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
import re
import urllib.request
from pathlib import Path


SOURCE_URL = (
    "https://raw.githubusercontent.com/qiuliw/Books/main/"
    "%E3%80%8A%E5%87%A1%E4%BA%BA%E4%BF%AE%E4%BB%99%E4%BC%A0%E3%80%8B"
    "%EF%BC%88%E6%A0%A1%E5%AF%B9%E7%89%88%E5%85%A8%E6%9C%AC%2B%E7%95%AA%E5%A4%96%EF%BC%89"
    "%E4%BD%9C%E8%80%85%EF%BC%9A%E5%BF%98%E8%AF%AD.txt"
)

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
TEXT_PATH = DATA_DIR / "fanrenxiuxianzhuan.txt"
NAMES_PATH = DATA_DIR / "fanren_names.txt"
EXTRACTED_NAMES_PATH = DATA_DIR / "fanren_extracted_names.txt"
EXTRACTED_TITLES_PATH = DATA_DIR / "fanren_extracted_titles.txt"
PERSON_CSV_PATH = DATA_DIR / "fanren_person_name_counts.csv"
PERSON_JSON_PATH = DATA_DIR / "fanren_person_name_counts.json"
TITLE_CSV_PATH = DATA_DIR / "fanren_title_counts.csv"
TITLE_JSON_PATH = DATA_DIR / "fanren_title_counts.json"
TEXT_ENCODINGS = ("utf-8-sig", "gb18030", "gbk")
CHINESE = r"\u4e00-\u9fff"
COMMON_SURNAMES = {
    "韩",
    "厉",
    "张",
    "墨",
    "陈",
    "李",
    "雷",
    "燕",
    "温",
    "董",
    "风",
    "向",
    "凌",
    "辛",
    "齐",
    "萧",
    "叶",
    "柳",
    "石",
    "许",
    "白",
    "梅",
    "乌",
    "魏",
    "马",
    "孙",
    "曲",
    "元",
    "龙",
    "凤",
    "金",
    "汪",
    "林",
    "宋",
    "赵",
    "王",
    "秦",
    "任",
    "富",
}
COMPOUND_SURNAMES = {
    "南宫",
    "令狐",
    "欧阳",
    "司徒",
    "司马",
    "诸葛",
    "皇甫",
}
SPECIAL_PERSON_NAMES = {
    "银月",
    "宝花",
    "紫灵",
    "曲魂",
    "啼魂",
    "冰凤",
    "木青",
    "纤纤",
    "明尊",
    "六极",
    "碧影",
    "陇东",
    "玲珑",
    "红拂",
    "风希",
    "妍丽",
    "曲儿",
    "金童",
}
TITLE_SUFFIXES = (
    "长老",
    "师祖",
    "老祖",
    "祖师",
    "仙子",
    "真人",
    "居士",
    "上人",
    "夫人",
    "圣祖",
    "神君",
    "大师",
    "老怪",
    "老魔",
    "道人",
    "侯",
)
KNOWN_TITLES = {
    "南陇侯",
    "大衍神君",
    "蟹道人",
}
GENERIC_PERSON_WORDS = {
    "一人",
    "二人",
    "三人",
    "几人",
    "二位",
    "两位",
    "几位",
    "诸位",
    "众人",
    "此人",
    "这人",
    "那人",
    "别人",
    "本人",
    "主人",
    "在下",
    "老夫",
    "老朽",
    "贫道",
    "妾身",
    "晚辈",
    "前辈",
    "道友",
    "师兄",
    "师弟",
    "师姐",
    "师妹",
    "长老",
    "老祖",
    "祖师",
    "仙子",
    "真人",
    "居士",
    "上人",
    "夫人",
    "魔尊",
    "圣祖",
    "神君",
    "大汉",
    "青年",
    "男子",
    "女子",
    "少女",
    "妇人",
    "美妇",
    "老者",
    "中年",
    "少年",
    "小童",
    "童子",
    "和尚",
    "儒生",
    "修士",
    "老僧",
    "道士",
    "弟子",
    "之人",
    "魔族",
    "妖族",
    "中年人",
    "异族人",
    "人妖两族",
    "老翁",
}
NON_NAME_PARTS = {
    "一个",
    "一些",
    "一声",
    "一下",
    "一种",
    "一般",
    "一阵",
    "一名",
    "一道",
    "一股",
    "一位",
    "有些",
    "现在",
    "知道",
    "其他",
    "不知",
    "不会",
    "露出",
    "同样",
    "东西",
    "竟然",
    "脸色",
    "忽然",
    "直接",
    "见此",
    "瞬间",
    "开始",
    "原本",
    "蓦然",
    "应该",
    "微微",
    "再次",
    "这样",
    "看来",
    "怎么",
    "这般",
    "这种",
    "淡淡",
    "进入",
    "恐怕",
    "情形",
    "银色",
    "缓缓",
    "当即",
    "不禁",
    "多谢",
    "既然",
    "这位",
    "可是",
    "这个",
    "我等",
    "刚才",
    "所有",
    "真是",
    "毕竟",
    "至于",
    "听到",
    "让韩",
    "难道",
    "十几",
    "不少",
    "合体",
    "当然",
    "大乘",
    "倒是",
    "几个",
    "不用",
    "大半",
    "人族",
    "这次",
    "所以",
    "原来",
    "这一次",
    "当年",
    "纵然",
    "这是",
    "那位",
    "需要",
    "黑袍",
    "听说",
    "许多",
    "希望",
    "麻烦",
    "当初",
    "没想到",
    "其余",
    "其实",
    "相信",
    "灵族",
    "多半",
    "说不定",
    "可惜",
    "不管",
    "阵法",
    "古魔",
    "想来",
    "不如",
    "女修",
    "汉子",
    "可见",
    "能让",
    "这名",
    "你这",
    "白衣",
    "自己",
    "老者",
    "少女",
    "女子",
    "美妇",
    "大汉",
    "青年",
    "男子",
    "妇人",
    "中年",
    "少年",
    "小童",
    "童子",
    "和尚",
    "儒生",
    "修士",
    "老僧",
    "道士",
    "他们",
    "她们",
    "我们",
    "你们",
    "对方",
    "这里",
    "那里",
    "此地",
    "此事",
    "此物",
    "此女",
    "此子",
    "这些",
    "那些",
    "什么",
    "如此",
    "只是",
    "但是",
    "不过",
    "因为",
    "没有",
    "不是",
    "已经",
    "突然",
    "只是",
    "如今",
    "顿时",
    "马上",
    "立刻",
    "自然",
    "虽然",
    "若是",
    "仿佛",
    "似乎",
    "终于",
    "附近",
    "远处",
    "身上",
    "手中",
    "口中",
    "眼中",
    "脸上",
    "心中",
    "神色",
    "目光",
    "声音",
    "法力",
    "元婴",
    "化神",
    "灵界",
    "人界",
    "魔界",
    "天渊城",
    "鬼灵门",
    "落云宗",
    "阴罗宗",
    "黄枫谷",
    "小极宫",
    "天鹏族",
    "木族",
    "灵族",
    "人族",
    "叶家",
    "陇家",
    "星宫",
    "天澜",
    "家族",
    "天鼎",
    "天鹏",
    "听韩",
    "听闻",
    "我看",
    "哪有",
    "除非",
    "要是",
    "想必",
    "要说",
    "这也是",
    "这就是",
    "换取",
    "难怪",
    "况且",
    "莫非",
    "当日",
    "跟在",
    "我说",
    "我想",
    "拜见",
    "敢问",
    "商盟",
    "姓韩",
    "小子",
    "老翁",
    "到时候",
    "任凭",
    "随时欢迎",
    "客卿",
    "厉声",
    "巨舟",
    "炼虚",
    "谨遵",
    "任何",
    "张口",
    "厉害",
    "金虫",
    "雷鸣",
    "乌黑",
    "元气",
    "元神",
    "元磁",
    "元子",
}
CONNECTIVE_CHARS = set("和与同给让被将把从向对为的是了")
TITLE_NAME_PATTERN = re.compile(
    rf"([{CHINESE}]{{1,4}}?)({'|'.join(TITLE_SUFFIXES)})"
)
PERSON_CONTEXT_PATTERNS = [
    re.compile(rf"(?:名叫|叫做|唤作|名为)([{CHINESE}]{{2,4}})"),
    re.compile(rf"“[^”]{{0,40}}”([{CHINESE}]{{2,4}}?)(?:说道|问道|笑道|冷笑道|淡淡道|沉声道|喝道|叫道|答道|叹道)"),
    re.compile(rf"([{CHINESE}]{{2,4}}?)(?:说道|问道|笑道|冷笑道|淡淡道|沉声道|喝道|叫道|答道|叹道|闻言|点头|摇头|苦笑|冷笑|微笑)"),
]
PERSON_AFTER_CHARS = set("，。？！、；：”）) \n\r\t见闻问说道笑冷沉喝叫答叹点摇")
PERSON_BEFORE_CHARS = set("，。？！、；：“（( \n\r\t见问叫名为是与和")

NAME_CONTEXT_PATTERNS = [
    re.compile(rf"([{CHINESE}]{{2,4}}?)(?:道友|兄弟|师兄|师弟|师姐|师妹|前辈|长老)"),
    re.compile(rf"(?:姓|名叫|叫做|唤作|自称|名为)([{CHINESE}]{{2,4}})"),
    re.compile(rf"“[^”]{{0,40}}”([{CHINESE}]{{2,4}}?)(?:说道|问道|笑道|冷笑道|淡淡道|沉声道|喝道|叫道|答道|叹道)"),
    re.compile(rf"(?:这位|那位|名|叫|称呼|号称)([{CHINESE}]{{2,4}}?)(?:道友|前辈|长老|老祖|祖师|仙子|真人|居士|上人|夫人|圣祖|神君|大师|老怪|老魔|道人)"),
]


def download_source(url: str = SOURCE_URL, output_path: Path = TEXT_PATH) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        content = response.read()
    output_path.write_bytes(content)


def load_names(path: Path = NAMES_PATH) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        name = line.strip()
        if not name or name.startswith("#"):
            continue
        if name not in seen:
            seen.add(name)
            names.append(name)
    return names


def is_likely_name(candidate: str) -> bool:
    candidate = candidate.strip()
    if len(candidate) < 2 or len(candidate) > 6:
        return False
    if not re.fullmatch(rf"[{CHINESE}]+", candidate):
        return False
    if candidate in GENERIC_PERSON_WORDS:
        return False
    if any(part in candidate for part in NON_NAME_PARTS):
        return False
    if any(char in candidate for char in CONNECTIVE_CHARS):
        return False
    if candidate[0] in "的一是在和与及或并但却而若如被把向从于为以将则便就都又也还只很更最已曾正乃即且这那此有不没无可要想听回我敢拜跟连随飞音高黑击魔装说谨过见论谢道里阴":
        return False
    if candidate[-1] in "的一了着过地得之和与及或并而也都就便则时后前中内外上下大小多少位名宗族门城宫家光色袍":
        return False
    return True


def has_known_surname(candidate: str) -> bool:
    return any(candidate.startswith(surname) for surname in COMPOUND_SURNAMES) or (
        candidate[0] in COMMON_SURNAMES
    )


def is_title(candidate: str) -> bool:
    return candidate.endswith(TITLE_SUFFIXES)


def normalize_title(base: str, suffix: str) -> str:
    if len(base) > 2:
        base = base[-2:]
    return base + suffix


def is_likely_person_name(candidate: str) -> bool:
    if candidate in SPECIAL_PERSON_NAMES:
        return True
    if is_title(candidate):
        return False
    if candidate.endswith(
        (
            "兄",
            "弟",
            "姐",
            "妹",
            "道",
            "道友",
            "前辈",
            "师",
            "某",
            "发",
            "壁",
            "柱",
            "台",
            "屋",
            "气",
            "神",
            "磁",
            "色",
            "光",
            "芒",
            "丝",
            "球",
            "竹",
            "兽",
            "云",
            "袍",
            "巨",
            "长老",
            "师祖",
            "候",
        )
    ):
        return False
    if not is_likely_name(candidate):
        return False
    if not has_known_surname(candidate):
        return False
    if len(candidate) > 4:
        return False
    return True


def extract_title_candidates(text: str, seed_names: list[str] | None = None) -> list[str]:
    counter: Counter[str] = Counter()
    seed_names = seed_names or []
    for title in KNOWN_TITLES:
        if text.count(title) > 0:
            counter[title] += text.count(title)
    for name in seed_names:
        if is_title(name) and is_likely_name(name):
            counter[name] += max(1, text.count(name))

    for match in TITLE_NAME_PATTERN.finditer(text):
        base, suffix = match.groups()
        candidate = normalize_title(base, suffix)
        if is_likely_name(candidate):
            counter[candidate] += 1

    return filter_title_expansions(sorted(counter, key=lambda name: (-counter[name], name)))


def filter_title_expansions(titles: list[str]) -> list[str]:
    title_set = set(titles)
    filtered: list[str] = []
    for title in titles:
        if title in KNOWN_TITLES:
            filtered.append(title)
            continue
        if any(
            len(longer) > len(title) and longer.endswith(title)
            for longer in title_set
        ):
            continue
        filtered.append(title)
    return filtered


def extract_person_candidates(text: str, seed_names: list[str] | None = None) -> list[str]:
    counter: Counter[str] = Counter()
    seed_names = seed_names or []

    for name in seed_names:
        if is_likely_person_name(name):
            counter[name] += max(1, text.count(name))

    for name in SPECIAL_PERSON_NAMES:
        if text.count(name) > 0:
            counter[name] += text.count(name)

    protected_names = set(seed_names) | SPECIAL_PERSON_NAMES
    return filter_person_name_expansions(
        sorted(counter, key=lambda name: (-counter[name], name)),
        protected_names,
    )


def has_person_context(text: str, start: int, end: int) -> bool:
    before = text[start - 1] if start > 0 else "\n"
    after = text[end] if end < len(text) else "\n"
    return before in PERSON_BEFORE_CHARS or after in PERSON_AFTER_CHARS


def scan_surname_person_candidates(text: str) -> list[str]:
    evidence: Counter[str] = Counter()
    surnames = sorted(COMPOUND_SURNAMES, key=len, reverse=True)

    for index in range(len(text)):
        matched_compound = next(
            (surname for surname in surnames if text.startswith(surname, index)),
            None,
        )
        if matched_compound:
            for total_len in (3, 4):
                candidate = text[index : index + total_len]
                if is_likely_person_name(candidate) and has_person_context(
                    text, index, index + total_len
                ):
                    evidence[candidate] += 1
            continue

        if text[index] in COMMON_SURNAMES:
            for total_len in (2, 3):
                candidate = text[index : index + total_len]
                if is_likely_person_name(candidate) and has_person_context(
                    text, index, index + total_len
                ):
                    evidence[candidate] += 1

    return [
        name
        for name, count in evidence.items()
        if count >= 2 or any(name.startswith(surname) for surname in COMPOUND_SURNAMES)
    ]


def filter_person_name_expansions(
    names: list[str], protected_names: set[str] | None = None
) -> list[str]:
    protected_names = protected_names or set()
    name_set = set(names)
    filtered: list[str] = []
    for name in names:
        if name in protected_names:
            filtered.append(name)
            continue
        if any(
            len(prefix) >= 2
            and name.startswith(prefix)
            and len(name) > len(prefix)
            and prefix in name_set
            for prefix_len in (2, 3)
            for prefix in [name[:prefix_len]]
        ):
            continue
        filtered.append(name)
    return filtered


def extract_people_and_titles(
    text: str, seed_names: list[str] | None = None
) -> tuple[list[str], list[str]]:
    seed_names = seed_names or []
    person_names = extract_person_candidates(text, seed_names)
    titles = extract_title_candidates(text, seed_names)
    title_set = set(titles)
    person_names = [name for name in person_names if name not in title_set]
    return person_names, titles


def extract_name_candidates(
    text: str,
    seed_names: list[str],
    min_auto_evidence: int = 2,
) -> list[str]:
    counter: Counter[str] = Counter()
    seed_set = set(seed_names)
    for name in seed_names:
        if name in seed_set:
            counter[name] += max(1, text.count(name))

    for match in TITLE_NAME_PATTERN.finditer(text):
        base, title = match.groups()
        if len(base) > 2:
            base = base[-2:]
        candidate = base + title
        if is_likely_name(candidate):
            counter[candidate] += 1

    for pattern in NAME_CONTEXT_PATTERNS:
        for match in pattern.finditer(text):
            candidate = match.group(1)
            if is_likely_name(candidate):
                counter[candidate] += 1

    accepted = []
    for name, evidence_count in counter.items():
        if name in seed_set or evidence_count >= min_auto_evidence:
            accepted.append(name)
    return sorted(accepted, key=lambda name: (-counter[name], name))


def write_word_list(words: list[str], path: Path) -> None:
    path.write_text("\n".join(words) + "\n", encoding="utf-8")


def write_extracted_names(names: list[str], path: Path = EXTRACTED_NAMES_PATH) -> None:
    write_word_list(names, path)


def count_names(text: str, names: list[str]) -> list[dict[str, int | str]]:
    rows = [
        {"name": name, "count": count}
        for name in names
        if (count := text.count(name)) > 0
    ]
    rows.sort(key=lambda row: (-int(row["count"]), str(row["name"])))
    return rows


def read_source_text(path: Path = TEXT_PATH) -> str:
    last_error: UnicodeDecodeError | None = None
    for encoding in TEXT_ENCODINGS:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError as error:
            last_error = error
    if last_error is not None:
        raise last_error
    return path.read_text()


def write_csv(rows: list[dict[str, int | str]], path: Path) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["name", "count"])
        writer.writeheader()
        writer.writerows(rows)


def write_json(rows: list[dict[str, int | str]], path: Path) -> None:
    path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_counts(extract_names: bool = True) -> list[dict[str, int | str]]:
    if not TEXT_PATH.exists():
        raise FileNotFoundError(
            f"Missing source text: {TEXT_PATH}. Run with --download first."
        )
    if not NAMES_PATH.exists():
        raise FileNotFoundError(f"Missing name list: {NAMES_PATH}")

    text = read_source_text()
    seed_names = load_names()
    names = seed_names
    if extract_names:
        names, titles = extract_people_and_titles(text, seed_names)
        write_extracted_names(names)
        write_word_list(titles, EXTRACTED_TITLES_PATH)
        title_rows = count_names(text, titles)
        write_csv(title_rows, TITLE_CSV_PATH)
        write_json(title_rows, TITLE_JSON_PATH)
    rows = count_names(text, names)
    write_csv(rows, PERSON_CSV_PATH)
    write_json(rows, PERSON_JSON_PATH)
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and count character names in 《凡人修仙传》."
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download or overwrite data/fanrenxiuxianzhuan.txt before counting.",
    )
    parser.add_argument(
        "--manual-only",
        action="store_true",
        help="Only count names listed in data/fanren_names.txt.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.download:
        download_source()
        print(f"Downloaded: {TEXT_PATH}")

    rows = build_counts(extract_names=not args.manual_only)
    print(f"Wrote: {PERSON_CSV_PATH}")
    print(f"Wrote: {PERSON_JSON_PATH}")
    if not args.manual_only:
        print(f"Wrote: {EXTRACTED_NAMES_PATH}")
        print(f"Wrote: {EXTRACTED_TITLES_PATH}")
        print(f"Wrote: {TITLE_CSV_PATH}")
        print(f"Wrote: {TITLE_JSON_PATH}")
    if rows:
        top = rows[0]
        print(f"Top name: {top['name']} ({top['count']})")


if __name__ == "__main__":
    main()
