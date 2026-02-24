"""
Classification engine. Handles the core labeling logic.
"""

import json
import re
import logging
from typing import Optional
from pydantic import BaseModel, field_validator

from config import MASTER_TOPICS, MIN_CONFIDENCE
from .llm_wrapper import structured_complete

logger = logging.getLogger(__name__)


class ClassificationResult(BaseModel):
    labels: list[str]
    sentiment: str
    confidence: float = 0.8
    suggested_label: Optional[str] = None
    suggestion_reason: Optional[str] = None

    @field_validator("labels")
    @classmethod
    def clean_labels(cls, v):
        return [label.strip() for label in v if label.strip()]

    @field_validator("sentiment")
    @classmethod
    def fix_sentiment(cls, v):
        valid = ["positive", "negative", "neutral", "mixed"]
        normalized = v.lower().strip()
        return normalized if normalized in valid else "neutral"


def _build_prompt(known_topics: list[str]) -> str:
    """Build the system prompt with current topic list."""
    topics_str = ", ".join(f'"{t}"' for t in known_topics)

    return f"""You classify movie reviews.

AVAILABLE TOPICS:
{topics_str}

Rules:
1. First, try to match the review to one of the AVAILABLE TOPICS
2. If it clearly doesn't fit any topic, use "UNCATEGORIZED" as the label
3. When using UNCATEGORIZED, you MUST suggest a new topic name
4. Sentiment options: positive, negative, neutral, mixed

Output format (JSON only):
{{"labels": ["Topic"], "sentiment": "neutral", "confidence": 0.9, "suggested_label": null, "suggestion_reason": null}}

For uncategorized reviews:
{{"labels": ["UNCATEGORIZED"], "sentiment": "negative", "confidence": 0.85, "suggested_label": "New Topic Name", "suggestion_reason": "Why this is a new category"}}"""


def _parse_json(text: str) -> dict:
    """Pull JSON out of messy LLM output."""
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)

    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return {}


class ReviewClassifier:
    def __init__(self, topics: list[str] = None):
        self.topics = topics or MASTER_TOPICS.copy()
        self.discovery_buffer: dict[str, list[dict]] = {}  # topic -> list of {review, idx}
        self._pending_retags: list[tuple[int, str]] = []  # (idx, new_label)

    def add_topic(self, topic: str) -> bool:
        """Add a new topic to the active list."""
        clean = topic.strip().title()
        if clean and clean not in self.topics:
            self.topics.append(clean)
            return True
        return False

    def classify(self, review: str, idx: int = None) -> ClassificationResult:
        """
        Classify a single movie review.

        idx is optional but needed if you want re-tagging to work later.
        """
        system = _build_prompt(self.topics)
        user = f"Classify:\n\n\"{review}\""

        try:
            raw = structured_complete(prompt=user, system=system, json_mode=True)
            data = _parse_json(raw)

            # normalize labels against our topic list
            final_labels = []
            for label in data.get("labels", []):
                clean = label.strip()
                if clean.upper() == "UNCATEGORIZED":
                    final_labels.append("UNCATEGORIZED")
                else:
                    # fuzzy match to known topics
                    for known in self.topics:
                        if clean.lower() in known.lower() or known.lower() in clean.lower():
                            final_labels.append(known)
                            break

            result = ClassificationResult(
                labels=final_labels,
                sentiment=data.get("sentiment", "neutral"),
                confidence=data.get("confidence", 0.7),
                suggested_label=data.get("suggested_label"),
                suggestion_reason=data.get("suggestion_reason"),
            )

            # buffer new topic suggestions for the sentinel
            if result.suggested_label and "UNCATEGORIZED" in result.labels:
                key = result.suggested_label.strip().title()
                if key not in self.discovery_buffer:
                    self.discovery_buffer[key] = []
                self.discovery_buffer[key].append({
                    "review": review,
                    "idx": idx,
                    "sentiment": result.sentiment,
                })

            return result

        except Exception as e:
            logger.error(f"Classification error: {e}")
            return ClassificationResult(labels=[], sentiment="neutral", confidence=0.0)

    def promote_topic(self, topic: str) -> list[tuple[int, str]]:
        """
        Promote a discovered topic to the master list.
        Returns list of (idx, new_label) pairs for re-tagging.
        """
        key = topic.strip().title()
        retags = []

        if key not in self.discovery_buffer:
            return retags

        self.add_topic(key)

        # collect items that need re-tagging
        for entry in self.discovery_buffer[key]:
            if entry["idx"] is not None:
                retags.append((entry["idx"], key))

        # clear from buffer
        del self.discovery_buffer[key]

        return retags

    def get_buffer(self) -> dict:
        """What's pending in the discovery buffer."""
        return self.discovery_buffer.copy()

    def get_topics(self) -> list[str]:
        """Current topic list."""
        return self.topics.copy()
