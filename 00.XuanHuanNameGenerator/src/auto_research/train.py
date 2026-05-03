"""
Autoresearch training script for the XuanHuan MLP name model.

Usage from 00.XuanHuanNameGenerator:
    python src/auto_research/train.py > run.log 2>&1

Only this file should be edited during hyperparameter experiments.
"""

from __future__ import annotations

import math
import os
import platform
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from auto_research import prepare


@dataclass(frozen=True)
class TrainConfig:
    seed: int = 0
    block_size: int = 3
    embedding_dim: int = 2
    hidden_dim: int = 100
    batch_size: int = 32
    lr_base: float = 0.3
    lr_min: float = 1e-5
    warmup_steps: int = 10_000
    max_steps: int = 200_000
    time_budget: float = prepare.TIME_BUDGET
    eval_batch_size: int = 4096


class NameMLP(nn.Module):
    def __init__(self, vocab_size: int, block_size: int, embedding_dim: int, hidden_dim: int):
        super().__init__()
        self.block_size = block_size
        self.embedding_dim = embedding_dim
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.fc1 = nn.Linear(block_size * embedding_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, vocab_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        emb = self.embedding(x)
        h = torch.tanh(self.fc1(emb.view(emb.shape[0], -1)))
        return self.fc2(h)


def init_model(config: TrainConfig, vocab_size: int, device: torch.device) -> NameMLP:
    model = NameMLP(
        vocab_size=vocab_size,
        block_size=config.block_size,
        embedding_dim=config.embedding_dim,
        hidden_dim=config.hidden_dim,
    ).to(device)
    with torch.no_grad():
        model.embedding.weight.normal_(0.0, 1.0)
        scale = (5 / 3) / math.sqrt(config.embedding_dim * config.block_size) * 0.4
        model.fc1.weight.normal_(0.0, scale)
        model.fc1.bias.normal_(0.0, 0.2)
        model.fc2.weight.normal_(0.0, 0.01)
        model.fc2.bias.zero_()
    return model


def get_lr(config: TrainConfig, step: int) -> float:
    if step < config.max_steps / 2:
        return config.lr_base
    if step > config.max_steps - config.max_steps / 4:
        return config.lr_base / 100
    return config.lr_base / 10


def current_peak_memory_gb(device: torch.device) -> float:
    if device.type == "cuda":
        return torch.cuda.max_memory_allocated() / 1024 / 1024 / 1024
    if platform.system() == "Windows":
        import ctypes
        from ctypes import wintypes

        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        psapi = ctypes.WinDLL("psapi.dll")
        kernel32 = ctypes.WinDLL("kernel32.dll")
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(ProcessMemoryCounters),
            wintypes.DWORD,
        ]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        handle = kernel32.GetCurrentProcess()
        ok = psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
        if ok:
            return counters.PeakWorkingSetSize / 1024 / 1024 / 1024
    try:
        import resource

        peak_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return peak_kb / 1024 / 1024
    except (ImportError, AttributeError):
        return 0.0
    return 0.0


def train(config: TrainConfig):
    torch.manual_seed(config.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    generator = torch.Generator(device=device.type).manual_seed(config.seed)
    bundle = prepare.load_data_bundle(seed=config.seed)

    x_train, y_train = prepare.build_dataset(bundle.train_tokens, config.block_size, bundle.stoi, device=device)
    x_val, y_val = prepare.build_dataset(bundle.val_tokens, config.block_size, bundle.stoi, device=device)
    x_test, y_test = prepare.build_dataset(bundle.test_tokens, config.block_size, bundle.stoi, device=device)
    model = init_model(config, bundle.vocab_size, device)

    parameters = list(model.parameters())
    t_start = time.time()
    t_start_training = time.time()
    smooth_loss = 0.0
    step = 0
    last_loss = float("nan")

    while True:
        batch_idxs = torch.randint(0, x_train.shape[0], (config.batch_size,), generator=generator, device=device)
        logits = model(x_train[batch_idxs])
        loss = F.cross_entropy(logits, y_train[batch_idxs])

        for p in parameters:
            p.grad = None
        loss.backward()

        lr = get_lr(config, step)
        with torch.no_grad():
            for p in parameters:
                p.add_(p.grad, alpha=-lr)

        last_loss = float(loss.item())
        smooth_loss = 0.9 * smooth_loss + 0.1 * last_loss
        elapsed = time.time() - t_start_training
        if step % 1000 == 0:
            debiased = smooth_loss / (1 - 0.9 ** (step + 1))
            print(
                f"step {step:06d} | train_loss: {debiased:.6f} | "
                f"lr: {lr:.6f} | elapsed: {elapsed:.1f}s",
                flush=True,
            )

        if math.isnan(last_loss) or last_loss > 100:
            print("FAIL")
            raise SystemExit(1)

        step += 1
        if step >= config.max_steps:
            break

    training_seconds = time.time() - t_start_training
    train_loss, train_acc = prepare.evaluate_loss_and_accuracy(model, x_train, y_train, config.eval_batch_size)
    val_loss, val_acc = prepare.evaluate_loss_and_accuracy(model, x_val, y_val, config.eval_batch_size)
    test_loss, test_acc = prepare.evaluate_loss_and_accuracy(model, x_test, y_test, config.eval_batch_size)
    quality = prepare.evaluate_sample_quality(model, bundle, config.block_size, device, config.seed)

    prepare.RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    sample_path = prepare.RECORDS_DIR / "latest_samples.csv"
    prepare.write_sample_rows(sample_path, quality["rows"])

    total_seconds = time.time() - t_start
    peak_memory_gb = current_peak_memory_gb(device)
    print("---")
    print(f"val_loss:         {val_loss:.6f}")
    print(f"val_acc:          {val_acc:.6f}")
    print(f"train_loss:       {train_loss:.6f}")
    print(f"train_acc:        {train_acc:.6f}")
    print(f"test_loss:        {test_loss:.6f}")
    print(f"test_acc:         {test_acc:.6f}")
    print(f"training_seconds: {training_seconds:.1f}")
    print(f"total_seconds:    {total_seconds:.1f}")
    print(f"peak_memory_gb:   {peak_memory_gb:.1f}")
    print(f"num_steps:        {step}")
    print(f"valid_rate:       {quality['valid_rate']:.6f}")
    print(f"unique_rate:      {quality['unique_rate']:.6f}")
    print(f"examples:         {quality['examples']}")
    print(f"sample_csv:       {sample_path}")
    print(f"config:           {asdict(config)}")
    return {
        "val_loss": val_loss,
        "peak_memory_gb": peak_memory_gb,
        "training_seconds": training_seconds,
        "num_steps": step,
    }


if __name__ == "__main__":
    train(TrainConfig(time_budget=float(os.environ.get("AUTORESEARCH_TIME_BUDGET", prepare.TIME_BUDGET))))
