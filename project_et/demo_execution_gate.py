"""Project E.T. autonomous DEMO order gate.

This module deliberately does not guess eToro API endpoints or authentication.
Supply a verified demo-only broker adapter after connection testing.
No live-account execution is supported.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol
import os


@dataclass(frozen=True)
class OrderIntent:
    instrument_id: int
    side: str
    amount: Decimal
    decision_id: str


class DemoBroker(Protocol):
    def verify_demo_account(self) -> bool: ...
    def submit_demo_order(self, order: OrderIntent) -> dict: ...


class ExecutionBlocked(RuntimeError):
    pass


class DemoExecutionGate:
    def __init__(self, broker: DemoBroker, max_order: Decimal = Decimal("10")):
        self.broker = broker
        self.max_order = max_order
        self._submitted = set()

    def execute(self, order: OrderIntent) -> dict:
        if not order.decision_id or order.decision_id in self._submitted:
            raise ExecutionBlocked("Missing or duplicate decision ID")
        if order.side not in ("BUY", "SELL"):
            raise ExecutionBlocked("Invalid order side")
        if not isinstance(order.instrument_id, int) or order.instrument_id <= 0:
            raise ExecutionBlocked("Invalid instrument ID")
        if not order.amount.is_finite() or not (Decimal("0") < order.amount <= self.max_order):
            raise ExecutionBlocked("Order amount exceeds demo risk limit")
        if os.getenv("PROJECT_ET_KILL_SWITCH", "ON") != "OFF":
            raise ExecutionBlocked("Kill switch active")
        if os.getenv("PROJECT_ET_DEMO_EXECUTION", "OFF") != "ON":
            return {"status": "SIMULATED", "decision_id": order.decision_id}
        if not self.broker.verify_demo_account():
            raise ExecutionBlocked("Demo account verification failed")
        # This local duplicate guard is insufficient across separate scheduled
        # processes: production integration must use durable idempotency.
        result = self.broker.submit_demo_order(order)
        self._submitted.add(order.decision_id)
        return result
