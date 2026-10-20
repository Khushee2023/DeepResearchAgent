from pydantic import BaseModel, Field
from app import config
from app.llm import get_llm
from app.prompts import PLANNER_PROMPT


class Plan(BaseModel):
    sub_questions: list[str] = Field(
        description="Focused, searchable sub-questions that together cover the query"
    )


def planner_node(state: dict) -> dict:
    questions: list[str] = []
    try:
        llm = get_llm().with_structured_output(Plan)
        plan = llm.invoke(
            PLANNER_PROMPT.format(query=state["query"], max_q=config.MAX_SUBQUESTIONS)
        )
        questions = (plan.sub_questions if plan else [])[: config.MAX_SUBQUESTIONS]
    except Exception as e:
        print(f"[planner] LLM failed, using the query as the plan: {e}")

    if not questions:  # fallback: poori query hi research karo
        questions = [state["query"]]
    return {"plan": questions, "iteration": 0}