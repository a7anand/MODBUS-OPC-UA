from app.core.config_schema import GatewayDocument, TagDefinition
from app.core.enums import DataType, ModbusFunction, TagQuality
from app.core.mapping_engine import MappingEngine
from app.core.tag_database import TagDatabase


def test_should_publish_allows_repeated_modbus_polls():
    doc = GatewayDocument.model_validate(
        {
            "gateway": {"name": "t"},
            "modbus": {
                "devices": [{"name": "D", "mode": "simulator", "enabled": True}],
            },
            "tags": [
                {
                    "name": "x",
                    "device": "D",
                    "function": 3,
                    "address": 40001,
                    "datatype": "uint16",
                    "deadband": 0,
                }
            ],
        }
    )
    tags = TagDatabase()
    tags.build_from_config(doc)
    tags.update_value("x", 1, TagQuality.GOOD, origin="modbus_poll")
    engine = MappingEngine(doc, tags)
    assert engine.should_publish("x", 2, "modbus_poll") is True
