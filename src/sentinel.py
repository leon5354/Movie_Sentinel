"""
Sentinel - the dynamic topic discovery module.
Watches for emerging patterns and auto-expands the taxonomy.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel

from config import DISCOVERY_THRESHOLD, SENTINEL_LOG_FILE

logger = logging.getLogger(__name__)


class Alert(BaseModel):
    topic: str
    hits: int
    first_seen: str
    samples: list[str] = []


class Sentinel:
    """
    Watches for new topics that aren't in the master list.
    When something gets mentioned enough, it gets promoted.
    """

    def __init__(self, threshold: int = DISCOVERY_THRESHOLD):
        self.threshold = threshold
        self.candidates: dict[str, dict] = {}  # pending topics
        self.confirmed: list[str] = []  # promoted topics
        self.log_path = Path(SENTINEL_LOG_FILE)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def observe(
        self,
        suggested: str,
        review: str,
        idx: int = None,
        reason: str = None
    ) -> bool:
        """
        Log a topic suggestion. Returns True if threshold hit.

        idx is the row index - needed for re-tagging later.
        """
        if not suggested:
            return False

        key = suggested.strip().title()

        if key in self.confirmed:
            return False

        if key not in self.candidates:
            self.candidates[key] = {
                "count": 0,
                "first_seen": datetime.now().isoformat(),
                "samples": [],
                "indices": [],  # track which rows mentioned this
            }

        self.candidates[key]["count"] += 1

        if idx is not None:
            self.candidates[key]["indices"].append(idx)

        # keep a few sample reviews for the log
        if len(self.candidates[key]["samples"]) < 5:
            self.candidates[key]["samples"].append(review[:200])

        # check if we hit threshold
        if self.candidates[key]["count"] >= self.threshold:
            self._promote(key)
            return True

        return False

    def _promote(self, topic: str) -> None:
        """Promote a candidate topic to confirmed."""
        self.confirmed.append(topic)
        data = self.candidates[topic]

        # console alert
        logger.info(
            f"\n{'='*50}\n"
            f"🚨 Sentinel Alert: New category '{topic}' detected and added to taxonomy.\n"
            f"   Hits: {data['count']}\n"
            f"{'='*50}"
        )

        # write to log
        self._log_alert(Alert(
            topic=topic,
            hits=data["count"],
            first_seen=data["first_seen"],
            samples=data["samples"],
        ))

    def _log_alert(self, alert: Alert) -> None:
        """Append alert to the JSON log."""
        entries = []
        if self.log_path.exists():
            try:
                with open(self.log_path, "r") as f:
                    entries = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        entries.append(alert.model_dump())
        with open(self.log_path, "w") as f:
            json.dump(entries, f, indent=2, default=str)

    def get_candidate_indices(self, topic: str) -> list[int]:
        """Get row indices for a candidate topic (for re-tagging)."""
        key = topic.strip().title()
        if key in self.candidates:
            return self.candidates[key].get("indices", [])
        return []

    def get_pending(self) -> dict[str, int]:
        """Topics that haven't hit threshold yet."""
        return {
            t: d["count"]
            for t, d in self.candidates.items()
            if t not in self.confirmed
        }

    def get_confirmed(self) -> list[str]:
        """Topics that have been promoted."""
        return self.confirmed.copy()

    def status(self) -> str:
        """Human-readable status dump."""
        lines = [
            "🔍 Sentinel Status",
            "-" * 30,
            f"Threshold: {self.threshold}",
            f"Watching: {len(self.candidates)} candidates",
            f"Promoted: {len(self.confirmed)} topics",
        ]

        if self.confirmed:
            lines.append("\n✅ Promoted:")
            for t in self.confirmed:
                lines.append(f"   • {t}")

        pending = self.get_pending()
        if pending:
            lines.append("\n⏳ Pending:")
            for t, count in sorted(pending.items(), key=lambda x: -x[1]):
                bar = "█" * count + "░" * (self.threshold - count)
                lines.append(f"   • {t} [{bar}] {count}/{self.threshold}")

        return "\n".join(lines)
