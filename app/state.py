import operator
from typing import Annotated, TypedDict


class Source(TypedDict):
    title: str
    url: str
    snippet: str


class Finding(TypedDict):
    question: str
    summary: str
    sources: list[Source]


class ResearchState(TypedDict, total=False):
    query: str
    plan: list[str]
    findings: Annotated[list[Finding], operator.add]  # reducer: parallel results merge hote hain
    gaps: list[str]
    iteration: int
    report: str


class ResearcherInput(TypedDict):
    """Send() se har parallel researcher ko ye milta hai."""
    question: str