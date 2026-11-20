"""HTTP smoke tests for the local single-world API."""

import unittest

from fastapi.testclient import TestClient

from app.main import app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        response = self.client.post("/api/reset", json={"seed": 11, "population": 150})
        self.assertEqual(response.status_code, 200)

    def test_get_step_and_policy(self):
        before = self.client.get("/api/world").json()
        self.assertEqual(before["day"], 0)
        stepped = self.client.post("/api/step", json={"days": 3})
        self.assertEqual(stepped.status_code, 200)
        self.assertEqual(stepped.json()["day"], 3)
        policy = self.client.post("/api/policy", json={"tax_rate": 0.2})
        self.assertEqual(policy.status_code, 200)
        self.assertEqual(policy.json()["tax_rate"], 0.2)

    def test_request_bounds(self):
        response = self.client.post("/api/step", json={"days": 1000})
        self.assertEqual(response.status_code, 422)
        response = self.client.post("/api/policy", json={"tax_rate": -1})
        self.assertEqual(response.status_code, 422)

    def test_heuristic_mayor_contract(self):
        response = self.client.post("/api/agent/mayor/decide", json={})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["agent_type"], "heuristic_stub")
        self.assertEqual(payload["proposal"]["target_tax_rate"], payload["world"]["tax_rate"])


if __name__ == "__main__":
    unittest.main()
