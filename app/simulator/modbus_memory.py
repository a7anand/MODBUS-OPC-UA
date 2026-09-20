# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Shared in-memory Modbus datastore for simulator and TCP/RTU server."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

from app.core.enums import RegisterArea


@dataclass
class ModbusMemory:
    coils: dict[tuple[int, int], bool] = field(default_factory=dict)
    discrete: dict[tuple[int, int], bool] = field(default_factory=dict)
    holding: dict[tuple[int, int], int] = field(default_factory=dict)
    input_regs: dict[tuple[int, int], int] = field(default_factory=dict)

    def seed_demo(self) -> None:
        for uid in (1, 2):
            self.holding[(uid, 0)] = 2500
            self.holding[(uid, 1)] = 1013
            self.input_regs[(uid, 0)] = 4096
            self.coils[(uid, 0)] = True

    def read(self, unit_id: int, area: RegisterArea, address: int, count: int) -> list[int]:
        t = time.time()
        values: list[int] = []
        for i in range(count):
            addr = address + i
            if area == RegisterArea.COIL:
                values.append(1 if self.coils.get((unit_id, addr), False) else 0)
            elif area == RegisterArea.DISCRETE_INPUT:
                values.append(1 if self.discrete.get((unit_id, addr), False) else 0)
            elif area == RegisterArea.HOLDING_REGISTER:
                base = self.holding.get((unit_id, addr))
                if base is None and i == 0:
                    base = int(2000 + 500 * math.sin(t / 5 + unit_id))
                values.append(base if base is not None else 0)
            else:
                values.append(self.input_regs.get((unit_id, addr), 1000 + i))
        return values

    def write(self, unit_id: int, area: RegisterArea, address: int, values: list[int]) -> None:
        for i, v in enumerate(values):
            addr = address + i
            if area == RegisterArea.COIL:
                self.coils[(unit_id, addr)] = bool(v)
            elif area == RegisterArea.HOLDING_REGISTER:
                self.holding[(unit_id, addr)] = v & 0xFFFF
