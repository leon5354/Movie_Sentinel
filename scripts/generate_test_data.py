#!/usr/bin/env python3
"""
Generate test data with a hidden topic for testing the sentinel.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import random
from datetime import datetime, timedelta
from faker import Faker

from config import (
    SYNTHETIC_ROW_COUNT,
    HIDDEN_TOPIC_NAME,
    HIDDEN_TOPIC_RATIO,
    COMMENT_COL_NAME,
    DATE_COL_NAME,
    ID_COL_NAME,
    MASTER_TOPICS,
)


fake = Faker()
Faker.seed(42)
random.seed(42)


# templates for each movie review topic
TEMPLATES = {
    "Acting Performance": [
        "The lead actor gave a phenomenal performance!",
        "Terrible acting, completely took me out of the movie.",
        "The cast chemistry was amazing.",
        "Overacted and melodramatic, hard to watch.",
        "Best performance I've seen this year.",
        "The supporting cast stole every scene.",
        "Wooden delivery, no emotional depth.",
        "Incredible range from the main character.",
    ],
    "Plot & Story": [
        "The story was gripping from start to finish.",
        "Predictable plot with no surprises.",
        "Twist ending completely caught me off guard!",
        "The narrative was all over the place.",
        "Beautifully written story with great pacing.",
        "Boring and forgettable storyline.",
        "Complex but rewarding plot.",
        "Full of plot holes and inconsistencies.",
    ],
    "Visual Effects": [
        "The CGI was absolutely stunning.",
        "Cheap-looking effects ruined the immersion.",
        "Visually breathtaking, a feast for the eyes.",
        "The effects looked dated and unconvincing.",
        "Practical effects blended perfectly with CGI.",
        "Over-reliance on green screen made it feel fake.",
        "The action sequences were visually spectacular.",
        "Subpar visual effects for a big budget film.",
    ],
    "Cinematography": [
        "Beautifully shot, every frame was a painting.",
        "Shaky cam made it unwatchable.",
        "The lighting and composition were masterful.",
        "Dull and uninspired cinematography.",
        "Creative camera work added to the tension.",
        "Too many close-ups, disorienting.",
        "The color grading was gorgeous.",
        "Looked like a TV movie, not a theatrical release.",
    ],
    "Soundtrack & Score": [
        "The score elevated every scene.",
        "Forgettable music that added nothing.",
        "The soundtrack was perfectly matched to the mood.",
        "Too loud and distracting.",
        "I've been listening to the score on repeat!",
        "Generic background music, nothing memorable.",
        "The main theme gave me chills.",
        "Poor audio mixing made dialogue hard to hear.",
    ],
    "Direction": [
        "The director's vision was clear and compelling.",
        "Felt like no one was in charge of this mess.",
        "Masterful direction, every scene had purpose.",
        "The pacing was all wrong.",
        "You can feel the director's passion in every frame.",
        "Lazy direction, phoned-in execution.",
        "Bold creative choices that paid off.",
        "The tone was inconsistent throughout.",
    ],
    "Dialogue": [
        "Sharp, witty dialogue throughout.",
        "Cringey one-liners ruined serious moments.",
        "Natural and believable conversations.",
        "Exposition-heavy dialogue was painful.",
        "Memorable quotes that'll stick with me.",
        "Stiff and unnatural line delivery.",
        "The banter between characters was perfect.",
        "Dialogue felt like it was written by AI.",
    ],
    # hidden topic - this is the sentinel trap
    "Pacing Issues": [
        "The movie dragged on forever in the middle.",
        "Way too slow, I almost fell asleep.",
        "First hour was great, then it lost all momentum.",
        "Needed at least 30 minutes cut from runtime.",
        "Rushed ending after a painfully slow buildup.",
        "The second act was a snoozefest.",
        "Pacing was all over the place.",
        "Could have been great as a 90-minute film.",
        "Felt like it would never end.",
        "Slow burn that never ignited.",
    ],
}


def _make_review(topic: str) -> str:
    """Generate a review for the topic."""
    templates = TEMPLATES.get(topic, ["General movie review."])
    base = random.choice(templates)

    # add some variety
    options = [
        base,
        f"{base} {fake.sentence()}",
        f"{fake.sentence()} {base.lower()}",
        base + " " + random.choice(["Highly recommend!", "Skip this one.", "Overall okay.", ""]),
    ]
    return random.choice(options)


def _make_date(days_back: int = 90) -> str:
    """Random date in the past N days."""
    end = datetime.now()
    start = end - timedelta(days=days_back)
    d = start + timedelta(days=random.randint(0, days_back))
    return d.strftime("%Y-%m-%d")


def generate_synthetic_data(
    num_rows: int = SYNTHETIC_ROW_COUNT,
    hidden_ratio: float = HIDDEN_TOPIC_RATIO,
    output_path: str = "data/movie_reviews.csv",
) -> pd.DataFrame:
    """
    Generate test movie review data.

    hidden_ratio: fraction of rows about the hidden topic
    """
    hidden_count = int(num_rows * hidden_ratio)
    regular_count = num_rows - hidden_count

    # exclude hidden topic from regular pool
    regular_topics = [t for t in MASTER_TOPICS if t != HIDDEN_TOPIC_NAME]

    data = []

    # regular reviews
    for i in range(regular_count):
        topic = random.choice(regular_topics)
        data.append({
            ID_COL_NAME: f"REV-{1000 + i:05d}",
            DATE_COL_NAME: _make_date(),
            COMMENT_COL_NAME: _make_review(topic),
        })

    # hidden topic reviews (the trap)
    for i in range(hidden_count):
        data.append({
            ID_COL_NAME: f"REV-{1000 + regular_count + i:05d}",
            DATE_COL_NAME: _make_date(),
            COMMENT_COL_NAME: _make_review(HIDDEN_TOPIC_NAME),
        })

    random.shuffle(data)

    df = pd.DataFrame(data)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"Generated {num_rows} rows")
    print(f"  Saved to: {output_path}")
    print(f"  Hidden topic '{HIDDEN_TOPIC_NAME}': {hidden_count} rows ({hidden_ratio*100:.0f}%)")
    print(f"  Regular topics: {regular_count} rows")

    return df


if __name__ == "__main__":
    print("Movie_Sentinel - Test Data Generator")
    print("=" * 40)

    df = generate_synthetic_data()

    print("\nSample:")
    print(df.head(10).to_string())
