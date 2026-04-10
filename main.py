import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan a directory, analyze files with an LLM agent, and output results."
    )
    parser.add_argument("path", type=Path, nargs="?", help="Root directory to scan (required in CLI mode)")
    parser.add_argument(
        "--cli", action="store_true",
        help="Run in CLI mode instead of GUI"
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


def run_cli(args: argparse.Namespace) -> None:
    from src.agent import Agent
    from src.db_manager import get_pending, update_record
    from src.llm_client import LLMClient
    from src.scanner import scan
    from src.tools import init_tools

    root = args.path.resolve()

    if not root.exists():
        print(f"Error: path '{root}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if not root.is_dir():
        print(f"Error: path '{root}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning: {root}")
    new_records = scan(root)
    pending = get_pending()
    print(f"Found {len(new_records)} new files ({len(pending)} pending analysis)")

    if not pending:
        print("Nothing to process.")
        return

    llm = LLMClient(base_url=args.lm_url, model=args.model)
    init_tools(llm)
    agent = Agent(llm)

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

        update_record(result)

        if result.status == "DONE":
            print(f"{result.category} -> {result.suggested_name}")
        else:
            print(f"FAILED: {result.error}")

    print(f"\nDone. Results saved to: ~/.aifilemanager/files.db")


def run_gui() -> None:
    from src.gui.app import App

    app = App()
    sys.exit(app.run())


def main() -> None:
    args = parse_args()

    if args.cli:
        if not args.path:
            print("Error: path is required in CLI mode.", file=sys.stderr)
            sys.exit(1)
        run_cli(args)
    else:
        run_gui()


if __name__ == "__main__":
    main()
