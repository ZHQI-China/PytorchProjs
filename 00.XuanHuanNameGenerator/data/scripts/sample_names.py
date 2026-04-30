from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
_IMPL_PATH = DATA_DIR / "script_gen" / "scripts" / "sample_names.py"

_SPEC = importlib.util.spec_from_file_location("_script_gen_sample_names", _IMPL_PATH)
_IMPL = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_IMPL)

COMMON_SURNAMES = _IMPL.COMMON_SURNAMES
COMMON_SURNAME_WEIGHT = _IMPL.COMMON_SURNAME_WEIGHT
read_lines = _IMPL.read_lines
weighted_surnames = _IMPL.weighted_surnames
format_training_name = _IMPL.format_training_name
build_sampled_names = _IMPL.build_sampled_names


def main() -> None:
    _IMPL.main()


if __name__ == "__main__":
    main()
