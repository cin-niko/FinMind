from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

_TEMPLATE_ROOT = Path(__file__).resolve().parent.parent / "templates"
_TEMPLATE_ENV = Environment(
    loader=FileSystemLoader(_TEMPLATE_ROOT),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
    undefined=StrictUndefined,
)


def render_record_context(template_name: str | None, context: dict[str, Any]) -> str:
    if template_name is None:
        payload = context.get("payload", {})
        return json.dumps(_display_value(payload), ensure_ascii=True, indent=2, default=str)
    template = _TEMPLATE_ENV.get_template(f"records/{template_name}")
    return template.render(**context).strip()


def _display_value(value: Any) -> Any:
    if value is None:
        return "Unavailable"
    if isinstance(value, dict):
        return {key: _display_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_display_value(item) for item in value]
    return value
