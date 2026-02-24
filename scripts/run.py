#!/usr/bin/env python3
"""
Main entry point for Movie_Sentinel.
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from tqdm import tqdm

from config import (
    INPUT_FILE_PATH,
    COMMENT_COL_NAME,
    MASTER_TOPICS,
    validate_config,
)
from src.classifier import ReviewClassifier
from src.sentinel import Sentinel
from src.reporter import Reporter
from src.llm_wrapper import provider_info


def main():
    parser = argparse.ArgumentParser(description="Movie_Sentinel - Movie Review Topic Segmentation")
    parser.add_argument("--input", "-i", default=INPUT_FILE_PATH, help="Input CSV file")
    parser.add_argument("--review-col", "-c", default=COMMENT_COL_NAME, help="Review column name")
    parser.add_argument("--generate", "-g", action="store_true", help="Generate test data first")
    parser.add_argument("--limit", "-l", type=int, default=None, help="Max rows to process")

    args = parser.parse_args()

    print("\n🎬 MOVIE_SENTINEL")
    print("=" * 50)

    # config check
    try:
        validate_config()
    except ValueError as e:
        print(f"Config error: {e}")
        sys.exit(1)

    # provider info
    info = provider_info()
    print(f"\nProvider: {info['provider']}")
    print(f"Model: {info['model']}")

    # generate if needed
    if args.generate:
        print("\nGenerating test data...")
        from scripts.generate_test_data import generate_synthetic_data
        generate_synthetic_data(output_path=args.input)

    # load input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input not found: {input_path}")
        print("Run with --generate to create test data")
        sys.exit(1)

    print(f"\nLoading: {input_path}")
    df = pd.read_csv(input_path)
    print(f"Rows: {len(df)}")

    if args.review_col not in df.columns:
        print(f"Column '{args.review_col}' not found")
        print(f"Available: {list(df.columns)}")
        sys.exit(1)

    if args.limit:
        df = df.head(args.limit)
        print(f"Limited to: {len(df)}")

    # init components
    initial_topics = MASTER_TOPICS.copy()
    classifier = ReviewClassifier(topics=initial_topics)
    sentinel = Sentinel()
    reporter = Reporter()

    # results storage
    results = []

    print(f"\nProcessing {len(df)} reviews...")

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Classifying"):
        review = str(row[args.review_col])

        result = classifier.classify(review, idx=idx)

        # check for new topic
        discovery_source = False
        if result.suggested_label and "UNCATEGORIZED" in result.labels:
            confirmed = sentinel.observe(
                suggested=result.suggested_label,
                review=review,
                idx=idx,
                reason=result.suggestion_reason,
            )

            if confirmed:
                # promote the topic
                classifier.add_topic(result.suggested_label)

                # re-tag all the placeholder rows
                for row_idx in sentinel.get_candidate_indices(result.suggested_label):
                    if row_idx < len(results):
                        old_labels = results[row_idx]["labels"]
                        new_labels = [l if l != "UNCATEGORIZED" else result.suggested_label.title()
                                      for l in old_labels]
                        results[row_idx]["labels"] = new_labels
                        results[row_idx]["discovery_source"] = True

                discovery_source = True

        results.append({
            "labels": result.labels,
            "sentiment": result.sentiment,
            "confidence": result.confidence,
            "suggested_label": result.suggested_label if "UNCATEGORIZED" in result.labels else None,
            "discovery_source": discovery_source,
        })

    # sentinel status
    print("\n" + sentinel.status())

    # export
    output_path = reporter.export(df, results)
    print(f"\nSaved to: {output_path}")

    # dashboard
    reporter.dashboard(
        results=results,
        discovered=sentinel.get_confirmed(),
        current_topics=classifier.get_topics(),
    )

    reporter.taxonomy_summary(initial_topics, classifier.get_topics())

    print("Done.\n")


if __name__ == "__main__":
    main()
