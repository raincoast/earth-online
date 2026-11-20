"""FastAPI interface for the Earth Online starter simulation.

The simulation lives only in memory. Run one API worker until persistence and
per-session state have been implemented.
"""

from threading import RLock
from fastapi import FastAPI
from pydantic import BaseModel, Field

from .agents import propose_mayor_policy
from .simulation import CitySimulation


app = FastAPI(title="Earth Online API", version="0.1.0")
_lock = RLock()
_world = CitySimulation()


class StepRequest(BaseModel):
    days: int = Field(default=1, ge=1, le=90)


class ResetRequest(BaseModel):
    seed: int = Field(default=42, ge=0, le=2_147_483_647)
    population: int = Field(default=1000, ge=100, le=5000)


class PolicyRequest(BaseModel):
    tax_rate: float = Field(ge=0, le=0.5)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/world")
def get_world() -> dict:
    with _lock:
        return _world.snapshot()


@app.post("/api/step")
def step_world(request: StepRequest) -> dict:
    with _lock:
        return _world.step(request.days)


@app.post("/api/reset")
def reset_world(request: ResetRequest) -> dict:
    global _world
    with _lock:
        _world = CitySimulation(seed=request.seed, population=request.population)
        return _world.snapshot()


@app.post("/api/policy")
def change_policy(request: PolicyRequest) -> dict:
    with _lock:
        _world.set_tax_rate(request.tax_rate)
        return _world.snapshot()


@app.post("/api/agent/mayor/decide")
def mayor_decides() -> dict:
    with _lock:
        proposal = propose_mayor_policy(_world.snapshot())
        _world.set_tax_rate(proposal.target_tax_rate)
        return {
            "agent_type": "heuristic_stub",
            "proposal": {
                "target_tax_rate": proposal.target_tax_rate,
                "rationale": proposal.rationale,
            },
            "world": _world.snapshot(),
        }

