"""Deterministic, in-memory city simulation for the Earth Online MVP.

All currency is stored as integer cents. The simulation is illustrative: its
parameters are invented, not calibrated to a real city or economy.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Any


DISTRICT_NAMES = (
    "Old Town", "Harbor", "North Park", "University", "Market Square",
    "Riverside", "West End", "Industrial", "South Hills", "Greenfield",
)


@dataclass(slots=True)
class District:
    id: int
    name: str
    rent_cents: int
    amenities: float


@dataclass(slots=True)
class Household:
    id: int
    district_id: int
    employer_id: int | None
    cash_cents: int
    satisfaction: float = 65.0
    last_wage_cents: int = 0
    missed_rent: bool = False


@dataclass(slots=True)
class Firm:
    id: int
    district_id: int
    cash_cents: int
    price_cents: int
    inventory: int = 0


@dataclass(slots=True)
class Government:
    cash_cents: int


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    transaction_id: int
    account: str
    amount_cents: int
    reason: str


class CitySimulation:
    """A reproducible micro-economy with testable accounting invariants."""

    def __init__(self, seed: int = 42, population: int = 1000) -> None:
        if not 100 <= population <= 5000:
            raise ValueError("population must be between 100 and 5000")
        self.seed = seed
        self.random = Random(seed)
        self.day = 0
        self.tax_rate = 0.12
        self.government = Government(cash_cents=100_000_000)
        self.districts = [
            District(i, name, 350 + i * 35, round(0.50 + (i % 4) * 0.12, 2))
            for i, name in enumerate(DISTRICT_NAMES)
        ]
        self.firms = [
            Firm(i, i % len(self.districts), 50_000_000, 750 + (i % 5) * 40)
            for i in range(20)
        ]
        self.households = [
            Household(
                id=i,
                district_id=self.random.randrange(len(self.districts)),
                employer_id=self.random.randrange(len(self.firms))
                if self.random.random() < 0.82 else None,
                cash_cents=self.random.randint(80_000, 250_000),
            )
            for i in range(population)
        ]
        self.ledger: list[LedgerEntry] = []
        self._transaction_counter = 0
        self.last_transactions = 0
        self.total_cash_at_start = self._total_cash()
        self.history: list[dict[str, float | int]] = [self._metrics()]

    def _total_cash(self) -> int:
        return (
            self.government.cash_cents
            + sum(h.cash_cents for h in self.households)
            + sum(f.cash_cents for f in self.firms)
        )

    def _transfer(
        self,
        source: Household | Firm | Government,
        destination: Household | Firm | Government,
        source_name: str,
        destination_name: str,
        amount_cents: int,
        reason: str,
    ) -> bool:
        """Apply a pair of ledger entries or reject the transfer atomically."""
        if amount_cents < 0:
            raise ValueError("negative transfer")
        if amount_cents == 0:
            return True
        if source.cash_cents < amount_cents:
            return False
        source.cash_cents -= amount_cents
        destination.cash_cents += amount_cents
        self._transaction_counter += 1
        tx = self._transaction_counter
        self.ledger.append(LedgerEntry(tx, source_name, -amount_cents, reason))
        self.ledger.append(LedgerEntry(tx, destination_name, amount_cents, reason))
        return True

    def set_tax_rate(self, tax_rate: float) -> None:
        if not 0 <= tax_rate <= 0.5:
            raise ValueError("tax rate must be between 0 and 0.5")
        self.tax_rate = round(tax_rate, 4)

    def step(self, days: int = 1) -> dict[str, Any]:
        if not 1 <= days <= 90:
            raise ValueError("days must be between 1 and 90")
        for _ in range(days):
            self._step_one_day()
        return self.snapshot()

    def _step_one_day(self) -> None:
        self.ledger.clear()
        self.day += 1

        # A simple social feedback mechanism: each neighborhood's previous
        # mood influences residents on the next day. More detailed networks
        # can replace this aggregated signal in a later version.
        district_mood = {}
        for district in self.districts:
            residents = [h for h in self.households if h.district_id == district.id]
            district_mood[district.id] = (
                sum(h.satisfaction for h in residents) / len(residents)
                if residents else 60.0
            )

        # Production: the simplified model has no intermediate inputs yet.
        workforce = [0] * len(self.firms)
        for household in self.households:
            if household.employer_id is not None:
                workforce[household.employer_id] += 1
        for firm in self.firms:
            firm.inventory = min(5000, firm.inventory + 3 * workforce[firm.id] + 5)

        # Employment, wages and income tax.
        for household in self.households:
            household.last_wage_cents = 0
            if household.employer_id is None:
                continue
            firm = self.firms[household.employer_id]
            wage = 2800 + (household.id % 6) * 100
            if self._transfer(
                firm, household, f"firm:{firm.id}", f"household:{household.id}",
                wage, "wage",
            ):
                household.last_wage_cents = wage
                tax = round(wage * self.tax_rate)
                self._transfer(
                    household, self.government, f"household:{household.id}",
                    "government", tax, "income_tax",
                )
            else:
                household.employer_id = None

        # Unemployment benefit: government transfers are also part of ledger.
        for household in self.households:
            if household.employer_id is None:
                self._transfer(
                    self.government, household, "government",
                    f"household:{household.id}", 750, "unemployment_benefit",
                )

        # Goods market: each household attempts to buy 1 or 2 units per day.
        for household in self.households:
            local_firms = [
                firm for firm in self.firms
                if firm.district_id == household.district_id and firm.inventory > 0
            ]
            candidates = local_firms or [f for f in self.firms if f.inventory > 0]
            if candidates:
                merchant = candidates[self.random.randrange(len(candidates))]
                units = 1 + int(self.random.random() < 0.65)
                units = min(units, merchant.inventory)
                price = units * merchant.price_cents
                if self._transfer(
                    household, merchant, f"household:{household.id}",
                    f"firm:{merchant.id}", price, "goods_purchase",
                ):
                    merchant.inventory -= units

        # Housing market: the municipality owns the starter housing stock.
        for household in self.households:
            rent = self.districts[household.district_id].rent_cents
            household.missed_rent = not self._transfer(
                household, self.government, f"household:{household.id}",
                "government", rent, "rent",
            )
            district = self.districts[household.district_id]
            employed = household.employer_id is not None
            savings_buffer = household.cash_cents >= 30 * district.rent_cents
            target = (
                25 + 30 * int(employed) + 15 * district.amenities
                + 14 * int(savings_buffer) - 15 * int(household.missed_rent)
                + 0.2 * (district_mood[district.id] - 60)
            )
            household.satisfaction = round(
                max(0, min(100, 0.85 * household.satisfaction + 0.15 * target)), 2
            )

        # Every payment must conserve the total money supply.
        assert sum(entry.amount_cents for entry in self.ledger) == 0
        assert self._total_cash() == self.total_cash_at_start
        assert all(h.cash_cents >= 0 for h in self.households)
        assert all(f.cash_cents >= 0 for f in self.firms)
        self.last_transactions = len(self.ledger) // 2
        self.history.append(self._metrics())

    def _metrics(self) -> dict[str, float | int]:
        employed = sum(h.employer_id is not None for h in self.households)
        population = len(self.households)
        return {
            "day": self.day,
            "population": population,
            "employment_rate": round(employed / population * 100, 1),
            "average_satisfaction": round(
                sum(h.satisfaction for h in self.households) / population, 1
            ),
            "government_balance": round(self.government.cash_cents / 100, 2),
            "household_savings": round(sum(h.cash_cents for h in self.households) / 100, 2),
            "firm_balance": round(sum(f.cash_cents for f in self.firms) / 100, 2),
            "transactions": self.last_transactions,
        }

    def snapshot(self) -> dict[str, Any]:
        district_metrics = []
        for district in self.districts:
            residents = [h for h in self.households if h.district_id == district.id]
            employed = sum(h.employer_id is not None for h in residents)
            district_metrics.append({
                "id": district.id,
                "name": district.name,
                "population": len(residents),
                "employment_rate": round(100 * employed / len(residents), 1)
                if residents else 0,
                "satisfaction": round(
                    sum(h.satisfaction for h in residents) / len(residents), 1
                ) if residents else 0,
                "daily_rent": round(district.rent_cents / 100, 2),
            })
        return {
            "seed": self.seed,
            "day": self.day,
            "tax_rate": self.tax_rate,
            "metrics": self._metrics(),
            "districts": district_metrics,
            "history": self.history[-180:],
            "total_money": round(self.total_cash_at_start / 100, 2),
        }

