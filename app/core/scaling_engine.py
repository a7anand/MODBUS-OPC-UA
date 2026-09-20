# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Engineering scaling: eng = raw * gain + offset."""

from __future__ import annotations

from app.core.config_schema import TagDefinition


def scale_to_engineering(raw: float, tag: TagDefinition) -> float:
    value = raw * tag.gain + tag.offset
    if tag.clamp:
        if tag.minimum is not None:
            value = max(value, tag.minimum)
        if tag.maximum is not None:
            value = min(value, tag.maximum)
    return value


def scale_to_raw(engineering: float, tag: TagDefinition) -> float:
    if tag.gain == 0:
        return engineering - tag.offset
    return (engineering - tag.offset) / tag.gain
