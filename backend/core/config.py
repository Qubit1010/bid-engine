"""Central configuration for the BidSense backend."""
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

DATA_DIR = BACKEND_DIR / "data"
MODELS_DIR = BACKEND_DIR / "models"
CACHE_DIR = BACKEND_DIR / "cache"
UPLOADS_DIR = BACKEND_DIR / "uploads"
DB_PATH = BACKEND_DIR / "bidsense.db"

for d in (MODELS_DIR, CACHE_DIR, UPLOADS_DIR):
    d.mkdir(exist_ok=True)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")
EMBEDDING_MODEL = "text-embedding-3-small"

# Bid-history sectors the win-probability model is trained on.
SECTORS = [
    "Construction", "Education", "Energy", "Finance",
    "Healthcare", "IT Services", "Logistics", "Telecom",
]

# Industry baseline used for the effort-reduction metric (problem statement:
# bid managers spend 60-80% of their time on manual prep; a 15-80 page RFP
# typically takes 2-4 working days to first draft).
MANUAL_BASELINE_HOURS_PER_PAGE = 0.5
MANUAL_BASELINE_MIN_HOURS = 16.0

# Demo pacing: floors each pipeline step's wall time (seconds) so the live
# stepper stays followable when LLM responses replay from the disk cache.
# 0 disables. Set ~1.5 in .env for stage demos.
DEMO_MIN_STEP_SECONDS = float(os.getenv("DEMO_MIN_STEP_SECONDS", "0"))
