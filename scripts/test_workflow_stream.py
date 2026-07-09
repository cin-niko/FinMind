#!/usr/bin/env python3
"""Call the workflow SSE endpoint and log stream events with timing.

Usage:
    .venv/bin/python scripts/test_workflow_stream.py \
      --workflow-id vn-financial-data-collector \
      --market VN_STOCK \
      --symbol VCB
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from typing import Any

import httpx


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Call a FinMind workflow stream endpoint and print SSE events.",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="API base URL. Default: %(default)s",
    )
    parser.add_argument(
        "--username",
        default="analyst",
        help="Login username. Default: %(default)s",
    )
    parser.add_argument(
        "--password",
        default="secret-pass",
        help="Login password. Default: %(default)s",
    )
    parser.add_argument(
        "--workflow-id",
        default="vn-financial-data-collector",
        help="Workflow id to run. Default: %(default)s",
    )
    parser.add_argument(
        "--market",
        default="VN_STOCK",
        help="Workflow market input. Default: %(default)s",
    )
    parser.add_argument(
        "--symbol",
        default="VCB",
        help="Workflow symbol input. Default: %(default)s",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print full JSON payloads instead of compact output.",
    )
    return parser


async def login(client: httpx.AsyncClient, base_url: str, username: str, password: str) -> None:
    response = await client.post(
        f"{base_url}/api/login",
        json={"username": username, "password": password},
    )
    response.raise_for_status()


def format_payload(payload: dict[str, Any], pretty: bool) -> str:
    if pretty:
        return json.dumps(payload, ensure_ascii=True, indent=2)

    kind = payload.get("kind")
    event_payload = payload.get("payload")
    if kind == "answer.delta" and isinstance(event_payload, dict):
        text = str(event_payload.get("text", ""))
        return f"text={text!r}"
    if kind == "run.stage" and isinstance(event_payload, dict):
        return (
            "stage="
            f"{event_payload.get('stage')} "
            f"status={event_payload.get('status')} "
            f"kind={event_payload.get('kind')}"
        )
    if kind == "run.started" and isinstance(event_payload, dict):
        return f"workflow_id={event_payload.get('workflow_id')} inputs={event_payload.get('inputs')}"
    if kind == "run.failed" and isinstance(event_payload, dict):
        return f"status={event_payload.get('status')} message={event_payload.get('message')!r}"
    if kind == "run.completed" and isinstance(event_payload, dict):
        return f"status={event_payload.get('status')}"
    if kind == "run.completed" and isinstance(event_payload, dict):
        run = event_payload.get("run")
        if isinstance(run, dict):
            return f"run_id={run.get('id')} status={run.get('status')}"
    return json.dumps(payload, ensure_ascii=True)


async def stream_workflow(
    client: httpx.AsyncClient,
    *,
    base_url: str,
    workflow_id: str,
    market: str,
    symbol: str,
    pretty: bool,
) -> None:
    start = time.perf_counter()
    async with client.stream(
        "POST",
        f"{base_url}/api/workflows/{workflow_id}/runs",
        headers={"Accept": "text/event-stream"},
        json={"market": market, "symbol": symbol},
    ) as response:
        print(f"HTTP {response.status_code} content-type={response.headers.get('content-type')}")
        response.raise_for_status()

        event_name = "message"
        data_lines: list[str] = []
        answer_delta_count = 0
        answer_delta_max = 0
        answer_delta_total = 0
        first_answer_at: float | None = None
        async for raw_line in response.aiter_lines():
            if raw_line == "":
                if data_lines:
                    payload = json.loads("\n".join(data_lines))
                    elapsed = time.perf_counter() - start
                    print(
                        f"{elapsed:0.3f}s {event_name} "
                        f"{format_payload(payload, pretty)}"
                    )
                    if payload.get("kind") == "answer.delta":
                        answer_delta_count += 1
                        text = str(payload.get("payload", {}).get("text", ""))
                        answer_delta_total += len(text)
                        answer_delta_max = max(answer_delta_max, len(text))
                        if first_answer_at is None:
                            first_answer_at = elapsed
                event_name = "message"
                data_lines = []
                continue
            if raw_line.startswith("event:"):
                event_name = raw_line.removeprefix("event:").strip()
                continue
            if raw_line.startswith("data:"):
                data_lines.append(raw_line.removeprefix("data:").strip())
        print("-" * 60)
        print(
            f"answer.delta events={answer_delta_count} "
            f"total_text={answer_delta_total} largest_chunk={answer_delta_max}"
        )
        if first_answer_at is not None:
            print(f"first_answer_delta_at={first_answer_at:0.3f}s")
        if answer_delta_count <= 1 and answer_delta_total > 0:
            print("VERDICT: SSE delivered the answer as ONE chunk (model is not streaming content incrementally).")
        elif answer_delta_count > 1:
            print("VERDICT: SSE delivered answer text incrementally (streaming works).")


async def main() -> None:
    args = build_parser().parse_args()
    timeout = httpx.Timeout(connect=10.0, read=None, write=10.0, pool=10.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        await login(client, args.base_url, args.username, args.password)
        await stream_workflow(
            client,
            base_url=args.base_url,
            workflow_id=args.workflow_id,
            market=args.market,
            symbol=args.symbol,
            pretty=args.pretty,
        )


if __name__ == "__main__":
    asyncio.run(main())
