import json
import os
from enum import IntEnum
from typing import Any

from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from .typedefs import Message, StreamEvent


class LogLevel(IntEnum):
    OFF = -1
    ERROR = 0
    INFO = 1
    DEBUG = 2

    @classmethod
    def parse(cls, level: "LogLevel | str | None") -> "LogLevel":
        if level is None:
            return cls.INFO
        if not isinstance(level, str):
            return level
        try:
            return cls[level.upper()]
        except KeyError as exc:
            raise ValueError(f"Invalid log level: {level}") from exc


class RunLogger:
    def __init__(
        self,
        level: LogLevel | str | None = LogLevel.INFO,
        console: Console | None = None,
    ) -> None:
        self.level = LogLevel.parse(level if level is not None else os.getenv("LOG_LEVEL"))
        self.console = console or Console(highlight=False)

    def log(self, *args: object, level: LogLevel = LogLevel.INFO, **kwargs: Any) -> None:
        if level <= self.level:
            self.console.print(*args, **kwargs)

    def log_header(self, title: str, *, level: LogLevel = LogLevel.INFO) -> None:
        self.log(
            Rule(title, characters="─", style="cyan"),
            level=level,
        )

    def log_message(
        self,
        message: Message,
        *,
        title: str | None = None,
        level: LogLevel = LogLevel.INFO,
    ) -> None:
        header = title or message.role.value
        body = Text(message.content or "")
        self.log(
            Panel(
                body,
                title=header,
                title_align="left",
                box=ROUNDED,
            ),
            level=level,
        )

    def log_action(
        self,
        *,
        tool_name: str,
        arguments_json: str,
        level: LogLevel = LogLevel.INFO,
    ) -> None:
        content = Text(f"{tool_name}({arguments_json})")
        self.log(
            Panel(
                content,
                title="action",
                title_align="left",
                box=ROUNDED,
            ),
            level=level,
        )

    def log_finish(self, answer: str, *, level: LogLevel = LogLevel.INFO) -> None:
        content = Text(f"finish({json.dumps(answer)})")
        self.log(
            Panel(
                content,
                title="action",
                title_align="left",
                box=ROUNDED,
            ),
            level=level,
        )

    def log_observation(
        self,
        content: str,
        *,
        level: LogLevel = LogLevel.INFO,
    ) -> None:
        self.log(
            Panel(
                Text(content),
                title="observation",
                title_align="left",
                box=ROUNDED,
            ),
            level=level,
        )

    def log_stream_event(self, event: StreamEvent, *, level: LogLevel = LogLevel.DEBUG) -> None:
        self.log(f"{event.type.value}: {event.model_dump(exclude={'type'})}", level=level)
