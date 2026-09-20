# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Shared enumerations for configuration and runtime."""

from __future__ import annotations

from enum import Enum


class AddressBase(str, Enum):
    ZERO = "zero"
    ONE = "one"


class ModbusDeviceMode(str, Enum):
    TCP_CLIENT = "tcp_client"
    TCP_SERVER = "tcp_server"
    RTU_CLIENT = "rtu_client"
    RTU_SERVER = "rtu_server"
    SIMULATOR = "simulator"


class RegisterArea(str, Enum):
    COIL = "coil"
    DISCRETE_INPUT = "discrete_input"
    HOLDING_REGISTER = "holding_register"
    INPUT_REGISTER = "input_register"


class ModbusFunction(int, Enum):
    READ_COILS = 1
    READ_DISCRETE = 2
    READ_HOLDING = 3
    READ_INPUT = 4
    WRITE_COIL = 5
    WRITE_REGISTER = 6
    WRITE_COILS = 15
    WRITE_REGISTERS = 16


class DataType(str, Enum):
    BOOL = "bool"
    INT16 = "int16"
    UINT16 = "uint16"
    INT32 = "int32"
    UINT32 = "uint32"
    INT64 = "int64"
    UINT64 = "uint64"
    FLOAT32 = "float32"
    FLOAT64 = "float64"
    STRING = "string"


class ByteLayout(str, Enum):
    """32-bit float/word layouts (ABCD = big-endian)."""

    ABCD = "ABCD"
    BADC = "BADC"
    CDAB = "CDAB"
    DCBA = "DCBA"


class WordOrder(str, Enum):
    BIG = "big"
    LITTLE = "little"


class MappingDirection(str, Enum):
    MB_TO_UA = "mb_to_ua"
    UA_TO_MB = "ua_to_mb"
    BIDIRECTIONAL = "bidirectional"


class TagQuality(str, Enum):
    GOOD = "GOOD"
    BAD = "BAD"
    UNCERTAIN = "UNCERTAIN"
    STALE = "STALE"
    COMMUNICATION_FAILURE = "COMMUNICATION_FAILURE"


class OpcUaSecurityMode(str, Enum):
    NONE = "none"
    SIGN = "sign"
    SIGN_AND_ENCRYPT = "sign_and_encrypt"


class UserRole(str, Enum):
    ADMINISTRATOR = "Administrator"
    ENGINEER = "Engineer"
    OPERATOR = "Operator"
    VIEWER = "Viewer"
