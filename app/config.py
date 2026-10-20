import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

MODEL_NAME = "gemini-3.1-flash-lite"
TEMPERATURE = 0.2
LLM_TIMEOUT = 90
LLM_MAX_RETRIES = 2

MAX_ITERATIONS = 2        # critic loop kitni baar chalega
MAX_SUBQUESTIONS = 4      # planner ke max sub-questions
MAX_SEARCH_RESULTS = 3    # har sub-question par Tavily results
SEARCH_TIMEOUT = 30

CHECKPOINT_DB = "checkpoints.db"


def validate():
    missing = [
        n for n, v in [("GOOGLE_API_KEY", GOOGLE_API_KEY), ("TAVILY_API_KEY", TAVILY_API_KEY)]
        if not v
    ]
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}. Check your .env file.")