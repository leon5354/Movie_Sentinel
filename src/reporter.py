"""
Output and reporting. Exports CSV and prints the dashboard.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional


class Reporter:
    """Handles all the output stuff."""

    def __init__(self, output_path: str = None):
        self.output_path = Path(output_path or "output/processed_reviews.csv")
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.tokens = 0
        self.latency = 0.0
        self.count = 0

    def track(self, tokens: int = None, latency_ms: float = None) -> None:
        """Keep tabs on usage stats."""
        if tokens:
            self.tokens += tokens
        if latency_ms:
            self.latency += latency_ms
        self.count += 1

    def export(
        self,
        original: pd.DataFrame,
        results: list[dict],
        path: str = None
    ) -> str:
        """
        Merge original data with results and save.
        Returns the output path.
        """
        out = Path(path) if path else self.output_path
        merged = pd.concat([original.reset_index(drop=True), pd.DataFrame(results)], axis=1)
        merged.to_csv(out, index=False)
        return str(out)

    def dashboard(
        self,
        results: list[dict],
        discovered: list[str],
        current_topics: list[str],
    ) -> None:
        """Print the summary dashboard."""
        df = pd.DataFrame(results)

        # count by topic
        topic_counts = {}
        for labels in df["labels"]:
            for label in labels:
                topic_counts[label] = topic_counts.get(label, 0) + 1

        sorted_topics = sorted(topic_counts.items(), key=lambda x: -x[1])

        # sentiment split
        sentiment_counts = df["sentiment"].value_counts().to_dict()

        # uncategorized count
        uncategorized = topic_counts.get("UNCATEGORIZED", 0)

        print("\n")
        print("╔" + "═" * 60 + "╗")
        print("║" + "MOVIE_SENTINEL DASHBOARD".center(60) + "║")
        print("╠" + "═" * 60 + "╣")
        print(f"  Generated: {datetime.now():%Y-%m-%d %H:%M:%S}")
        print(f"  Total reviews: {len(results)}")
        print(f"  Uncategorized: {uncategorized}")
        print()
        print("  TOP TOPICS:")

        for i, (topic, count) in enumerate(sorted_topics[:5], 1):
            if topic == "UNCATEGORIZED":
                continue
            bar = "█" * min(count // 2, 20)
            print(f"    {i}. {topic:20} {bar} ({count})")

        print()
        print("  SENTIMENT:")

        emojis = {"positive": "💚", "negative": "❤️", "neutral": "🤍", "mixed": "💛"}
        for s in ["positive", "negative", "neutral", "mixed"]:
            c = sentiment_counts.get(s, 0)
            pct = (c / len(results) * 100) if results else 0
            bar = "█" * int(pct / 5)
            print(f"    {emojis[s]} {s:10} {bar} {c} ({pct:.0f}%)")

        print()
        if discovered:
            print("  NEW TOPICS FOUND:")
            for t in discovered:
                print(f"    ✨ {t}")
        else:
            print("  No new topics discovered.")

        print()
        print("  USAGE:")
        print(f"    API calls: {self.count}")
        if self.tokens:
            print(f"    Tokens: {self.tokens:,}")
        if self.latency and self.count:
            print(f"    Avg latency: {self.latency / self.count:.0f}ms")

        print("╚" + "═" * 60 + "╝")
        print()

    def taxonomy_summary(self, initial: list[str], current: list[str]) -> None:
        """Show how the topic list has grown."""
        new = [t for t in current if t not in initial]

        print("TOPIC TAXONOMY:")
        print(f"  Started with {len(initial)} topics")
        for t in initial:
            print(f"    • {t}")

        if new:
            print(f"\n  Discovered {len(new)} new:")
            for t in new:
                print(f"    ✨ {t}")
        else:
            print("\n  No new topics added.")
