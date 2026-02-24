# Movie_Sentinel

Movie review classification with automatic topic discovery.

## What It Does

Classifies movie reviews into topics, but also watches for new patterns. When enough reviews mention something you didn't anticipate, it notices and adds that topic automatically.

## How It Works

### The Hybrid Logic

Two modes working together:

1. **Guided Mode** - LLM tries to fit reviews into your existing topics
2. **Discovery Mode** - When a review doesn't fit, it gets labeled UNCATEGORIZED and the LLM suggests a new topic name

```
┌─────────────────────────────────────────────────────────────┐
│                      INCOMING REVIEW                         │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
              ┌───────────────────────┐
              │  Does it fit a known  │
              │       topic?          │
              └───────────┬───────────┘
                    │           │
                   YES          NO
                    │           │
                    ▼           ▼
            ┌──────────┐  ┌─────────────────────────┐
            │ Label it │  │ Label: UNCATEGORIZED    │
            │ normally │  │ + suggest new topic     │
            └──────────┘  └──────────┬──────────────┘
                                    │
                                    ▼
                          ┌─────────────────────┐
                          │ Sentinel counts it  │
                          └──────────┬──────────┘
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │ Hit threshold (5)?  │
                          └──────────┬──────────┘
                                │         │
                               NO        YES
                                │         │
                                ▼         ▼
                          ┌────────┐  ┌─────────────────────┐
                          │ Wait   │  │ PROMOTE:            │
                          │ more   │  │ • Add to topics     │
                          └────────┘  │ • Re-tag old rows   │
                                      │ • Alert user        │
                                      └─────────────────────┘
```

---

## Configuration Guide

### All Editable Parameters

Open `config.py` and change these:

```python
# ============================================
# LLM SETTINGS
# ============================================
LLM_PROVIDER = "ollama"        # ollama, openai, anthropic, google
TEMPERATURE = 0.1              # 0.0-1.0 (lower = more consistent)
MAX_TOKENS = 512               # Max response length
RETRY_ATTEMPTS = 3             # How many times to retry on failure

# ============================================
# DISCOVERY SETTINGS
# ============================================
DISCOVERY_THRESHOLD = 5        # Hits needed to auto-add new topic
MIN_CONFIDENCE = 0.7           # Minimum confidence to accept label

# ============================================
# DATA SETTINGS
# ============================================
INPUT_FILE_PATH = "data/movie_reviews.csv"       # Where to read
OUTPUT_FILE_PATH = "output/processed_reviews.csv" # Where to save

# Column names in your CSV (change these!)
COMMENT_COL_NAME = "review_text"
DATE_COL_NAME = "date"
ID_COL_NAME = "id"

# ============================================
# TOPIC TAXONOMY
# ============================================
MASTER_TOPICS = [
    "Acting Performance",
    "Plot & Story",
    "Visual Effects",
    "Cinematography",
    "Soundtrack & Score",
    "Direction",
    "Dialogue",
]
```

---

### Changing Topics for Your Dataset

In `config.py`, find the `MASTER_TOPICS` list and edit it:

```python
# Example: Film festival reviews
MASTER_TOPICS = [
    "Acting",
    "Story",
    "Cinematography",
    "Sound",
    "Editing",
]

# Example: Streaming platform reviews
MASTER_TOPICS = [
    "Content Quality",
    "User Interface",
    "Streaming Quality",
    "Subtitle/CC",
    "Recommendation Algorithm",
]
```

Topics should be:
- **Short** (1-3 words)
- **Distinct** (not overlapping)
- **Broad enough** to catch variations

---

### Adjusting Columns for Different Datasets

Your CSV might have different column names. Change these in `config.py`:

```python
# If your CSV looks like:
# review_id, created_at, review_text, rating
COMMENT_COL_NAME = "review_text"
DATE_COL_NAME = "created_at"
ID_COL_NAME = "review_id"
```

Or override via command line:

```bash
python3 scripts/run.py --input mydata.csv --comment-col "review_text"
```

---

## Quick Start

### 1. Install

```bash
cd Movie_Sentinel
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your provider and API key
```

### 3. Run

```bash
# Test with synthetic data
python3 scripts/run.py --generate --limit 20

# Your own data
python3 scripts/run.py --input your_data.csv --comment-col "your_column"
```

---

## CLI Reference

```bash
python3 scripts/run.py [options]

Options:
  --input, -i FILE       Input CSV file (default: data/movie_reviews.csv)
  --comment-col, -c COL  Column name for review text (default: review_text)
  --generate, -g         Generate test data before running
  --limit, -l N          Only process N rows (for testing)
```

---

## Output

### Console Dashboard

```
╔════════════════════════════════════════════════════════════════╗
║                  MOVIE_SENTINEL DASHBOARD                      ║
╠════════════════════════════════════════════════════════════════╣
  Generated: 2026-02-24 09:00:00
  Total reviews: 150
  Uncategorized: 0

  TOP TOPICS:
    1. Acting Performance   ████████ (32)
    2. Plot & Story         ██████ (24)
    3. Pacing Issues        █████ (22)

  SENTIMENT:
    💚 positive    ████████ 45 (30%)
    ❤️ negative    ██████████ 52 (35%)
    🤍 neutral     ████████ 38 (25%)
    💛 mixed       ███ 15 (10%)

  NEW TOPICS FOUND:
    ✨ Pacing Issues
╚════════════════════════════════════════════════════════════════╝
```

### CSV Output Columns

| Column | Description |
|--------|-------------|
| `[original columns]` | Your input data preserved |
| `labels` | List of matched topics |
| `sentiment` | positive / negative / neutral / mixed |
| `confidence` | Model confidence (0.0 - 1.0) |
| `suggested_label` | New topic name (if UNCATEGORIZED) |
| `discovery_source` | True = this review triggered topic discovery |

---

## Provider Setup

### Ollama (Local, Free)

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3
```

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434
```

### OpenAI

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

### Anthropic

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-haiku-20240307
```

### Google Gemini

```env
LLM_PROVIDER=google
GOOGLE_API_KEY=...
GOOGLE_MODEL=gemini-2.0-flash
```

---

## Project Structure

```
Movie_Sentinel/
├── config.py              # <-- EDIT THIS (topics, columns, settings)
├── .env                   # <-- EDIT THIS (API keys, provider)
├── .env.example
│
├── src/
│   ├── llm_wrapper.py     # Provider interface
│   ├── classifier.py      # Labeling logic
│   ├── sentinel.py        # Topic discovery
│   └── reporter.py        # Output
│
├── scripts/
│   ├── run.py             # Main entry
│   └── generate_test_data.py
│
├── data/                  # Put your CSVs here
└── output/                # Results saved here
```

---

## Tips

- Run with `--limit 20` first to test your setup
- Check `output/sentinel_log.json` for discovery history
- Topics work best when they're mutually exclusive
- If too many UNCATEGORIZED, your topics might be too narrow
- If nothing gets discovered, topics might be too broad
