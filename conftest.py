"""Pytest bootstrap for the PA momentum research project.

Two problems are solved here, both without mutating the host environment:

1. ``freqtrade`` is a research *dependency*, not a copy of this project. If it
   is not installed, the path to a source checkout can be supplied through the
   ``FREQTRADE_SRC`` environment variable. When that variable is absent the
   conventional sibling checkouts (``../freqtrade-develop`` and the nested
   ``../freqtrade-develop/freqtrade-develop``) are probed. If none works, the
   tests that need freqtrade skip themselves instead of failing the whole
   session.
2. ``user_data/strategies/shared`` is put on ``sys.path`` so that helper
   modules import exactly the way they do from inside a strategy file.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SHARED_DIR = PROJECT_ROOT / "user_data" / "strategies" / "shared"

for _path in (SHARED_DIR,):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))


def _freqtrade_importable() -> bool:
    """
    Report whether ``freqtrade`` can be imported.

    :return: True when ``import freqtrade`` succeeds.
    """
    try:
        import freqtrade  # noqa: F401
    except ImportError:
        return False
    return True


def _ensure_freqtrade_importable() -> bool:
    """
    Best-effort attempt to make ``freqtrade`` importable.

    :return: True when ``freqtrade`` is importable afterwards.
    """
    if _freqtrade_importable():
        return True

    candidates: list[Path] = []
    env_path = os.environ.get("FREQTRADE_SRC")
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(
        [
            PROJECT_ROOT.parent / "freqtrade-develop",
            PROJECT_ROOT.parent / "freqtrade-develop" / "freqtrade-develop",
            PROJECT_ROOT.parent,
        ]
    )

    for candidate in candidates:
        if (candidate / "freqtrade" / "__init__.py").is_file():
            sys.path.insert(0, str(candidate))
            if _freqtrade_importable():
                return True
    return False


FREQTRADE_AVAILABLE = _ensure_freqtrade_importable()

__all__ = ["FREQTRADE_AVAILABLE", "PROJECT_ROOT", "SHARED_DIR"]
