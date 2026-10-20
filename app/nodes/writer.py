import re
from app.llm import get_llm, get_text
from app.prompts import WRITER_PROMPT

CITE_RE = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")


def _number_findings(findings: list[dict]) -> tuple[str, list[dict]]:
    """Har finding ke local [1],[2] ko global numbers mein badlo (URL se dedupe)."""
    url_to_id: dict[str, int] = {}
    all_sources: list[dict] = []
    blocks: list[str] = []

    for f in findings:
        local_to_global: dict[int, int] = {}
        for i, s in enumerate(f["sources"], start=1):
            if s["url"] not in url_to_id:
                url_to_id[s["url"]] = len(url_to_id) + 1
                all_sources.append(s)
            local_to_global[i] = url_to_id[s["url"]]

        summary = re.sub(
            r"\[(\d+)\]",
            lambda m: f"[{local_to_global[int(m.group(1))]}]"
            if int(m.group(1)) in local_to_global
            else "",
            f["summary"],
        )
        blocks.append(f"Question: {f['question']}\nFinding: {summary}")

    return "\n\n".join(blocks), all_sources


def _compact_citations(report: str, sources: list[dict]) -> tuple[str, list[dict]]:
    """Sirf jo sources report mein cite hue unhe rakho, aur first-use order mein renumber karo."""
    mapping: dict[int, int] = {}

    def repl(m: re.Match) -> str:
        new_ids = []
        for n in (int(x) for x in re.split(r"\s*,\s*", m.group(1))):
            if 1 <= n <= len(sources):
                mapping.setdefault(n, len(mapping) + 1)
                new_ids.append(mapping[n])
        return "[" + ", ".join(map(str, sorted(set(new_ids)))) + "]" if new_ids else ""

    report = CITE_RE.sub(repl, report)
    used: list[dict] = [{}] * len(mapping)
    for old, new in mapping.items():
        used[new - 1] = sources[old - 1]
    return report, used


def writer_node(state: dict) -> dict:
    findings = state.get("findings", [])
    if not findings:
        return {"report": "No findings were gathered, so no report could be written."}

    findings_text, sources = _number_findings(findings)
    response = get_llm().invoke(
        WRITER_PROMPT.format(query=state["query"], findings=findings_text)
    )
    report, used_sources = _compact_citations(get_text(response), sources)

    # Sources code se jodte hain (LLM se nahi), taaki URLs hallucinate na hon
    if used_sources:
        refs = "\n".join(
            f"[{i}] {s['title']} - {s['url']}" for i, s in enumerate(used_sources, start=1)
        )
        report += f"\n\n## Sources\n{refs}"

    return {"report": report}