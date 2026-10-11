"""Float32 helpers: the original C++ stores edge/process reference times as
`float` and compares against `float` literals (1.3f, 1.1f). Reproducing the
thresholds in double precision shifts borderline comparisons, so we round
through 32-bit explicitly wherever the original did.
"""

from __future__ import annotations

import struct

_PACK = struct.Struct("f")


def f32(x: float) -> float:
    """Round a Python float to the nearest IEEE-754 binary32 value."""
    return _PACK.unpack(_PACK.pack(x))[0]


def qt_to_double(text: str) -> tuple[float, bool]:
    """Mirror QString::toDouble(&ok): returns (0.0, False) on failure."""
    try:
        return float(text), True
    except ValueError:
        return 0.0, False


def qt_to_int(text: str) -> int:
    """Mirror QString::toInt(): 0 on failure."""
    try:
        return int(text)
    except ValueError:
        try:
            # Qt's toInt() does not accept "3.0"; neither do we.
            return 0
        except ValueError:
            return 0


def qt_to_float(text: str) -> float:
    """Mirror QString::toFloat(): 0.0f on failure, binary32 precision."""
    try:
        return f32(float(text))
    except ValueError:
        return 0.0


def to_ulonglong(number: str) -> int:
    """Mirror BusinessProcessModel::convertToULongLong — truncate at '.'."""
    index = number.find(".")
    if index < 0:
        try:
            return int(number)
        except ValueError:
            return 0
    try:
        return int(number[:index])
    except ValueError:
        return 0
