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
    """Simulate fetching a new fault plan."""
    await h.maybe_delay()
    failure = await h.maybe_fail()
    plan = h.get_fault_plan()
    return failure or JSONResponse(plan)


@app.post("/api/v1/agent/plan/ack")
async def agent_acknowledge_plan(request: Request):
    """Simulate acknowledging a fault plan."""
    await h.maybe_delay()
    failure = await h.maybe_fail()
    return failure or JSONResponse({"status": "ok"})


@app.get("/api/v1/agent/fault/{fault_id}")
async def agent_fetch_fault(fault_id: int):
    """Simulate fetching a new fault."""
    await h.maybe_delay()
    failure = await h.maybe_fail()
    fault = h.get_fault()
    fault["id"] = fault_id
    return failure or JSONResponse(fault)
