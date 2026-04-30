# 结构化拼音：声母/韵母训练数据

## Summary

新增一套结构化拼音数据，不覆盖现有 `names_pinyin.txt` / `names1_pinyin.txt`。新格式按“每个汉字一个音节 token，音节内部拆成 `声母:韵母`”，继续保留 `|` 作为姓/名边界。

示例：

```text
韩|立 -> h:an|l:i
南宫|婉 -> n:an g:ong|w:an
欧阳|修 -> _:ou y:ang|x:iu
吕|清玄 -> l:v|q:ing x:uan
```

零声母用 `_`，`ü` 统一写成 `v`。

## Key Changes

- 扩展 `data/scripts/convert_names_to_pinyin.py`，新增结构化转换能力：
  - `convert_training_name_structured("韩|立") -> "h:an|l:i"`
  - 每个汉字独立转音节，避免把 `南宫` 错写成一个不可拆 token。
  - 继续使用已有多音姓覆盖表，如 `曾 -> zeng`、`单 -> shan`、`长孙 -> zhangsun`，但结构化输出时会拆成对应音节。
- 新增输出文件：
  - `data/names_pinyin_structured.txt`
  - `data/names1_pinyin_structured.txt`
  - `data/pinyin_structured_to_hanzi_names.txt`
  - `data/pinyin_structured_to_hanzi_names1.txt`
- 映射表仍用 TSV，一对多保留同音冲突：
  ```text
  h:an|l:i	韩|立 寒|立
  n:an g:ong|w:an	南宫|婉
  ```
- 保留旧连续拼音文件，方便后续对比：
  - `names_pinyin.txt`
  - `names1_pinyin.txt`
  - `pinyin_to_hanzi_names.txt`
  - `pinyin_to_hanzi_names1.txt`

## Test Plan

- 添加结构化转换单元测试：
  - `韩|立 -> h:an|l:i`
  - `南宫|婉 -> n:an g:ong|w:an`
  - `欧阳|修 -> _:ou y:ang|x:iu`
  - `吕|清玄 -> l:v|q:ing x:uan`
- 添加结构化映射测试：
  - 同一个结构化拼音 key 可对应多个汉字名。
  - TSV 每行格式为 `structured_pinyin<TAB>汉字名1 汉字名2 ...`。
- 数据校验：
  - 两份结构化文件每行都有且只有一个 `|`。
  - `|` 左右非空。
  - 每个音节 token 都匹配 `声母:韵母`。
  - 声母为空时必须是 `_`。
  - 映射表 key 必须能在结构化训练文件中找到。

## Assumptions

- 不加入声调，先只建模声母/韵母结构。
- 结构化拼音用空格分隔同一侧的多个汉字音节，用 `|` 分隔姓和名。
- 旧连续拼音文件继续保留，新的结构化文件作为下一组实验数据。
