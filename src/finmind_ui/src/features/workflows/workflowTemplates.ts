const TEMPLATES: Record<string, (symbol: string) => string> = {
  "vn-financial-data-collector": (s) => `Collect and audit financial data for stock ${s}`,
  "vn-fundamental-analysis": (s) => `Analyze the fundamentals of stock ${s}`,
  "vn-technical-analysis": (s) => `Analyze the technicals of stock ${s}`,
};

export function workflowPromptTemplate(workflowId: string): (symbol: string) => string {
  return TEMPLATES[workflowId] ?? ((s) => `Analyze stock ${s}`);
}


