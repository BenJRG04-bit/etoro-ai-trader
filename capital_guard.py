"""Offline capital-protection overlay for research simulations only.

Tracks a hypothetical account's equity peak. It cannot guarantee protection
against gaps, execution delays, or losses in real markets.
"""
from math import isfinite

class CapitalGuard:
    def __init__(self, starting_equity, *, max_drawdown=0.10,
                 profit_lock_trigger=0.05, profit_giveback=0.50):
        if not isfinite(starting_equity) or starting_equity <= 0:
            raise ValueError("Starting equity must be positive")
        if not (0 < max_drawdown <= 0.10):
            raise ValueError("Max drawdown must be within (0, 10%]")
        if not (0 < profit_lock_trigger < 1):
            raise ValueError("Invalid profit lock trigger")
        if not (0 < profit_giveback < 1):
            raise ValueError("Invalid profit giveback")
        self.initial = float(starting_equity)
        self.peak = float(starting_equity)
        self.max_drawdown = max_drawdown
        self.profit_lock_trigger = profit_lock_trigger
        self.profit_giveback = profit_giveback
        self.halted = False
        self.reason = None

    def observe(self, equity):
        if not isfinite(equity) or equity < 0:
            raise ValueError("Invalid equity")
        self.peak = max(self.peak, equity)
        if self.halted:
            return self.status()
        if equity <= self.peak * (1 - self.max_drawdown):
            self.halted, self.reason = True, "MAX_DRAWDOWN"
        elif self.peak >= self.initial * (1 + self.profit_lock_trigger):
            # Once gains exceed the trigger, stop if enough peak gains vanish.
            gains = self.peak - self.initial
            if equity <= self.peak - gains * self.profit_giveback:
                self.halted, self.reason = True, "PROFIT_GIVEBACK"
        return self.status()

    def status(self):
        return {"halted": self.halted, "reason": self.reason,
                "peak_equity": round(self.peak, 6),
                "research_only": True}
