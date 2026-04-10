import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.agent import Agent
from src.csv_manager import read_pending, update_record
from src.llm_client import LLMClient
from src.scanner import scan
from src.tools import init_tools

load_dotenv()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan a directory, analyze files with an LLM agent, and output a CSV with results."
    )
    parser.add_argument("path", type=Path, help="Root directory to scan")
    parser.add_argument(
        "--output", "-o", type=Path, default=Path("result.csv"),
        help="Output CSV file path (default: result.csv)"
    )
    parser.add_argument(
        "--lm-url", default=os.getenv("LLM_BASE_URL", "http://127.0.0.1:1234/v1"),
        help="LM Studio API base URL"
    )
    parser.add_argument(
        "--model", default=os.getenv("LLM_MODEL", "glm-4.7-flash"),
        help="Model name as shown in LM Studio"
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

    # Step 1: Scan directory and create/update CSV
    print(f"Scanning: {root}")
    all_records = scan(root, args.output)
    pending = [r for r in all_records if r.status == "NEW"]
    total = len(all_records)
    print(f"Found {total} files ({len(pending)} pending analysis)")

    if not pending:
        print("Nothing to process.")
        return

    # Step 2: Initialize LLM and agent
    llm = LLMClient(base_url=args.lm_url, model=args.model)
    init_tools(llm)
    agent = Agent(llm)

    # Step 3: Process each pending file
    for i, record in enumerate(pending, 1):
        print(f"  [{i}/{len(pending)}] {record.name}", end=" ... ", flush=True)

        try:
            result = agent.process(record)
        except KeyboardInterrupt:
            print("\nInterrupted. Progress saved.")
            sys.exit(0)
        except Exception as e:
            record.status = "FAILED"
            record.error = str(e)
            result = record

        update_record(args.output, result)

        if result.status == "DONE":
            print(f"{result.category} -> {result.suggested_name}")
        else:
            print(f"FAILED: {result.error}")

    done = sum(1 for r in all_records if r.status != "NEW" or r in pending)
    print(f"\nDone. Results saved to: {args.output}")


if __name__ == "__main__":
    main()
