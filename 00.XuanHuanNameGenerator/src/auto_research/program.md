# XuanHuan MLP Autoresearch

This project follows the small-file discipline of `karpathy/autoresearch`.

## Setup

1. Work on branch `autoresearch/may3-xuanhuan`.
2. Treat `prepare.py` as fixed once the baseline run starts.
3. Edit only `train.py` during experiments.
4. Keep `results.tsv` uncommitted.

## Goal

Minimize `val_loss`. Lower is better. `valid_rate`, `unique_rate`, and generated examples are diagnostic only.

## Baseline

Run from `00.XuanHuanNameGenerator`:

```bash
python src/auto_research/train.py > run.log 2>&1
```

The migrated baseline is:

- `block_size=3`
- `embedding_dim=4`
- `hidden_dim=100`
- `batch_size=32`
- `lr_base=0.1`
- `seed=0`

## Results

Log every experiment in `src/auto_research/results.tsv`:

```text
commit	val_loss	memory_gb	status	description
```

Use `keep` for a lower `val_loss`, `discard` for an equal or worse run, and `crash` for failed runs.

## Loop

1. Check current git state.
2. Change one idea in `train.py`.
3. Commit the change.
4. Run training with stdout/stderr redirected to `run.log`.
5. Read `val_loss` and `peak_memory_gb`.
6. Append a row to `results.tsv`.
7. Keep the commit only if `val_loss` improves.

Initial experiments:

1. baseline
2. `hidden_dim=128`
3. `hidden_dim=64`
4. `batch_size=64`
5. `lr_base=0.05`
6. `lr_base=0.2`
7. `embedding_dim=6`
8. `block_size=4`
