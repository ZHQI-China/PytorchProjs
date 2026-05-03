"""
Fixed data and evaluation utilities for XuanHuan MLP autoresearch.

This file mirrors the role of karpathy/autoresearch prepare.py: keep data
loading, splits, metrics, and sample validation stable while experiments edit
train.py.
"""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import torch
import torch.nn.functional as F


SEED = 0
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "names1" / "names1_pinyin_components.txt"
CHAR_MAPPING_PATH = PROJECT_ROOT / "data" / "names1" / "pinyin_components_to_hanzi_chars1.txt"
RECORDS_DIR = PROJECT_ROOT / "records" / "auto_research"
TIME_BUDGET = 60.0
EVAL_SAMPLE_COUNT = 100
MAX_SAMPLE_TOKENS = 20

INITIALS = {
    "_", "b", "p", "m", "f", "d", "t", "n", "l", "g", "k", "h",
    "j", "q", "x", "r", "z", "c", "s", "y", "w", "zh", "ch", "sh",
}

FINALS = {
    "a", "o", "e", "i", "u", "v",
    "ai", "ei", "ui", "ao", "ou", "iu", "ie", "ue", "er",
    "an", "en", "in", "un", "vn",
    "ang", "eng", "ing", "ong",
    "ia", "iao", "ian", "iang", "iong",
    "ua", "uo", "uai", "uan", "uang",
}


@dataclass(frozen=True)
class DataBundle:
    raw_tokens: list[list[str]]
    token_list: list[str]
    stoi: dict[str, int]
    itos: dict[int, str]
    train_tokens: list[list[str]]
    val_tokens: list[list[str]]
    test_tokens: list[list[str]]

    @property
    def vocab_size(self) -> int:
        return len(self.token_list)


def load_data_bundle(seed: int = SEED, data_path: Path = DATA_PATH) -> DataBundle:
    lines = data_path.read_text(encoding="utf-8").splitlines()
    raw_tokens = [line.split() for line in lines if line.strip()]
    token_list = sorted({"."} | {token for row in raw_tokens for token in row})
    stoi = {token: i for i, token in enumerate(token_list)}
    itos = {i: token for token, i in stoi.items()}

    shuffled = raw_tokens[:]
    random.Random(seed).shuffle(shuffled)
    n_train = int(0.8 * len(shuffled))
    n_val = int(0.9 * len(shuffled))
    return DataBundle(
        raw_tokens=raw_tokens,
        token_list=token_list,
        stoi=stoi,
        itos=itos,
        train_tokens=shuffled[:n_train],
        val_tokens=shuffled[n_train:n_val],
        test_tokens=shuffled[n_val:],
    )


def build_dataset(data: Iterable[list[str]], block_size: int, stoi: dict[str, int], device: torch.device | None = None):
    x_rows: list[list[int]] = []
    y_rows: list[int] = []
    for tokens in data:
        context_tokens = ["."] * block_size + tokens + ["."]
        target_tokens = tokens + ["."]
        for i, target in enumerate(target_tokens):
            x_rows.append([stoi[context_tokens[j]] for j in range(i, i + block_size)])
            y_rows.append(stoi[target])
    return (
        torch.tensor(x_rows, dtype=torch.long, device=device),
        torch.tensor(y_rows, dtype=torch.long, device=device),
    )


@torch.no_grad()
def evaluate_loss_and_accuracy(model, x: torch.Tensor, y: torch.Tensor, batch_size: int = 4096):
    model.eval()
    losses = []
    correct = 0
    count = 0
    for start in range(0, x.shape[0], batch_size):
        xb = x[start:start + batch_size]
        yb = y[start:start + batch_size]
        logits = model(xb)
        losses.append(F.cross_entropy(logits, yb, reduction="sum").item())
        correct += int((logits.argmax(dim=1) == yb).sum().item())
        count += int(yb.numel())
    model.train()
    return sum(losses) / count, correct / count


def is_valid_sample(tokens: list[str]) -> bool:
    if tokens.count("|") != 1:
        return False
    sep = tokens.index("|")
    if sep == 0 or sep == len(tokens) - 1:
        return False
    parts = tokens[:sep] + tokens[sep + 1:]
    if len(parts) % 2 != 0:
        return False
    for i in range(0, len(parts), 2):
        if parts[i] not in INITIALS or parts[i + 1] not in FINALS:
            return False
    return True


def load_component_char_mapping(path: Path = CHAR_MAPPING_PATH) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            key, chars_text = line.split("\t", 1)
            mapping[key] = chars_text.split()
    return mapping


def tokens_to_pinyin(tokens: list[str]) -> str:
    if "|" not in tokens:
        return " ".join(tokens)
    sep = tokens.index("|")
    return f"{' '.join(tokens[:sep])} | {' '.join(tokens[sep + 1:])}"


def tokens_to_name(tokens: list[str], mapping: dict[str, list[str]], rng: random.Random) -> str | None:
    if not is_valid_sample(tokens):
        return None
    sep = tokens.index("|")
    name_parts = []
    for side in (tokens[:sep], tokens[sep + 1:]):
        chars = []
        for i in range(0, len(side), 2):
            key = f"{side[i]} {side[i + 1]}"
            choices = mapping.get(key)
            chars.append(rng.choice(choices) if choices else side[i] + side[i + 1])
        name_parts.append("".join(chars))
    return "".join(name_parts)


@torch.no_grad()
def generate_samples(model, itos: dict[int, str], block_size: int, n: int, max_tokens: int, seed: int, device: torch.device):
    model.eval()
    sample_generator = torch.Generator(device=device.type).manual_seed(seed)
    samples: list[list[str]] = []
    for _ in range(n):
        has_first_name = False
        out: list[str] = []
        context = [0] * block_size
        for _ in range(max_tokens):
            x = torch.tensor([context], dtype=torch.long, device=device)
            probs = torch.softmax(model(x), dim=1)
            ix = torch.multinomial(probs, num_samples=1, replacement=True, generator=sample_generator).item()
            token = itos[ix]
            if token == ".":
                if has_first_name:
                    break
                continue
            if token == "|":
                if has_first_name:
                    break
                has_first_name = True
            context = context[1:] + [ix]
            out.append(token)
        samples.append(out)
    model.train()
    return samples


def evaluate_sample_quality(model, bundle: DataBundle, block_size: int, device: torch.device, seed: int = SEED):
    mapping = load_component_char_mapping()
    rng = random.Random(seed)
    samples = generate_samples(
        model=model,
        itos=bundle.itos,
        block_size=block_size,
        n=EVAL_SAMPLE_COUNT,
        max_tokens=MAX_SAMPLE_TOKENS,
        seed=seed,
        device=device,
    )
    rows = []
    valid_names = []
    for i, sample in enumerate(samples):
        valid = is_valid_sample(sample)
        name = tokens_to_name(sample, mapping, rng)
        if valid and name:
            valid_names.append(name)
        rows.append({
            "idx": i,
            "valid": valid,
            "token_len": len(sample),
            "pinyin_tokens": tokens_to_pinyin(sample),
            "name": name or "",
        })
    valid_count = len(valid_names)
    return {
        "valid_count": valid_count,
        "valid_rate": valid_count / max(1, len(samples)),
        "unique_count": len(set(valid_names)),
        "unique_rate": len(set(valid_names)) / max(1, valid_count),
        "examples": "、".join(valid_names[:8]),
        "rows": rows,
    }


def write_sample_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["idx", "valid", "token_len", "pinyin_tokens", "name"])
        writer.writeheader()
        writer.writerows(rows)
