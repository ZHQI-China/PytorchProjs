from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
FIRST_NAMES_PATH = DATA_DIR / "first_names.txt"
SECOND_NAMES_PATH = DATA_DIR / "second_names.txt"
SPECIAL_NAMES_PATH = DATA_DIR / "special_names.txt"

# Real Chinese surnames. Common surnames appear first so sampling can weight
# toward names that read naturally without removing rarer surnames entirely.
FIRST_NAMES = [
    "李", "王", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴", "徐", "孙",
    "云", "楚", "洛", "墨", "牧", "风", "元",
    "胡", "朱", "高", "林", "何", "郭", "马", "罗", "梁", "宋", "郑", "谢",
    "韩", "唐", "冯", "于", "董", "萧", "程", "曹", "袁", "邓", "许", "傅",
    "沈", "曾", "彭", "吕", "苏", "卢", "蒋", "蔡", "贾", "丁", "魏", "薛",
    "叶", "阎", "余", "潘", "杜", "戴", "夏", "钟", "汪", "田", "任", "姜",
    "范", "方", "石", "姚", "谭", "廖", "邹", "熊", "金", "陆", "郝", "孔",
    "白", "崔", "康", "毛", "邱", "秦", "江", "史", "顾", "侯", "邵", "孟",
    "龙", "万", "段", "雷", "钱", "汤", "尹", "黎", "易", "常", "武", "乔",
    "贺", "赖", "龚", "文", "庞", "樊", "兰", "殷", "施", "陶", "洪", "翟",
    "安", "颜", "倪", "严", "牛", "温", "芦", "季", "俞", "章", "鲁", "葛",
    "韦", "申", "尤", "毕", "聂", "丛", "焦", "向", "柳", "邢", "路", "岳",
    "齐", "梅", "莫", "庄", "辛", "管", "祝", "左", "涂", "谷", "祁", "厉",
    "时", "舒", "耿", "牟", "卜", "路", "詹", "关", "苗", "凌", "费", "纪",
    "靳", "盛", "童", "欧", "甄", "项", "曲", "成", "游", "阳", "裴", "席",
    "卫", "查", "屈", "鲍", "覃", "霍", "翁", "隋", "甘", "景",
    "薄", "单", "包", "司", "柏", "宁", "柯", "阮", "桂", "闵", "欧阳", "司马",
    "上官", "诸葛", "南宫", "东方", "慕容", "令狐", "皇甫", "夏侯", "闻人",
    "长孙", "宇文", "尉迟", "轩辕", "百里", "端木", "公孙", "司徒", "司空",
    "钟离", "赫连", "西门", "东郭",
]

REAL_GIVEN_NAMES = [
    "立", "平", "宁", "安", "远", "明", "修", "文", "言", "泽", "川", "然",
    "清", "云", "衡", "舟", "行", "深", "临", "知", "微", "白", "青", "遥",
    "瑶", "婉", "晴", "月", "雪", "兰", "溪", "禾", "棠", "音", "瑜", "宁",
    "若", "初", "晚", "秋", "书", "南", "北", "昭", "瑾", "珩", "璟", "晏",
    "子涵", "子墨", "子衿", "子安", "子宁", "子清", "子渊", "子衡", "子瑜",
    "明远", "明川", "明轩", "明昭", "明微", "修远", "修文", "修齐", "修然",
    "清和", "清越", "清宁", "清远", "清秋", "清辞", "清欢", "清言", "清扬",
    "云舒", "云起", "云深", "云溪", "云泽", "云舟", "云知", "云岚", "云初",
    "若曦", "若宁", "若安", "若云", "若晴", "若瑶", "若溪", "若兰", "若水",
    "怀瑾", "怀瑜", "怀远", "怀安", "怀宁", "知微", "知秋", "知远", "知白",
    "景行", "景明", "景云", "景和", "景宁", "昭明", "昭华", "昭宁", "昭远",
    "青禾", "青溪", "青棠", "青岚", "青宁", "青竹", "晚晴", "晚棠", "晚舟",
    "听雨", "听雪", "听澜", "听风", "听云", "星河", "星洲", "星遥", "星临",
    "月白", "月华", "月宁", "月遥", "雪晴", "雪棠", "雪宁", "雪竹",
]

