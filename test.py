from __future__ import annotations

import argparse
from collections.abc import Callable, Iterator
from contextlib import contextmanager
import json
import os
import signal
import sys
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

def main() -> int:
    args = parse_args()
    load_dotenv(args.env_file)
    apply_runtime_overrides(args)

    missing = missing_required_env()
    if missing:
        print(f"Missing required env: {', '.join(missing)}", file=sys.stderr)
        print_env_help(file=sys.stderr)
        return 2

    if args.show_env:
        print_env_summary()
        return 0

    try:
        print("Creating FinMind agents workflow service...", flush=True)
        workflow_service = create_workflow_service_from_env()
        print(
            f"Running workflow {args.workflow} for {args.market}:{args.symbol}...",
            flush=True,
        )
        result = run_with_timeout(
            args.timeout,
            lambda: workflow_service.run_workflow(
                workflow_id=args.workflow,
                inputs={"market": args.market, "symbol": args.symbol},
                requested_by="local-smoke-test",
            ),
        )
    except TimeoutError as error:
        print(f"Workflow run timed out after {args.timeout:.0f}s: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Workflow run failed: {type(error).__name__}: {error}", file=sys.stderr)
        return 1

    print_summary(result)
    if args.raw_json:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    if args.export:
        output_path = export_report(result, args.workflow, args.symbol)
        print(f"\nExported report: {output_path}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a local FinMind workflow smoke test using .env.",
    )
    parser.add_argument("--workflow", default="vn-financial-data-collector")
    parser.add_argument("--market", default="VN_STOCK")
    parser.add_argument("--symbol", default="DXG")
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--model", help="Override LITELLM_CHAT_MODEL for this run.")
    parser.add_argument(
        "--export",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Export JSON result to reports/workflows/.",
    )
    parser.add_argument(
        "--raw-json",
        action="store_true",
        help="Print the full workflow JSON response.",
    )
    parser.add_argument(
        "--show-env",
        action="store_true",
        help="Print non-secret runtime configuration and exit.",
    )
    return parser.parse_args()


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), clean_env_value(value))


def clean_env_value(value: str) -> str:
    return value.strip().strip('"').strip("'")


def apply_runtime_overrides(args: argparse.Namespace) -> None:
    if args.model:
        os.environ["LITELLM_CHAT_MODEL"] = args.model


def missing_required_env() -> list[str]:
    required = [
        "LITELLM_CHAT_MODEL",
        "LITELLM_API_KEY",
    ]
    missing: list[str] = []
    for name in required:
        if not os.getenv(name):
            missing.append(name)
    return missing


def print_env_summary() -> None:
    print("Runtime configuration")
    print(f"- LITELLM_CHAT_MODEL: {os.getenv('LITELLM_CHAT_MODEL') or '<missing>'}")
    print(f"- LITELLM_API_KEY set: {bool(os.getenv('LITELLM_API_KEY'))}")
    print(f"- LITELLM_API_BASE: {os.getenv('LITELLM_API_BASE') or '<empty>'}")
    print("- VN data provider: vnstock")
    print(f"- FINMIND_VNSTOCK_API_KEY set: {bool(os.getenv('FINMIND_VNSTOCK_API_KEY'))}")


def print_env_help(file: object) -> None:
    print("\nMinimum .env for this smoke test:", file=file)
    print("LITELLM_CHAT_MODEL=...", file=file)
    print("LITELLM_API_KEY=...", file=file)
    print("LITELLM_API_BASE=...  # optional, for OpenAI-compatible gateways", file=file)
    print("FINMIND_VNSTOCK_API_KEY=...  # if your vnstock account requires it", file=file)


def create_workflow_service_from_env():
    from finmind_agents.dataflows.registry import build_default_provider_registry
    from finmind_agents.dataflows.service import DataflowService
    from finmind_agents.memory import (
        InMemoryMarketDataRepository,
        InMemoryRunRepository,
        create_workflow_catalog,
    )
    from finmind_agents.runtime.service import AgentOrchestrator
    from finmind_agents.workflows.service import WorkflowService

    market_data = InMemoryMarketDataRepository()
    dataflows = DataflowService(
        registry=build_default_provider_registry(
            vn_data_provider="vnstock",
            vnstock_api_key=os.getenv("FINMIND_VNSTOCK_API_KEY", "").strip(),
            fallback_market_data=market_data,
        )
    )
    return WorkflowService(
        workflows=create_workflow_catalog(),
        dataflows=dataflows,
        agent_orchestrator=AgentOrchestrator(),
        runs=InMemoryRunRepository(),
    )


def run_with_timeout[T](timeout_seconds: float, callback: Callable[[], T]) -> T:
    with timeout_after(timeout_seconds):
        return callback()


@contextmanager
def timeout_after(timeout_seconds: float) -> Iterator[None]:
    def handle_timeout(signum: int, frame: object) -> None:
        raise TimeoutError("workflow execution exceeded timeout")

    previous_handler = signal.signal(signal.SIGALRM, handle_timeout)
    signal.setitimer(signal.ITIMER_REAL, timeout_seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


def print_summary(result: dict[str, object]) -> None:
    output = as_dict(result.get("output"))
    collection = as_dict(output.get("collection"))
    quality = as_dict(output.get("quality"))
    agent = as_dict(output.get("agent"))

    print("Workflow run complete")
    print(f"- run_id: {result.get('id')}")
    print(f"- status: {result.get('status')}")
    print(f"- inputs: {result.get('inputs')}")
    print(f"- collection_status: {collection.get('status')}")
    print(f"- requested_dataset_groups: {collection.get('requested_dataset_groups')}")
    print(f"- provider_results: {collection.get('provider_results')}")
    print(f"- quality_status: {quality.get('quality_status')}")
    print(f"- blocked_claims: {quality.get('blocked_claims')}")
    print(f"- agent_status: {agent.get('status')}")
    print(f"- retrieval_plan_status: {agent.get('retrieval_plan_status')}")


def as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def export_report(
    result: dict[str, object],
    workflow: str,
    symbol: str,
) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output_dir = ROOT / "reports" / "workflows"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{timestamp}-{workflow}-{symbol}.json"
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return output_path


if __name__ == "__main__":
    raise SystemExit(main())
