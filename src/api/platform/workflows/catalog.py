from api.platform.models import Market, WorkflowSpecification


def build_workflow_catalog() -> list[WorkflowSpecification]:
    return [
        WorkflowSpecification(
            workflow_id="daily-market-brief",
            title="Daily Market Brief",
            market_scope=(Market.VN_STOCK, Market.GOLD),
            required_inputs=({"name": "market", "type": "string", "required": True},),
            stages=("technical", "macro", "risk"),
            role_agents=("technical", "macro", "risk"),
            output_sections=("Market Snapshot", "Risk Notes"),
            citation_policy="material_claims_require_citations",
            chart_requirements=("price_snapshot",),
        ),
        WorkflowSpecification(
            workflow_id="vn-single-symbol-research",
            title="VN Single-Symbol Research",
            market_scope=(Market.VN_STOCK,),
            required_inputs=(
                {"name": "market", "type": "string", "required": True},
                {"name": "symbol", "type": "string", "required": False},
            ),
            stages=("fundamental", "technical", "risk"),
            role_agents=("fundamental", "technical", "risk"),
            output_sections=("Symbol Snapshot", "Risk Notes"),
            citation_policy="material_claims_require_citations",
            chart_requirements=("price_snapshot",),
        ),
        WorkflowSpecification(
            workflow_id="gold-brief",
            title="Gold Brief",
            market_scope=(Market.GOLD,),
            required_inputs=({"name": "market", "type": "string", "required": True},),
            stages=("macro", "technical", "risk"),
            role_agents=("macro", "technical", "risk"),
            output_sections=("Gold Snapshot", "Risk Notes"),
            citation_policy="material_claims_require_citations",
            chart_requirements=("price_snapshot",),
        ),
    ]
