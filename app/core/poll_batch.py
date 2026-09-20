# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Plan contiguous Modbus read batches (PDF §13 — optimize consecutive registers)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.tag_database import TagRecord

MAX_REGISTERS_PER_REQUEST = 125


@dataclass(frozen=True)
class ReadBatch:
    device: str
    unit_id: int
    function: int
    start_internal: int
    register_count: int
    records: tuple[TagRecord, ...]


def plan_read_batches(records: list[TagRecord]) -> list[ReadBatch]:
    """Group tags by device + function + unit, merge contiguous address ranges."""
    if not records:
        return []
    sorted_recs = sorted(
        records,
        key=lambda r: (
            r.definition.device,
            int(r.definition.unit_id),
            int(r.definition.function),
            r.address_internal,
        ),
    )
    batches: list[ReadBatch] = []
    current: list[TagRecord] = []
    cur_key = None
    cur_end = -1

    def flush() -> None:
        nonlocal current, cur_key, cur_end
        if not current:
            return
        start = current[0].address_internal
        count = cur_end - start + 1
        batches.append(
            ReadBatch(
                device=current[0].definition.device,
                unit_id=int(current[0].definition.unit_id),
                function=int(current[0].definition.function),
                start_internal=start,
                register_count=count,
                records=tuple(current),
            )
        )
        current = []
        cur_end = -1

    for rec in sorted_recs:
        key = (
            rec.definition.device,
            int(rec.definition.unit_id),
            int(rec.definition.function),
        )
        start = rec.address_internal
        need = rec.definition.register_count
        end = start + need - 1
        if not current:
            current = [rec]
            cur_key = key
            cur_end = end
            continue
        if key != cur_key or start != cur_end + 1:
            flush()
            current = [rec]
            cur_key = key
            cur_end = end
            continue
        new_count = end - current[0].address_internal + 1
        if new_count > MAX_REGISTERS_PER_REQUEST:
            flush()
            current = [rec]
            cur_key = key
            cur_end = end
            continue
        current.append(rec)
        cur_end = end
    flush()
    return batches
