import sys
import uuid

from langgraph.types import Command

from app import config
from app.graph import build_graph


def run_until_pause(graph, inputs, run_config):
    for update in graph.stream(inputs, run_config, stream_mode="updates"):
        for node in update:
            if node != "__interrupt__":
                print(f"[done] {node}")


def main():
    config.validate()
    query = " ".join(sys.argv[1:]) or "How is AI being used in healthcare diagnostics?"

    graph = build_graph()
    run_config = {
        "configurable": {"thread_id": str(uuid.uuid4())},
        "recursion_limit": 50,
        "max_concurrency": 3,  # Gemini free tier rate limits ke liye
    }

    run_until_pause(graph, {"query": query}, run_config)

    # Jab tak graph pause hai (plan approval), user se pooch kar resume karo
    while True:
        snapshot = graph.get_state(run_config)
        if not snapshot.next:
            break
        payload = snapshot.tasks[0].interrupts[0].value
        print("\nPROPOSED PLAN:")
        for i, q in enumerate(payload["plan"], start=1):
            print(f"  {i}. {q}")
        answer = input("\nPress Enter to approve, or type new questions separated by ';' : ").strip()
        resume = [q for q in answer.split(";") if q.strip()] if answer else True
        run_until_pause(graph, Command(resume=resume), run_config)

    final = graph.get_state(run_config).values
    print("\n" + "=" * 70 + "\n")
    print(final.get("report", "No report generated."))


if __name__ == "__main__":
    main()