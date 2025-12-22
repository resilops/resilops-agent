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
async def fetch_plan():
    """Simulate fetching a new fault plan."""
    await h.maybe_delay()
    failure = await h.maybe_fail()
    plan = h.get_fault_plan()
    return failure or JSONResponse(plan)


@app.post("/api/v1/agent/plan/ack")
async def acknowledge_plan(request: Request):
    """Simulate acknowledging a fault plan."""
    await h.maybe_delay()
    failure = await h.maybe_fail()
    return failure or JSONResponse({"status": "ok"})


@app.post("/api/v1/agent/events")
async def agent_event(request: Request):
    """Simulate agent sending events."""
    await h.maybe_delay()
    failure = await h.maybe_fail()
    if failure:
        return failure

    body = await request.body()
    data = await request.json() if body else {}
    return JSONResponse({"received": data})
