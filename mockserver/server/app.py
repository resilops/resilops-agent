from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from server import helpers as h

app = FastAPI(title="Control Plane API")


@app.get("/api/v1/agent/heartbeat")
async def agent_heartbeat():
    """Simulate heartbeat endpoint."""
    await h.maybe_delay()
    failure = await h.maybe_fail()
    return failure or JSONResponse({"status": "ok"})


@app.get("/api/v1/agent/suite")
async def agent_fetch_suite():
    """Simulate fetching a new resiliency test suite."""
    await h.maybe_delay()
    failure = await h.maybe_fail()
    suite = h.get_resiliency_suite()
    return failure or JSONResponse(suite)


@app.post("/api/v1/agent/suite/ack")
async def agent_acknowledge_suite(request: Request):
    """Simulate acknowledging a resiliency suite."""
    await h.maybe_delay()
    failure = await h.maybe_fail()
    return failure or JSONResponse({"status": "ok"})


@app.get("/api/v1/agent/suite/{suite_id}/scenario/{scenario_id}")
async def agent_fetch_scenario(suite_id: int, scenario_id: int):
    """Simulate fetching a new resiliency scenario from a given suite."""
    await h.maybe_delay()
    failure = await h.maybe_fail()
    scenario = h.get_scenario()
    scenario["id"] = scenario_id
    return failure or JSONResponse(scenario)
