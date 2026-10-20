from pydantic import BaseModel, Field
from app import config
from app.llm import get_llm
from app.prompts import CRITIC_PROMPT

MAX_GAPS = 3


class Critique(BaseModel):
    enough: bool = Field(description="True if the findings cover the query well")
    gaps: list[str] = Field(
        default_factory=list,
        description="New searchable follow-up questions if coverage is not enough",
    )


def critic_node(state: dict) -> dict:
    iteration = state.get("iteration", 0) + 1
    findings = state.get("findings", [])

    # Max iterations ho gaye to critic ko bulana hi nahi, seedha stop
    if iteration > config.MAX_ITERATIONS:
        return {"gaps": [], "iteration": iteration}

    asked = [f["question"] for f in findings]
    findings_text = "\n\n".join(
        f"Q: {f['question']}\nA: {f['summary']}" for f in findings
    )

    try:
        llm = get_llm().with_structured_output(Critique)
        result = llm.invoke(
            CRITIC_PROMPT.format(
                query=state["query"],
                asked="\n".join(f"- {q}" for q in asked),
                findings=findings_text,
                max_gaps=MAX_GAPS,
            )
        )
    except Exception as e:
        print(f"[critic] LLM failed, skipping further research: {e}")
        result = None

    if result is None or result.enough:
        gaps: list[str] = []
    else:
        # already pooche gaye questions dobara nahi
        gaps = [g for g in result.gaps if g not in asked][:MAX_GAPS]

    return {"gaps": gaps, "iteration": iteration}