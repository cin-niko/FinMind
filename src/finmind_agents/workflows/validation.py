from dataclasses import dataclass

from finmind_agents.models import Market, WorkflowSpecification


class WorkflowValidationError(ValueError):
    """Raised when workflow inputs do not satisfy V1 scope or spec rules."""


@dataclass(frozen=True)
class ValidatedWorkflowInputs:
    market: Market
    symbol: str | None = None


def parse_market(value: object) -> Market:
    if not isinstance(value, str) or not value:
        raise WorkflowValidationError("market is required")
    normalized = value.strip().upper()
    aliases = {
        "VN": Market.VN_STOCK,
        "VN_STOCK": Market.VN_STOCK,
        "GOLD": Market.GOLD,
    }
    market = aliases.get(normalized)
    if market is None:
        raise WorkflowValidationError("This workflow supports VN stocks or Gold only")
    return market


def validate_workflow_inputs(
    workflow: WorkflowSpecification,
    inputs: dict[str, object],
) -> ValidatedWorkflowInputs:
    market = parse_market(inputs.get("market"))
    if market not in workflow.market_scope:
        raise WorkflowValidationError(
            "This workflow does not support the selected market"
        )
    if market is Market.GOLD and "symbol" in inputs:
        supplied = inputs.get("symbol")
        if supplied not in (None, "", "XAUUSD"):
            raise WorkflowValidationError("Gold workflows only support XAUUSD")
    validated_symbol = _validate_symbol(workflow, inputs)
    if market is Market.GOLD and validated_symbol not in {None, "XAUUSD"}:
        raise WorkflowValidationError("Gold workflows only support XAUUSD")
    return ValidatedWorkflowInputs(
        market=market,
        symbol=validated_symbol or ("XAUUSD" if market is Market.GOLD else None),
    )


def _validate_symbol(
    workflow: WorkflowSpecification,
    inputs: dict[str, object],
) -> str | None:
    symbol_input = next(
        (
            item
            for item in workflow.required_inputs
            if item.get("name") == "symbol"
        ),
        None,
    )
    if symbol_input is None:
        return None

    value = inputs.get("symbol")
    if not isinstance(value, str) or not value.strip():
        if symbol_input.get("required"):
            raise WorkflowValidationError("symbol is required")
        return None
    return value.strip().upper()
