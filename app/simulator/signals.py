# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Simulator signal modes (PDF §30)."""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from enum import Enum


class SignalMode(str, Enum):
    MANUAL = "manual"
    RANDOM = "random"
    RAMP = "ramp"
    SINE = "sine"
    TOGGLE = "toggle"
    COUNTER = "counter"


# PDF §30 demo register map (holding register offsets per unit)
DEMO_SIGNALS: dict[str, tuple[int, SignalMode]] = {
    "PUMP1_RUNNING": (0, SignalMode.TOGGLE),
    "PUMP2_RUNNING": (1, SignalMode.TOGGLE),
    "PUMP1_SPEED": (10, SignalMode.RAMP),
    "PUMP2_SPEED": (11, SignalMode.RAMP),
    "FLOW": (20, SignalMode.SINE),
    "PRESSURE": (21, SignalMode.SINE),
    "TEMPERATURE": (22, SignalMode.SINE),
}


@dataclass
class SignalState:
    mode: SignalMode = SignalMode.SINE
    manual_value: int = 0
    counter: int = 0
    toggle: bool = False
    ramp_start: float = field(default_factory=time.time)


class SignalEngine:
    def __init__(self) -> None:
        self._states: dict[str, SignalState] = {
            name: SignalState(mode=mode) for name, (_addr, mode) in DEMO_SIGNALS.items()
        }
        self._t0 = time.time()

    def set_mode(self, name: str, mode: SignalMode, manual: int = 0) -> None:
        st = self._states.setdefault(name, SignalState())
        st.mode = mode
        st.manual_value = manual
        if mode == SignalMode.RAMP:
            st.ramp_start = time.time()

    def sample(self, name: str) -> int:
        st = self._states.get(name) or SignalState()
        t = time.time() - self._t0
        mode = st.mode
        if mode == SignalMode.MANUAL:
            return st.manual_value & 0xFFFF
        if mode == SignalMode.RANDOM:
            return random.randint(0, 10000)
        if mode == SignalMode.COUNTER:
            st.counter += 1
            return st.counter & 0xFFFF
        if mode == SignalMode.TOGGLE:
            st.toggle = (int(t) % 4) < 2
            return 1 if st.toggle else 0
        if mode == SignalMode.RAMP:
            elapsed = time.time() - st.ramp_start
            return int((elapsed * 50) % 10000) & 0xFFFF
        # SINE default
        phase = DEMO_SIGNALS.get(name, (0, SignalMode.SINE))[0]
        val = 5000 + 4000 * math.sin(t / 3 + phase / 10)
        return int(val) & 0xFFFF

    def apply_to_memory(self, memory, unit_id: int = 1) -> None:
        from app.core.enums import RegisterArea

        for name, (addr, _mode) in DEMO_SIGNALS.items():
            memory.write(unit_id, RegisterArea.HOLDING_REGISTER, addr, [self.sample(name)])

    def status(self) -> list[dict]:
        return [
            {
                "name": name,
                "address": addr,
                "mode": self._states.get(name, SignalState()).mode.value,
                "value": self.sample(name),
            }
            for name, (addr, _) in DEMO_SIGNALS.items()
        ]
