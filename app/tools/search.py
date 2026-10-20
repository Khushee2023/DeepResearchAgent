from tavily import TavilyClient
from app import config
from app.state import Source

_client: TavilyClient | None = None


def _get_client() -> TavilyClient:
    global _client
    if _client is None:
        _client = TavilyClient(api_key=config.TAVILY_API_KEY)
    return _client


def search_web(query: str) -> list[Source]:
    """Tavily top results. Fail ho to empty list, poora graph crash nahi hota."""
    try:
        resp = _get_client().search(
            query=query,
            max_results=config.MAX_SEARCH_RESULTS,
            search_depth="basic",
            timeout=config.SEARCH_TIMEOUT,
        )
    except Exception as e:
        print(f"[search] failed for '{query}': {e}")
        return []

    return [
        {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")}
        for r in resp.get("results", [])
        if r.get("url")
    ]