import type { Workflow } from "../../api/client";
import { translate, type MessageKey, type UiLanguage } from "../settings/catalog.ts";

export type WorkflowMarket = "VN_STOCK" | "GOLD";

export type WorkflowCatalogSummary = {
  id: string;
  title: string;
  description: string;
  markets: string[];
  requiredInputs: string[];
  stages: string[];
  sections: string[];
  citationLabel: string;
  chartLabel: string;
};

const WORKFLOW_COPY: Record<string, { title: MessageKey; description: MessageKey }> = {
  "vn-financial-data-collector": { title: "workflowCollectorTitle", description: "workflowCollectorDescription" },
  "vn-fundamental-analysis": { title: "workflowFundamentalTitle", description: "workflowFundamentalDescription" },
  "vn-technical-analysis": { title: "workflowTechnicalTitle", description: "workflowTechnicalDescription" }
};

const INPUT_KEYS: Record<string, MessageKey> = {
  market: "inputMarket",
  symbol: "inputSymbol"
};

const STAGE_KEYS: Record<string, MessageKey> = {
  collect_data: "stageCollectData",
  "data-audit": "stageDataAudit",
  "technical-analysis": "stageTechnicalAnalysis",
  "fundamental-analysis": "stageFundamentalAnalysis"
};

const SECTION_KEYS: Record<string, MessageKey> = {
  "Collected Data": "sectionCollectedData",
  "Fundamental Analysis": "sectionFundamentalAnalysis",
  "Technical Analysis": "sectionTechnicalAnalysis"
};

export function marketLabel(market: WorkflowMarket, language: UiLanguage = "en"): string {
  return translate(language, market === "VN_STOCK" ? "marketVnStocks" : "marketGold");
}

export function isSupportedWorkflowMarket(market: string): market is WorkflowMarket {
  return market === "VN_STOCK" || market === "GOLD";
}

export function formatWorkflowMarket(market: string, language: UiLanguage = "en"): string {
  return isSupportedWorkflowMarket(market)
    ? marketLabel(market, language)
    : translate(language, "unsupportedMarket");
}

function localizedToken(value: string, language: UiLanguage): string {
  const exact = INPUT_KEYS[value] ?? STAGE_KEYS[value];
  if (exact) return translate(language, exact);
  const partial = Object.entries(STAGE_KEYS).find(([token]) => value.includes(token));
  return partial ? translate(language, partial[1]) : value;
}

function chartTitle(title: string | undefined, language: UiLanguage): string {
  if (!title) return translate(language, "noChart");
  if (title === "Price trend") return translate(language, "priceTrend");
  if (title === "XAUUSD daily price trend") return translate(language, "goldPriceTrend");
  return title;
}

export function summarizeWorkflow(
  workflow: Workflow,
  language: UiLanguage = "en"
): WorkflowCatalogSummary {
  const copy = WORKFLOW_COPY[workflow.id];
  const title = copy ? translate(language, copy.title) : workflow.title;
  return {
    id: workflow.id,
    title,
    description: copy ? translate(language, copy.description) : workflow.description,
    markets: workflow.market_scope.map((market) => formatWorkflowMarket(market, language)),
    requiredInputs: workflow.required_inputs.map((input) => localizedToken(input.name, language)),
    stages: workflow.stages.map((stage) => localizedToken(stage, language)),
    sections: workflow.output_sections.map((section) => {
      const key = SECTION_KEYS[section];
      return key ? translate(language, key) : section;
    }),
    citationLabel: translate(language, workflow.requires_citations ? "citationsRequired" : "citationsOptional"),
    chartLabel: chartTitle(workflow.chart_requirements[0]?.title, language)
  };
}
