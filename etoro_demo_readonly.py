"""Fail-closed eToro Demo integration foundation.

No network calls, credentials, brokerage endpoints, or order execution.
An official documented read-only adapter must be implemented and verified
separately before any account data can be fetched.
"""
from dataclasses import dataclass
from typing import Mapping
import os

class DemoSafetyError(RuntimeError):
    pass

@dataclass(frozen=True)
class DemoConfig:
    environment: str = "demo"
    read_only: bool = True
    orders_enabled: bool = False

    def validate(self) -> None:
        if self.environment.lower() != "demo":
            raise DemoSafetyError("Only the demo environment is permitted")
        if not self.read_only or self.orders_enabled:
            raise DemoSafetyError("Read-only mode is mandatory")

class DemoReadOnlyGateway:
    def __init__(self, config: DemoConfig = DemoConfig()):
        config.validate()
        self.config = config

    def connection_status(self) -> Mapping[str, object]:
        return {
            "environment": "demo",
            "read_only": True,
            "orders_enabled": False,
            "connected": False,
            "reason": "Official read-only endpoint and authentication not yet verified",
        }

    def get_account_summary(self):
        raise DemoSafetyError(
            "Account reads disabled until official Demo API endpoint and authentication are verified"
        )

    def place_order(self, *args, **kwargs):
        raise DemoSafetyError("Order execution is permanently disabled in this adapter")

    def close_position(self, *args, **kwargs):
        raise DemoSafetyError("Order execution is permanently disabled in this adapter")

def validate_secret_configuration() -> bool:
    """Check presence only; never return, log or transmit a secret."""
    return bool(os.environ.get("ETORO_DEMO_API_KEY"))

if __name__ == "__main__":
    print(DemoReadOnlyGateway().connection_status())
