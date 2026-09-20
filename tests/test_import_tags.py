# Copyright (c) 2026 Aman Anand, M (T&I), Barauni

from app.core.config_schema import GatewayDocument, ModbusDeviceConfig
from app.core.config_editor import add_device, merge_imported_tags
from app.core.enums import ModbusDeviceMode
from app.core.import_export import import_tags_csv, row_to_tag_definition, rows_to_tag_definitions


def test_csv_row_to_tag():
    row = {
        "TagName": "T1",
        "Device": "SIM_PLC",
        "Function": "3",
        "Address": "40001",
        "Datatype": "int16",
        "Gain": "0.01",
    }
    tag = row_to_tag_definition(row)
    assert tag.name == "T1"
    assert tag.gain == 0.01


def test_merge_import():
    doc = GatewayDocument.model_validate(
        {
            "gateway": {"name": "G"},
            "modbus": {
                "devices": [{"name": "D", "mode": "simulator"}],
            },
            "tags": [],
        }
    )
    rows = import_tags_csv(
        "TagName,Device,Function,Address,Datatype\nX,D,3,40001,uint16\n"
    )
    tags, errs = rows_to_tag_definitions(rows)
    assert not errs
    doc, stats = merge_imported_tags(doc, tags)
    assert stats["added"] == 1
    assert len(doc.tags) == 1
