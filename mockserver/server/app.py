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


@app.get("/api/v1/agent/plan")
async def agent_fetch_plan():
    """Simulate fetching a new resiliency plan."""
    await h.maybe_delay()
    failure = await h.maybe_fail()
    plan = h.get_resiliency_plan()
    return failure or JSONResponse(plan)


@app.post("/api/v1/agent/plan/ack")
async def agent_acknowledge_plan(request: Request):
    """Simulate acknowledging a resiliency plan."""
    await h.maybe_delay()
    failure = await h.maybe_fail()
    return failure or JSONResponse({"status": "ok"})


@app.get("/api/v1/agent/plan/{plan_id}/step/{step_id}")
async def agent_fetch_plan_step(plan_id: int, step_id: int):
    """Simulate fetching a new resiliency plan step."""
    await h.maybe_delay()
    failure = await h.maybe_fail()
    step = h.get_resiliency_plan_step()
    step["id"] = step_id
    return failure or JSONResponse(step)
