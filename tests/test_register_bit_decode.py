# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from __future__ import annotations

from app.core.config_schema import TagDefinition
from app.core.enums import DataType, ModbusFunction
from app.core.register_bit_decode import (
    decode_bit,
    holding_plc_address,
    parse_four_x_address,
    preview_register_bits,
    set_bit,
)
from app.modbus.register_codec import decode_registers, encode_registers


def test_four_x_address_parsing():
    assert parse_four_x_address("4X:11.3") == (40012, 3)
    assert parse_four_x_address("4X:11") == (40012, None)
    assert holding_plc_address(11) == 40012


def test_decode_bit_from_word():
    # bit 3 set in register
    word = 0b1000
    assert decode_bit(word, 3) is True
    assert decode_bit(word, 0) is False


def test_bool_tag_bit_index_decode():
    tag = TagDefinition(
        name="DI_3",
        device="PLC",
        function=ModbusFunction.READ_HOLDING,
        address=40012,
        datatype=DataType.BOOL,
        bit_index=3,
    )
    assert decode_registers([0b1000], tag) is True
    assert decode_registers([0], tag) is False


def test_set_bit_roundtrip():
    w = set_bit(0b1010, 1, True)
    assert decode_bit(w, 1) is True


def test_preview_sixteen_bits():
    bits = preview_register_bits(0xFFFF)
    assert len(bits) == 16
    assert all(b["value"] for b in bits)
