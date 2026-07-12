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
    }
    market = aliases.get(normalized)
    if market is None:
        raise WorkflowValidationError("This workflow supports VN stocks only")
    return market


def validate_workflow_inputs(
    workflow: WorkflowSpecification,
    inputs: dict[str, object],
) -> ValidatedWorkflowInputs:
    market = parse_market(inputs.get("market"))
    if market not in workflow.market_scope:
        raise WorkflowValidationError(
            "This workflow supports VN stocks only"
        )
    return ValidatedWorkflowInputs(
        market=market,
        symbol=_validate_symbol(workflow, inputs),
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
