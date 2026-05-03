"""Extract clean Mao text for training.

The source file is a PDF/OCR-style dump.  This script keeps article titles,
dates, and body text while removing tables of contents, page markers, notes,
and collector footer/header noise.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = SCRIPT_DIR.parent / "raw" / "毛泽东选集（1-7：原版五卷+静火+赤旗+草堂） POv5.txt"
DEFAULT_OUTPUT = SCRIPT_DIR.parent / "Mao.txt"


PAGE_MARKER_RE = re.compile(r"^=+第\d+页=+$")
FOOTER_DATE_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$")
PAGE_COUNT_RE = re.compile(r"^(?:第\s*)?\d+\s*[／/]\s*\d+\s*页?$")
DATE_RE = re.compile(r"^[（(][^）)]*(?:年|一九|二零|二〇|19|20)[^）)]*[）)]$")
INLINE_ARTICLE_RE = re.compile(r"^(.{1,60}?)([（(][^）)]*(?:年|一九|二零|二〇|19|20)[^）)]*[）)])(.*)$")
SINGLE_ARABIC_NUMBER_RE = re.compile(r"^\d+$")
VOLUME_RE = re.compile(r"^(?:第[一二三四五六七]卷|毛泽东选集第[一二三四五六七]卷)$")
PERIOD_HEADING_RE = re.compile(r"^[\u4e00-\u9fff]+时期(?:（[上下]）)?$")
CHAPTER_NUMBER_RE = re.compile(r"^[一二三四五六七八九十]+$")


STRUCTURAL_LINES = {
    "毛泽东选集",
    "目录",
    "出版说明",
    "第二版出版说明",
    "本书出版的说明",
    "版本信息",
    "全世界无产者，联合起来！",
    "王洋东",
    "福",
    "元",
    "整理",
    "草堂闲人",
    "草堂闲人整理",
}


SENTENCE_ENDINGS = "。！？；.!?;"
TITLE_ENDINGS = "。！？；，、：,.!?;:"


@dataclass(frozen=True)
class ExtractStats:
    input_line_count: int
    article_count: int
    duplicate_count: int
    output_char_count: int


@dataclass(frozen=True)
class ArticleStart:
    title: str
    date: str
    date_index: int
    body_after_date: str = ""


def normalize_line(line: str) -> str:
    return line.strip().lstrip("\ufeff")


def clean_title(title: str) -> str:
    return title.strip().rstrip("*＊").strip()


def normalize_date(date: str) -> str:
    date = date.strip()
    if date.startswith("(") and date.endswith("）"):
        return "（" + date[1:]
    if date.startswith("（") and date.endswith(")"):
        return date[:-1] + "）"
    if date.startswith("(") and date.endswith(")"):
        return "（" + date[1:-1] + "）"
    return date


def title_key(title: str) -> str:
    return re.sub(r"\s+", "", clean_title(title))


def is_noise_line(line: str) -> bool:
    if not line:
        return True
    compact = re.sub(r"\s+", "", line)
    if PAGE_MARKER_RE.match(line):
        return True
    if FOOTER_DATE_RE.match(line):
        return True
    if PAGE_COUNT_RE.match(line):
        return True
    if SINGLE_ARABIC_NUMBER_RE.match(line):
        return True
    if line in {"页", "第"}:
        return True
    if compact in {"整理", "草堂闲人", "草堂闲人整理"}:
        return True
    if line.startswith("======本书由"):
        return True
    if line.startswith("在网上搜集整理"):
        return True
    return False


def is_structural_line(line: str) -> bool:
    if line in STRUCTURAL_LINES:
        return True
    if VOLUME_RE.match(line):
        return True
    if PERIOD_HEADING_RE.match(line):
        return True
    if line.startswith("本全集包含"):
        return True
    return False


def is_source_note(line: str) -> bool:
    return bool(
        line.startswith("根据")
        or re.match(r"^根据.+刊印。?$", line)
        or line.startswith("来源：")
        or line.startswith("选自")
        or line.startswith("（根据")
        or line.startswith("(根据")
        or line.startswith("*这是")
    )


def is_date_line(line: str) -> bool:
    if "版" in line:
        return False
    return bool(DATE_RE.match(line))


def is_article_title_line(line: str) -> bool:
    if is_noise_line(line) or is_structural_line(line) or is_date_line(line):
        return False
    if line == "注释" or is_source_note(line):
        return False
    if "版" in line:
        return False
    if line[0] in "[〔(（0123456789":
        return False
    if len(line) > 50:
        return False
    if line.endswith(tuple(TITLE_ENDINGS)):
        return False
    return True


def find_article_start(lines: list[str], index: int) -> ArticleStart | None:
    inline = find_inline_article_start(lines[index], index)
    if inline is not None:
        return inline

    if not is_article_title_line(lines[index]):
        return None

    title_lines: list[str] = []
    cursor = index
    scanned = 0
    crossed_noise_after_title = False
    while cursor < len(lines) and scanned < 8:
        line = lines[cursor]
        scanned += 1

        if is_noise_line(line):
            if title_lines:
                crossed_noise_after_title = True
            cursor += 1
            continue

        if is_date_line(line):
            if title_lines:
                title = clean_title("".join(title_lines))
                return ArticleStart(title=title, date=normalize_date(line), date_index=cursor)
            return None

        if is_article_title_line(line) and len(title_lines) < 4:
            if crossed_noise_after_title:
                return None
            title_lines.append(clean_title(line))
            cursor += 1
            continue

        return None

    return None


def find_inline_article_start(line: str, index: int) -> ArticleStart | None:
    match = INLINE_ARTICLE_RE.match(line)
    if match is None:
        return None

    title = clean_title(match.group(1))
    date = match.group(2)
    if "版" in date:
        return None
    if not is_article_title_line(title):
        return None

    body_after_date = match.group(3).strip()
    return ArticleStart(
        title=title,
        date=normalize_date(date),
        date_index=index,
        body_after_date=body_after_date,
    )


def is_chapter_number(line: str) -> bool:
    return bool(CHAPTER_NUMBER_RE.match(line)) and len(line) <= 3


def should_flush_after_line(line: str, paragraph_lines: list[str]) -> bool:
    if not line.endswith(tuple(SENTENCE_ENDINGS)):
        return False
    paragraph = "".join(paragraph_lines)
    return len(paragraph) >= 80


def render_paragraph(paragraph_lines: list[str]) -> str:
    return "".join(part.strip() for part in paragraph_lines if part.strip())


def extract_text(lines: list[str], dedupe: bool = True) -> tuple[str, int, int]:
    output: list[str] = []
    paragraph_lines: list[str] = []
    seen_titles: set[str] = set()
    article_count = 0
    duplicate_count = 0
    in_article = False
    skipping_duplicate = False
    skipping_notes = False

    def flush_paragraph() -> None:
        if not in_article or skipping_duplicate or not paragraph_lines:
            paragraph_lines.clear()
            return
        paragraph = render_paragraph(paragraph_lines)
        paragraph_lines.clear()
        if paragraph:
            output.append(paragraph)
            output.append("")

    def start_article(article: ArticleStart) -> None:
        nonlocal article_count, duplicate_count, in_article, skipping_duplicate, skipping_notes
        flush_paragraph()
        key = title_key(article.title)
        skipping_notes = False
        in_article = True

        if dedupe and key in seen_titles:
            duplicate_count += 1
            skipping_duplicate = True
            return

        seen_titles.add(key)
        skipping_duplicate = False
        article_count += 1
        if output and output[-1] != "":
            output.append("")
        output.extend([article.title, "", article.date, ""])
        if article.body_after_date and not is_source_note(article.body_after_date):
            paragraph_lines.append(article.body_after_date)

    index = 0
    while index < len(lines):
        line = lines[index]
        article = find_article_start(lines, index)
        if article is not None:
            start_article(article)
            index = article.date_index + 1
            continue

        if is_noise_line(line):
            index += 1
            continue

        if line == "注释" or line.startswith(("注释:", "注释：")):
            flush_paragraph()
            skipping_notes = True
            index += 1
            continue

        if skipping_notes:
            index += 1
            continue

        if not in_article or skipping_duplicate:
            index += 1
            continue

        if "注释:" in line or "注释：" in line:
            before_note = re.split(r"注释[:：]", line, maxsplit=1)[0].strip()
            if before_note and not is_source_note(before_note):
                paragraph_lines.append(before_note)
            flush_paragraph()
            skipping_notes = True
            index += 1
            continue

        if is_structural_line(line) or is_source_note(line):
            flush_paragraph()
            if is_source_note(line):
                skipping_notes = True
            index += 1
            continue

        if is_chapter_number(line):
            flush_paragraph()
            output.append(line)
            output.append("")
            index += 1
            continue

        paragraph_lines.append(line)
        if should_flush_after_line(line, paragraph_lines):
            flush_paragraph()
        index += 1

    flush_paragraph()
    text = "\n".join(output).strip() + "\n"
    return text, article_count, duplicate_count


def extract_file(input_path: Path, output_path: Path, dedupe: bool = True) -> ExtractStats:
    lines = [normalize_line(line) for line in input_path.read_text(encoding="utf-8").splitlines()]
    text, article_count, duplicate_count = extract_text(lines, dedupe=dedupe)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8", newline="\n")
    return ExtractStats(
        input_line_count=len(lines),
        article_count=article_count,
        duplicate_count=duplicate_count,
        output_char_count=len(text),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract Mao body text for training.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="source txt path")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="clean output txt path")
    parser.add_argument("--no-dedupe", action="store_true", help="keep duplicate article titles")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stats = extract_file(args.input, args.output, dedupe=not args.no_dedupe)
    print(f"Input lines: {stats.input_line_count}")
    print(f"Articles output: {stats.article_count}")
    print(f"Duplicate titles skipped: {stats.duplicate_count}")
    print(f"Output chars: {stats.output_char_count}")
    print(f"Wrote: {args.output}")


if __name__ == "__main__":
    main()
