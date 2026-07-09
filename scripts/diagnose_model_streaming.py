#!/usr/bin/env python3
"""Diagnose whether the configured chat model streams answer content
incrementally or emits it as a single chunk.

This isolates the model/adapter from the deep-agent streaming path so you can
tell whether "the final answer arrives as one big chunk" is caused by the
model/provider or by FinMind streaming code. Supports two adapters so you can
compare: `langchain-litellm` (ChatLiteLLM, the FinMind default) and
`langchain-openai` (ChatOpenAI, pointing at the same OpenAI-compatible base URL).

Usage:
    .venv/bin/python scripts/diagnose_model_streaming.py --adapter litellm
    .venv/bin/python scripts/diagnose_model_streaming.py --adapter openai
    .venv/bin/python scripts/diagnose_model_streaming.py --adapter all
    .venv/bin/python scripts/diagnose_model_streaming.py --prompt "Summarize VCB fundamentals in 3 bullets"

Reads LITELLM_CHAT_MODEL / LITELLM_API_KEY / LITELLM_API_BASE from the
environment (or .env). Prints one line per streamed chunk with elapsed time,
content length, and whether the chunk carried reasoning vs answer text, then a
summary per adapter.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import time
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").lstrip()
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(name, value)


def _text_from_content(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                if isinstance(block.get("text"), str):
                    parts.append(block["text"])
                elif isinstance(block.get("thinking"), str):
                    parts.append(block["thinking"])
        return "".join(parts)
    return ""


def _has_reasoning(content: object) -> bool:
    if isinstance(content, list):
        return any(
            isinstance(b, dict) and b.get("type") in ("thinking", "redacted_thinking")
            for b in content
        )
    return False


def build_model(adapter: str, settings: object) -> object:
    """Build a chat model for the requested adapter using the same env settings.

    `production` uses FinMind's `build_chat_model` (the actual runtime choice:
    langchain-openai for OpenAI-compatible endpoints, langchain-litellm
    otherwise). `litellm` and `openai` force a specific adapter for comparison.
    """
    if adapter == "production":
        from finmind_agents.runtime.bootstrap import build_chat_model

        return build_chat_model(settings)

    if adapter == "litellm":
        from langchain_litellm import ChatLiteLLM

        provider_kwargs: dict[str, object] = {}
        if settings.api_base:
            provider_kwargs["custom_llm_provider"] = "openai"
        return ChatLiteLLM(
            model=settings.model,
            api_key=settings.api_key or None,
            api_base=settings.api_base or None,
            temperature=settings.temperature,
            **provider_kwargs,
        )

    if adapter == "openai":
        from langchain_openai import ChatOpenAI

        kwargs: dict[str, object] = {
            "model": settings.model,
            "api_key": settings.api_key or None,
            "streaming": True,
            "temperature": settings.temperature,
        }
        if settings.api_base:
            kwargs["base_url"] = settings.api_base
        return ChatOpenAI(**kwargs)

    raise SystemExit(f"unknown adapter: {adapter}")


async def run_adapter(adapter: str, settings: object, prompt: str) -> None:
    model = build_model(adapter, settings)
    messages = [
        SystemMessage(content="You are a concise financial assistant. Answer in plain text."),
        HumanMessage(content=prompt),
    ]

    print(f"=== adapter={adapter} model={settings.model} api_base={settings.api_base or '(default)'} ===")
    print("streaming chat completion directly (no deep agent, no FinMind code)...")
    print("-" * 60)

    start = time.perf_counter()
    chunk_count = 0
    content_chunks = 0
    reasoning_chunks = 0
    total_text = 0
    first_content_at: float | None = None
    max_chunk = 0

    async for chunk in model.astream(messages):
        chunk_count += 1
        content = getattr(chunk, "content", None)
        text = _text_from_content(content)
        reasoning = _has_reasoning(content)
        if reasoning:
            reasoning_chunks += 1
        if text:
            content_chunks += 1
            if first_content_at is None:
                first_content_at = time.perf_counter() - start
            total_text += len(text)
            max_chunk = max(max_chunk, len(text))
        elapsed = time.perf_counter() - start
        print(
            f"{elapsed:0.3f}s chunk#{chunk_count:03d} "
            f"content_len={len(text):4d} reasoning={'Y' if reasoning else 'N'} "
            f"text={text[:40]!r}"
        )

    print("-" * 60)
    print(f"total_chunks={chunk_count}")
    print(f"content_chunks={content_chunks} reasoning_chunks={reasoning_chunks}")
    print(f"total_answer_text_len={total_text} largest_single_chunk={max_chunk}")
    if first_content_at is not None:
        print(f"first_answer_text_at={first_content_at:0.3f}s")
    if content_chunks <= 1 and total_text > 0:
        print("VERDICT: adapter sees the answer as a SINGLE chunk -> provider is not streaming content incrementally.")
    elif content_chunks > 1:
        print("VERDICT: adapter streams answer text incrementally -> FinMind should stream it token-by-token.")
    else:
        print("VERDICT: no answer text observed (check credentials/model).")
    print()


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", default="Briefly describe VN stock VCB in 50 short sentences.")
    parser.add_argument(
        "--adapter",
        default="production",
        choices=("production", "litellm", "openai", "all"),
        help="Which chat model adapter to test. 'all' runs litellm, openai, and production. Default: %(default)s",
    )
    args = parser.parse_args()

    load_dotenv()
    from finmind_agents.runtime.bootstrap import AgentModelSettings

    settings = AgentModelSettings.from_env()
    if not settings.model:
        raise SystemExit("LITELLM_CHAT_MODEL is not set")

    adapters = ("litellm", "openai", "production") if args.adapter == "all" else (args.adapter,)
    for adapter in adapters:
        await run_adapter(adapter, settings, args.prompt)


if __name__ == "__main__":
    asyncio.run(main())
