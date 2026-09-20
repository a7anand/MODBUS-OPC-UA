# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from app.core.config_schema import TagDefinition
from app.core.poll_batch import plan_read_batches
from app.core.tag_database import TagRecord


def _rec(name: str, device: str, fn: int, addr: int, count: int = 1) -> TagRecord:
    d = TagDefinition(
        name=name,
        device=device,
        function=fn,
        address=40001 + addr,
        register_count=count,
        datatype="uint16",
    )
    r = TagRecord(definition=d, address_internal=addr, address_display=40001 + addr)
    return r


def test_plan_merges_contiguous_holding_registers():
    records = [_rec("a", "D", 3, 0), _rec("b", "D", 3, 1), _rec("c", "D", 3, 5)]
    batches = plan_read_batches(records)
    assert len(batches) == 2
    assert batches[0].register_count == 2
    assert len(batches[0].records) == 2
    assert batches[1].register_count == 1
