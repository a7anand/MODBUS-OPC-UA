# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Signal modes for built-in simulators."""

from __future__ import annotations

import math
import random
import time
from enum import Enum


class SignalMode(str, Enum):
    MANUAL = "manual"
    RANDOM = "random"
    RAMP = "ramp"
    SINE = "sine"
    TOGGLE = "toggle"
    COUNTER = "counter"


class SignalGenerator:
    def __init__(self, mode: SignalMode = SignalMode.SINE) -> None:
        self.mode = mode
        self._counter = 0
        self._toggle = False
        self.manual_value = 0.0

    def next(self) -> float:
        t = time.time()
        if self.mode == SignalMode.MANUAL:
            return self.manual_value
        if self.mode == SignalMode.RANDOM:
            return random.uniform(0, 100)
        if self.mode == SignalMode.RAMP:
            return (t % 100)
        if self.mode == SignalMode.SINE:
            return 50 + 40 * math.sin(t / 3)
        if self.mode == SignalMode.TOGGLE:
            self._toggle = not self._toggle
            return 1.0 if self._toggle else 0.0
        self._counter += 1
        return float(self._counter)
