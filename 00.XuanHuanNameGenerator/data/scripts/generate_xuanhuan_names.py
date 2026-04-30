from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
_IMPL_PATH = DATA_DIR / "script_gen" / "scripts" / "generate_xuanhuan_names.py"

_SPEC = importlib.util.spec_from_file_location("_script_gen_generate_xuanhuan_names", _IMPL_PATH)
_IMPL = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_IMPL)

FIRST_NAMES = _IMPL.FIRST_NAMES
SINGLE_GIVEN_CHARS = _IMPL.SINGLE_GIVEN_CHARS
REAL_GIVEN_NAMES = _IMPL.REAL_GIVEN_NAMES
XIANXIA_GIVEN_NAMES = _IMPL.XIANXIA_GIVEN_NAMES
SPECIAL_NAMES = _IMPL.SPECIAL_NAMES
unique = _IMPL.unique
build_second_names = _IMPL.build_second_names


def main() -> None:
    _IMPL.main()


if __name__ == "__main__":
    main()
