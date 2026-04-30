import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "data" / "fanren" / "count_fanren_names.py"
SPEC = importlib.util.spec_from_file_location("count_fanren_names", SCRIPT_PATH)
count_fanren_names = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(count_fanren_names)


def test_extracts_person_names_and_titles_separately():
    text = (
        "韩立见到了南宫婉。银月和宝花、紫灵也到了。"
        "南陇侯说道，大衍神君点头。韩立又见南陇侯。"
    )

    seed_names = ["韩立", "南宫婉", "银月", "宝花", "紫灵"]
    person_names, titles = count_fanren_names.extract_people_and_titles(text, seed_names)
    person_rows = count_fanren_names.count_names(text, person_names)
    title_rows = count_fanren_names.count_names(text, titles)

    assert {row["name"] for row in person_rows} >= {"韩立", "南宫婉", "银月", "宝花", "紫灵"}
    assert "南陇侯" not in {row["name"] for row in person_rows}
    assert "大衍神君" not in {row["name"] for row in person_rows}

    assert {row["name"] for row in title_rows} >= {"南陇侯", "大衍神君"}
    assert "韩立" not in {row["name"] for row in title_rows}
    assert next(row for row in title_rows if row["name"] == "南陇侯")["count"] == 2