XIANXIA_GIVEN_NAMES = [
    "清玄", "玄清", "云澈", "云渊", "云霁", "云岫", "云衡", "云微",
    "墨渊", "墨尘", "墨寒", "墨离", "墨玄", "墨白", "墨衡", "墨微",
    "青玄", "青渊", "青冥", "青霄", "青离", "青衡", "青羽", "青鸾",
    "玄微", "玄宁", "玄明", "玄真", "玄衡", "玄霄", "玄羽", "玄月",
    "灵均", "灵溪", "灵微", "灵素", "灵月", "灵音", "灵雨", "灵瑶",
    "玉衡", "玉清", "玉宁", "玉微", "玉珩", "玉宸", "玉霄", "玉璃",
    "瑶光", "瑶华", "瑶音", "瑶月", "瑶清", "瑶宁", "瑶微", "瑶岚",
    "澜舟", "观澜", "听澜", "沧澜", "澜清", "澜宁", "澜微", "澜月",
    "长庚", "长风", "长歌", "长明", "长宁", "长安", "长离", "长渊",
    "无尘", "无涯", "无咎", "无念", "无双", "无衣", "无羡", "无恙",
    "归云", "归尘", "归鸿", "归远", "归舟", "归晚", "归月", "归宁",
    "扶摇", "惊鸿", "照夜", "问道", "抱朴", "守真", "含章", "执明",
    "承影", "承渊", "承霄", "承宁", "承安", "少微", "少衡", "少白",
]

SINGLE_GIVEN_CHARS = [
    "立", "宁", "安", "远", "明", "修", "言", "泽", "川", "然", "清", "云",
    "衡", "舟", "行", "微", "白", "青", "遥", "瑶", "婉", "晴", "月", "雪",
    "兰", "溪", "音", "瑜", "若", "初", "秋", "书", "昭", "瑾", "澈", "玄",
]

# Known person names only. Titles and epithets such as "大衍神君" are excluded
# from this training dataset so the model learns personal-name boundaries.
SPECIAL_NAMES = [
    "韩立", "南宫婉", "厉飞雨", "陈巧倩", "墨凤舞", "辛如音", "齐云霄",
    "元瑶", "风希", "白素", "萧炎", "林动", "牧尘", "云韵",
    "林清玄", "顾怀瑾", "沈听雪", "陆观澜", "谢知秋", "秦执明",
    "楚承影", "叶无尘", "许长安", "周明远", "苏清和", "温若曦",
    "洛云澈", "江墨渊", "唐青玄", "宁无咎", "程惊鸿", "陆照夜",
]


def unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def build_second_names() -> list[str]:
    return unique(REAL_GIVEN_NAMES + XIANXIA_GIVEN_NAMES + SINGLE_GIVEN_CHARS)


def write_lines(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    first_names = unique(FIRST_NAMES)
    second_names = build_second_names()
    special_names = unique(SPECIAL_NAMES)

    write_lines(FIRST_NAMES_PATH, first_names)
    write_lines(SECOND_NAMES_PATH, second_names)
    write_lines(SPECIAL_NAMES_PATH, special_names)

    normal_combinations = len(first_names) * len(second_names)
    print(f"Wrote {len(first_names)} surnames to {FIRST_NAMES_PATH}")
    print(f"Wrote {len(second_names)} given names to {SECOND_NAMES_PATH}")
    print(f"Wrote {len(special_names)} special names to {SPECIAL_NAMES_PATH}")
    print(f"Normal possible combinations: {normal_combinations}")


if __name__ == "__main__":
    main()
