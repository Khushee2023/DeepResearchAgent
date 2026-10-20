from langchain_google_genai import ChatGoogleGenerativeAI
from app import config


def get_llm(temperature: float | None = None) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=config.MODEL_NAME,
        temperature=config.TEMPERATURE if temperature is None else temperature,
        google_api_key=config.GOOGLE_API_KEY,
        timeout=config.LLM_TIMEOUT,
        max_retries=config.LLM_MAX_RETRIES,
    )


def get_text(response) -> str:
    """Gemini kabhi string, kabhi content blocks ki list deta hai. Dono se plain text nikalo."""
    content = response.content
    if isinstance(content, str):
        return content.strip()
    parts = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "".join(parts).strip()