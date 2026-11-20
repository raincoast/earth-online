"""Run with: python -m unittest discover -s backend/tests -v"""

import unittest

from app.agents import propose_mayor_policy
from app.simulation import CitySimulation


class CitySimulationTests(unittest.TestCase):
    def test_same_seed_reproduces_history(self):
        first = CitySimulation(seed=17, population=200)
        second = CitySimulation(seed=17, population=200)
        first.step(20)
        second.step(20)
        self.assertEqual(first.snapshot(), second.snapshot())

    def test_money_conservation_after_policy_change(self):
        world = CitySimulation(seed=8, population=300)
        total = world.total_cash_at_start
        world.set_tax_rate(0.25)
        world.step(30)
        self.assertEqual(world._total_cash(), total)
        self.assertEqual(sum(entry.amount_cents for entry in world.ledger), 0)

    def test_population_is_stable_in_starter(self):
        world = CitySimulation(seed=42, population=150)
        world.step(7)
        self.assertEqual(world.snapshot()["metrics"]["population"], 150)
        self.assertEqual(world.day, 7)
        self.assertTrue(all(0 <= h.satisfaction <= 100 for h in world.households))

    def test_bad_inputs_fail(self):
        with self.assertRaises(ValueError):
            CitySimulation(population=5)
        world = CitySimulation(population=100)
        with self.assertRaises(ValueError):
            world.set_tax_rate(0.75)
        with self.assertRaises(ValueError):
            world.step(0)

    def test_mayor_proposal_is_bounded(self):
        world = CitySimulation(population=100)
        proposal = propose_mayor_policy(world.snapshot())
        self.assertGreaterEqual(proposal.target_tax_rate, 0)
        self.assertLessEqual(proposal.target_tax_rate, 0.5)


if __name__ == "__main__":
    unittest.main()

