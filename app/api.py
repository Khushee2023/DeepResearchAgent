import json
import uuid
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from langgraph.types import Command

from app import config
from app.graph import build_graph

config.validate()

app = FastAPI(title="Deep Research Agent")
graph = build_graph()  # ek baar build, sab requests share karti hain

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def run_config(thread_id: str) -> dict:
    return {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 50,
        "max_concurrency": 3,  # Gemini rate limits ke liye
    }


def stream_run(inputs, thread_id: str):
    """Graph chalao, progress events yield karo. Ruk jaye (plan approval) to 'plan' event,
    khatam ho jaye to 'report' event."""
    cfg = run_config(thread_id)
    try:
        for update in graph.stream(inputs, cfg, stream_mode="updates"):
            for node, out in update.items():
                if node == "__interrupt__":
                    continue
                detail = None
                if node == "researcher" and isinstance(out, dict):
                    findings = out.get("findings") or []
                    if findings:
                        detail = findings[0].get("question")
                yield sse("progress", {"node": node, "detail": detail})

        snapshot = graph.get_state(cfg)
        if snapshot.next:  # plan approval par pause
            payload = snapshot.tasks[0].interrupts[0].value
            yield sse("plan", {"thread_id": thread_id, "plan": payload["plan"]})
        else:
            yield sse("report", {"report": snapshot.values.get("report", "")})
    except Exception as e:
        yield sse("error", {"message": str(e)})
    yield sse("done", {})


@app.get("/api/start")
def start(query: str):
    thread_id = str(uuid.uuid4())

    def gen():
        yield sse("thread", {"thread_id": thread_id})
        yield from stream_run({"query": query}, thread_id)

    return StreamingResponse(gen(), media_type="text/event-stream", headers=SSE_HEADERS)


@app.get("/api/resume/{thread_id}")
def resume(thread_id: str, plan: str | None = None):
    """plan = JSON list of sub-questions (edited plan). Na do to original plan approve."""
    decision = True
    if plan:
        try:
            parsed = json.loads(plan)
            if isinstance(parsed, list):
                decision = parsed
        except json.JSONDecodeError:
            pass
    return StreamingResponse(
        stream_run(Command(resume=decision), thread_id),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


# Frontend (Prompt 5 mein banega)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR, check_dir=False), name="static")


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")