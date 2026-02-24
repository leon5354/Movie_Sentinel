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


# templates for each topic - movie review themed
TEMPLATES = {
    "Acting Performance": [
        "The lead actor delivered an incredible performance.",
        "Terrible acting, completely took me out of the movie.",
        "The cast was perfectly chosen, everyone fit their role.",
        "Overacting ruined several key scenes.",
        "Best performance I've seen all year!",
        "The supporting cast outshined the leads.",
        "Wooden dialogue delivery made it painful to watch.",
        "Method acting at its finest.",
    ],
    "Plot & Story": [
        "The story kept me on the edge of my seat.",
        "Predictable plot twists, saw everything coming.",
        "A masterpiece of storytelling.",
        "The narrative was all over the place.",
        "Original and refreshing storyline.",
        "Full of plot holes you could drive a truck through.",
        "Emotional and gripping from start to finish.",
        "Boring and derivative, nothing new here.",
    ],
    "Visual Effects": [
        "The CGI was absolutely stunning.",
        "Cheap-looking effects broke the immersion.",
        "Visually breathtaking, every frame is art.",
        "The green screen work was obvious and distracting.",
        "Practical effects blended seamlessly with CGI.",
        "Video game quality graphics, disappointing.",
        "The action sequences were visually spectacular.",
        "Over-reliance on CGI ruined the authenticity.",
    ],
    "Cinematography": [
        "Beautifully shot, every scene was gorgeous.",
        "Shaky cam made several scenes unwatchable.",
        "The lighting and framing were masterful.",
        "Bland and uninspired camera work.",
        "Some of the best cinematography this decade.",
        "Too many close-ups, disorienting at times.",
        "The color palette perfectly matched the mood.",
        "Amateurish camera angles throughout.",
    ],
    "Soundtrack & Score": [
        "The score elevated every scene perfectly.",
        "Forgettable music that added nothing.",
        "I've been listening to the soundtrack on repeat!",
        "The music was distracting and overpowering.",
        "Haunting and beautiful orchestral pieces.",
        "Generic background noise, nothing memorable.",
        "The song choices were spot on.",
        "Jarring musical choices that didn't fit.",
    ],
    "Direction": [
        "The director's vision clearly shines through.",
        "A muddled mess with no clear direction.",
        "Masterful pacing and scene composition.",
        "The director lost control of the tone.",
        "Every frame shows the director's careful attention.",
        "Feels like the director didn't know the genre.",
        "Bold and innovative directorial choices.",
        "Safe and boring, played it too safe.",
    ],
    "Dialogue": [
        "Sharp and witty dialogue throughout.",
        "Cringe-worthy one-liners ruined key moments.",
        "The script is quotable and memorable.",
        "Unnatural and forced conversations.",
        "Intelligent and thought-provoking lines.",
        "Exposition-heavy dialogue slowed everything down.",
        "The banter between characters was perfect.",
        "Clunky dialogue that no real person would say.",
    ],
    # hidden topic - this is the sentinel trap
    "Pacing Issues": [
        "The movie dragged on forever in the middle.",
        "Way too long, should have been 30 minutes shorter.",
        "The pacing was all wrong, slow then rushed.",
        "Boring stretches that killed the momentum.",
        "The first act took forever to get going.",
        "Felt like a 2-hour movie stretched to 3.",
        "Uneven pacing made it hard to stay engaged.",
        "The runtime felt twice as long as it was.",
        "Editing was poor, too many slow scenes.",
        "Lost interest during the slow parts.",
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
        base + " " + random.choice(["Highly recommended!", "Skip this one.", "5/10.", ""]),
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
    Generate test review data.

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
