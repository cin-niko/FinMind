import { translate, type MessageKey, type UiLanguage } from "../settings/catalog.ts";

const WORKFLOW_PROMPT_KEYS: Record<string, MessageKey> = {
  "vn-financial-data-collector": "promptCollector",
  "vn-fundamental-analysis": "promptFundamental",
  "vn-technical-analysis": "promptTechnical",
  "vn-news-digest": "promptNews",
  "vn-valuation": "promptValuation",
  "vn-stock-brief": "promptBrief",
  "gold-technical-analysis": "promptGold"
};

export function workflowPromptTemplate(
  workflowId: string,
  language: UiLanguage = "en"
): (symbol: string) => string {
  const key = WORKFLOW_PROMPT_KEYS[workflowId] ?? "promptGenericStock";
  return (symbol) => translate(language, key, { symbol });
}
