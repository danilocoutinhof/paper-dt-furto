from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class MockBillingMeter:
    records: pd.DataFrame
    _index: dict[tuple[pd.Timestamp, str], dict[str, Any]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        # A per-lookup boolean mask scan over the whole DataFrame made
        # `get_at` O(T) per call and therefore O(T^2) for a single
        # T-event twin simulation (identified while producing the
        # computational-complexity/scalability analysis requested during
        # peer review). Building a (timestamp, dev_eui) -> row dict once,
        # here, makes each lookup O(1) and the closed-loop runtime genuinely
        # O(T) per twin, matching the complexity analysis reported in the
        # manuscript.
        self._index = {
            (row["timestamp"], row["dev_eui"]): row.to_dict()
            for _, row in self.records.iterrows()
        }

    def get_at(self, timestamp: pd.Timestamp, dev_eui: str) -> dict[str, Any]:
        return self._index[(timestamp, dev_eui)]
