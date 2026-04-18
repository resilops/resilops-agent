import asyncio
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Response, status
from server.constants import (
    M2M_TOKEN_RESPONSE,
    ResiliencyScenario,
    ResiliencyScenarioStatusEnum,
)

app = FastAPI(title="Control Plane API")
claim_lock = asyncio.Lock()

queued_scenario: Optional[ResiliencyScenario] = None


# -------------------------------------------------------------------
# Health
# -------------------------------------------------------------------


@app.get("/api/health/live")
async def health_live():
    """Health live endpoint"""
    return {"status": "ok"}


@app.get("/api/health/ready")
async def health_ready():
    """Health ready endpoint"""
    return {"status": "ok"}


# -------------------------------------------------------------------
# Auth service APIs
# -------------------------------------------------------------------


@app.post("/api/v1/m2m/token")
async def m2m_token(request: Request):
    return M2M_TOKEN_RESPONSE


# -------------------------------------------------------------------
# Agent APIs
# -------------------------------------------------------------------


@app.post("/api/v1/agent/heartbeat")
async def agent_heartbeat(request: Request):
    """Simulate heartbeat endpoint."""
    payload = await request.json()
    print(payload)
    return {"health": payload.get("health")}


@app.post("/api/v1/agent/snapshots/cluster")
async def cluster_snapshot(request: Request):
    payload = await request.json()
    print(payload)
    return {"status": "ok"}


# -------------------------------------------------------------------
# Queue and claims APIs
# -------------------------------------------------------------------


@app.post("/api/v1/scenario-queue/items", status_code=status.HTTP_201_CREATED)
async def queue_scenario(scenario: ResiliencyScenario):
    global queued_scenario
    scenario.state = ResiliencyScenarioStatusEnum.PENDING
    queued_scenario = scenario
    return {"status": "queued"}


@app.get("/api/v1/agent/scenario-queue/claims")
async def scenario_claims(request: Request):
    """Fetch a queued resiliency test suite."""
    if (
        queued_scenario is None
        or queued_scenario.state != ResiliencyScenarioStatusEnum.PENDING
    ):
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return [
        {
            "id": "053fd5b8-5d2f-4d08-9c96-7b2758742fde",
            "run_id": 1,
            "scenario_id": 1,
            "status": "pending",
        }
    ]


@app.post("/api/v1/agent/scenario-claims/{claim_id}/ack")
async def agent_acknowledge_claim(claim_id: int):
    """Acknowledge and mark claim as processed."""

    async with claim_lock:
        if queued_scenario is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No scenario queued",
            )
        if queued_scenario.state == ResiliencyScenarioStatusEnum.ACKNOWLEDGED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Some other agent already picked this up",
            )
        queued_scenario.state = ResiliencyScenarioStatusEnum.ACKNOWLEDGED

    return {
        "id": "053fd5b8-5d2f-4d08-9c96-7b2758742fde",
        "scenario_id": 1,
        "status": ResiliencyScenarioStatusEnum.ACKNOWLEDGED.value,
    }


# -------------------------------------------------------------------
# Scenario
# -------------------------------------------------------------------


@app.get("/api/v1/agent/scenarios/{scenario_id}/runs/{run_id}")
async def agent_fetch_scenario_run(scenario_id: int, run_id: int):
    """Fetch a resiliency scenario from a suite."""
    return {"id": run_id, "scenario_id": scenario_id, "config": queued_scenario}


# -------------------------------------------------------------------
# Ingest Events
# -------------------------------------------------------------------


@app.post("/api/v1/agent/events", status_code=status.HTTP_201_CREATED)
async def ingest_events(request: Request):
    payload = await request.json()
    print(payload)
    return {"status": "events_queued", "count": len(payload)}


# -------------------------------------------------------------------
# Ingest Events
# -------------------------------------------------------------------


@app.post("/api/v1/agent/metrics", status_code=status.HTTP_201_CREATED)
async def ingest_metrics(request: Request):
    payload = await request.json()
    print(payload)
    return {"status": "metrics_queued", "count": len(payload)}
