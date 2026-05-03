# core/config.py
from functools import lru_cache
from pathlib import Path
from typing import Any

import tomllib


@lru_cache(maxsize=1)
def load_config(path_str: str = "config.toml") -> dict[str, Any]:
    with open(Path(path_str).expanduser(), "rb") as f:
        return tomllib.load(f)
