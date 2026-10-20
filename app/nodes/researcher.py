from app.llm import get_llm, get_text
from app.prompts import RESEARCHER_PROMPT
from app.tools.search import search_web


def researcher_node(state: dict) -> dict:
    """Ek sub-question ke liye search + summarize.
    Prompt 3 mein Send() isko har question ke liye parallel chalayega."""
    question = state["question"]
    sources = search_web(question)

    if not sources:
        finding = {
            "question": question,
            "summary": "No sources were found for this question.",
            "sources": [],
        }
        return {"findings": [finding]}

    context = "\n\n".join(
        f"[{i}] {s['title']} ({s['url']})\n{s['snippet']}"
        for i, s in enumerate(sources, start=1)
    )
    try:
        response = get_llm().invoke(
            RESEARCHER_PROMPT.format(question=question, context=context)
        )
        summary = get_text(response)
    except Exception as e:  # ek worker fail ho to baaki parallel workers na rukein
        print(f"[researcher] failed for '{question}': {e}")
        summary = "Summarization failed for this question."

    # Return list hai kyunki state mein reducer (operator.add) is key par lagta hai
    return {"findings": [{"question": question, "summary": summary, "sources": sources}]}