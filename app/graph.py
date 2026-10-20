import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send, interrupt

from app import config
from app.nodes.critic import critic_node
from app.nodes.planner import planner_node
from app.nodes.researcher import researcher_node
from app.nodes.writer import writer_node
from app.state import ResearchState


def approve_plan_node(state: dict) -> dict:
    """Graph yahan ruk jata hai. Resume value:
    - True / None  -> plan jaisa hai approve
    - list[str]    -> user ka edited plan
    Dhyan: resume par ye node shuru se dobara chalta hai, isliye interrupt se pehle koi side effect nahi."""
    decision = interrupt({"plan": state["plan"], "message": "Approve or edit the research plan"})
    if isinstance(decision, list):
        cleaned = [q.strip() for q in decision if isinstance(q, str) and q.strip()]
        if cleaned:
            return {"plan": cleaned}
    return {"plan": state["plan"]}


def fan_out_plan(state: dict):
    """Har sub-question ke liye ek parallel researcher (map-reduce)."""
    return [Send("researcher", {"question": q}) for q in state["plan"]]


def route_after_critic(state: dict):
    """Gaps hain to unhi par dobara parallel research, warna writer."""
    gaps = state.get("gaps") or []
    if gaps:
        return [Send("researcher", {"question": g}) for g in gaps]
    return "writer"


def get_checkpointer() -> SqliteSaver:
    conn = sqlite3.connect(config.CHECKPOINT_DB, check_same_thread=False)
    return SqliteSaver(conn)


def build_graph(checkpointer=None):
    g = StateGraph(ResearchState)

    g.add_node("planner", planner_node)
    g.add_node("approve_plan", approve_plan_node)
    g.add_node("researcher", researcher_node)
    g.add_node("critic", critic_node)
    g.add_node("writer", writer_node)

    g.add_edge(START, "planner")
    g.add_edge("planner", "approve_plan")
    g.add_conditional_edges("approve_plan", fan_out_plan, ["researcher"])
    g.add_edge("researcher", "critic")
    g.add_conditional_edges("critic", route_after_critic, ["researcher", "writer"])
    g.add_edge("writer", END)

    return g.compile(checkpointer=checkpointer or get_checkpointer())