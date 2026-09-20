# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from app.core.enums import MappingDirection
from app.core.mapping_feedback import find_feedback_cycles


class _Map:
    def __init__(self, tag_name: str, direction: MappingDirection, enabled: bool = True):
        self.tag_name = tag_name
        self.direction = direction
        self.enabled = enabled


class _Doc:
    mappings = [
        _Map("t1", MappingDirection.MB_TO_UA),
        _Map("t1", MappingDirection.UA_TO_MB),
    ]


def test_feedback_warning_on_conflicting_directions():
    assert find_feedback_cycles(_Doc())  # type: ignore[arg-type]
