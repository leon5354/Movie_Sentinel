"""
Movie_Sentinel - Configuration Module
All adjustable parameters in one place.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ===========================================
# LLM Provider Settings
# ===========================================
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

# Provider-specific settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")

# ===========================================
# Model Behavior
# ===========================================
TEMPERATURE = 0.1  # Low for consistent classification
MAX_TOKENS = 512
RETRY_ATTEMPTS = 3
RETRY_DELAY_BASE = 2  # Exponential backoff base (seconds)

# ===========================================
# Data Settings
# ===========================================
INPUT_FILE_PATH = "data/movie_reviews.csv"
OUTPUT_FILE_PATH = "output/processed_reviews.csv"

# Column mapping - adjust these to match your CSV structure
COMMENT_COL_NAME = "review_text"
DATE_COL_NAME = "date"
ID_COL_NAME = "id"

# ===========================================
# Classification Settings
# ===========================================
# Initial taxonomy - the "known" topics for movie reviews
MASTER_TOPICS = [
    "Acting Performance",
    "Plot & Story",
    "Visual Effects",
    "Cinematography",
    "Soundtrack & Score",
    "Direction",
    "Dialogue",
]

# Topic discovery settings
DISCOVERY_THRESHOLD = 5  # Min hits before auto-adding topic
MIN_CONFIDENCE = 0.7  # Minimum confidence for label assignment

# ===========================================
# Synthetic Data Generation
# ===========================================
SYNTHETIC_ROW_COUNT = 150
HIDDEN_TOPIC_NAME = "Pacing Issues"
HIDDEN_TOPIC_RATIO = 0.15  # 15% of rows will be about the hidden topic

# ===========================================
# Sentinel Settings
# ===========================================
SENTINEL_LOG_FILE = "output/sentinel_log.json"

# ===========================================
# Validation
# ===========================================
def validate_config():
    """Validate that required credentials exist for the selected provider."""
    provider = LLM_PROVIDER
    
    if provider == "openai" and not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set in .env")
    elif provider == "anthropic" and not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set in .env")
    elif provider == "google" and not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not set in .env")
    
    return True
