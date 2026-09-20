# Copyright (c) 2026 Aman Anand, M (T&I), Barauni

from app.core.config_schema import TagDefinition
from app.core.enums import ByteLayout, DataType, ModbusFunction
from app.modbus.register_codec import decode_registers, diagnostic_interpretations, encode_registers


def test_int16_scale():
    tag = TagDefinition(
        name="t",
        device="d",
        function=ModbusFunction.READ_HOLDING,
        address=40001,
        datatype=DataType.INT16,
        gain=0.01,
        offset=0,
    )
    assert decode_registers([2500], tag) == 25.0


def test_bool_decode():
    tag = TagDefinition(
        name="b",
        device="d",
        function=ModbusFunction.READ_COILS,
        address=1,
        datatype=DataType.BOOL,
    )
    assert decode_registers([1], tag) is True


def test_roundtrip_uint16():
    tag = TagDefinition(
        name="u",
        device="d",
        function=ModbusFunction.READ_HOLDING,
        address=40010,
        datatype=DataType.UINT16,
    )
    regs = encode_registers(42, tag)
    assert decode_registers(regs, tag) == 42


def test_diagnostic_interpretations():
    interp = diagnostic_interpretations([0x4049, 0x0FDB])
    assert "float32" in interp
