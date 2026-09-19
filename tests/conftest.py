"""Pytest bootstrap for the PA momentum research project.

Three things are handled here, none of which mutate the host environment:

1. The project root is put on ``sys.path`` so that ``tests.*`` imports resolve
   identically regardless of the pytest import mode.
2. ``user_data/strategies/shared`` is put on ``sys.path`` so helper modules
   import exactly the way they do from inside a strategy file.
3. ``freqtrade`` is a research *dependency*, not a copy of this project. If it
   is not installed, a source checkout can be supplied through the
   ``FREQTRADE_SRC`` environment variable; otherwise the conventional sibling
   checkouts (``../freqtrade-develop`` and the nested
   ``../freqtrade-develop/freqtrade-develop``) are probed. If none works, tests
   that need freqtrade skip themselves instead of failing the whole session.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from tests.helpers import make_candles

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SHARED_DIR = PROJECT_ROOT / "user_data" / "strategies" / "shared"

for _path in (SHARED_DIR, PROJECT_ROOT):
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

requires_freqtrade = pytest.mark.skipif(
    not FREQTRADE_AVAILABLE,
    reason="freqtrade is not importable; set FREQTRADE_SRC to a source checkout",
)

__all__ = ["FREQTRADE_AVAILABLE", "PROJECT_ROOT", "SHARED_DIR", "requires_freqtrade"]


@pytest.fixture
def trending_breakout_candles() -> object:
    """
    A flat base followed by a sustained upward breakout.

    :return: OHLCV frame that must produce exactly one entry signal.
    """
    base = [100.0 + 0.01 * ((-1) ** i) for i in range(40)]
    rally = [100.0 + 2.0 * (i + 1) for i in range(20)]
    return make_candles(base + rally)


@pytest.fixture
def breakdown_candles() -> object:
    """
    A flat base followed by a sustained sell-off.

    :return: OHLCV frame that must produce exit signals after the decline.
    """
    base = [100.0 + 0.01 * ((-1) ** i) for i in range(40)]
    decline = [100.0 - 2.0 * (i + 1) for i in range(20)]
    return make_candles(base + decline)
