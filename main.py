import argparse
import sys
from pathlib import Path

from src.classifier import Classifier
from src.csv_writer import write_csv
from src.scanner import scan


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan a directory, classify files with a local LLM, and output a CSV with proposed changes."
    )
    parser.add_argument("path", type=Path, help="Root directory to scan")
    parser.add_argument(
        "--output", "-o", type=Path, default=Path("result.csv"),
        help="Output CSV file path (default: result.csv)"
    )
    parser.add_argument(
        "--lm-url", default="http://localhost:1234/v1",
        help="LM Studio API base URL (default: http://localhost:1234/v1)"
    )
    parser.add_argument(
        "--model", default="qwen2.5-7b-instruct",
        help="Model name as shown in LM Studio (default: qwen2.5-7b-instruct)"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.path.resolve()

    if not root.exists():
        print(f"Error: path '{root}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if not root.is_dir():
        print(f"Error: path '{root}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning: {root}")
    classifier = Classifier(base_url=args.lm_url, model=args.model)

    results = []
    for file_info in scan(root):
        label = "DIR " if file_info.is_dir else "FILE"
        print(f"  [{label}] {file_info.path.relative_to(root)}", end=" ... ", flush=True)
        result = classifier.classify(file_info, root)
        alt = f" (alt: {result.alternative_category})" if result.alternative_category else ""
        print(f"{result.category} [{result.confidence:.0%}]{alt} → {result.action}")
        results.append(result)

    count = write_csv(results, args.output)
    print(f"\nDone. {count} entries written to: {args.output}")


if __name__ == "__main__":
    main()
