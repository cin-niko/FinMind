from api.platform.models import Market, WorkflowSpecification


class WorkflowValidationError(ValueError):
    """Raised when workflow inputs do not satisfy V1 scope or spec rules."""


def parse_market(value: object) -> Market:
    if not isinstance(value, str) or not value:
        raise WorkflowValidationError("market is required")
    normalized = value.strip().upper()
    aliases = {"VN": Market.VN_STOCK, "VN_STOCK": Market.VN_STOCK, "GOLD": Market.GOLD}
    market = aliases.get(normalized)
    if market is None:
        raise WorkflowValidationError("V1 supports VN stocks and gold only")
    return market


def validate_workflow_inputs(
    workflow: WorkflowSpecification,
    inputs: dict[str, object],
) -> Market:
    market = parse_market(inputs.get("market"))
    if market not in workflow.market_scope:
        raise WorkflowValidationError("V1 supports VN stocks and gold only for this workflow")
    return market
