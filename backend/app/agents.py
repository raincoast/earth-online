"""Replaceable decision agent contract.

This is intentionally an offline heuristic, not an LLM. Integrate an LLM
adapter later, but keep the same validation boundary in the API.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TaxProposal:
    target_tax_rate: float
    rationale: str


def propose_mayor_policy(world: dict[str, Any]) -> TaxProposal:
    employment = float(world["metrics"]["employment_rate"])
    balance = float(world["metrics"]["government_balance"])
    current_rate = float(world["tax_rate"])

    if employment < 85:
        proposed = max(0.05, current_rate - 0.01)
        rationale = "Reduce income tax while employment is weak."
    elif balance < 300_000:
        proposed = min(0.35, current_rate + 0.01)
        rationale = "Protect the city budget while cash reserves are low."
    else:
        proposed = current_rate
        rationale = "Maintain the current policy under stable conditions."

    # This allowlist is where a future LLM-generated proposal must be checked.
    proposed = round(proposed, 4)
    if not 0 <= proposed <= 0.5:
        raise ValueError("agent proposal is outside the policy bounds")
    return TaxProposal(target_tax_rate=proposed, rationale=rationale)

