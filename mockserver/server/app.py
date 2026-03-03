from typing import Optional

from fastapi import FastAPI, HTTPException, Request, status
from server.constants import AGENT_CONFIG, ResiliencySuite, ResiliencySuiteStatusEnum

app = FastAPI(title="Control Plane API")

current_suite: Optional[ResiliencySuite] = None


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
# Agent APIs
# -------------------------------------------------------------------


@app.get("/api/v1/agent/heartbeat")
async def agent_heartbeat():
    """Simulate heartbeat endpoint."""
    return {"status": "ok"}


@app.get("/api/v1/agent/config")
async def agent_config():
    """Simulate agent config endpoint."""
    return AGENT_CONFIG


@app.get("/api/v1/agent/suite")
async def agent_fetch_suite():
    """Fetch a queued resiliency test suite."""
    if current_suite is None or current_suite.state != ResiliencySuiteStatusEnum.QUEUED:
        return {}

    return current_suite.suite


@app.post("/api/v1/agent/suite/ack")
async def agent_acknowledge_suite():
    """Acknowledge and mark suite as processed."""
    if current_suite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No suite queued",
        )

    current_suite.state = ResiliencySuiteStatusEnum.PROCESSED
    return {"status": "ok"}


@app.get("/api/v1/agent/suite/{suite_id}/scenario/{scenario_id}")
async def agent_fetch_scenario(suite_id: int, scenario_id: int):
    """Fetch a resiliency scenario from a suite."""
    if current_suite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active suite",
        )
    return current_suite.scenarios[0]


# -------------------------------------------------------------------
# Queue APIs
# -------------------------------------------------------------------


@app.post("/api/v1/queue/suite", status_code=status.HTTP_201_CREATED)
async def queue_suite(suite: ResiliencySuite):
    global current_suite
    suite.state = ResiliencySuiteStatusEnum.QUEUED
    current_suite = suite
    return {"status": "queued"}


# -------------------------------------------------------------------
# Ingest Events
# -------------------------------------------------------------------


@app.post("/api/v1/ingest/events", status_code=status.HTTP_201_CREATED)
async def ingest_events(request: Request):
    payload = await request.json()
    print(payload)
    return {"status": "events_queued", "count": len(payload)}


# -------------------------------------------------------------------
# Ingest Events
# -------------------------------------------------------------------


@app.post("/api/v1/ingest/metrics", status_code=status.HTTP_201_CREATED)
async def ingest_metrics(request: Request):
    payload = await request.json()
    print(payload)
    return {"status": "metrics_queued", "count": len(payload)}
