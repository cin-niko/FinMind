export const SUPPORTED_UI_LANGUAGES = ["en", "vi"] as const;
export type UiLanguage = (typeof SUPPORTED_UI_LANGUAGES)[number];
export type LanguageSelection = "auto" | UiLanguage;

export function isUiLanguage(value: unknown): value is UiLanguage {
  return typeof value === "string" && SUPPORTED_UI_LANGUAGES.includes(value as UiLanguage);
}

export function resolveLanguageSelection(
  selection: LanguageSelection,
  browserLanguages: readonly string[]
): UiLanguage {
  if (isUiLanguage(selection)) return selection;
  for (const value of browserLanguages) {
    const primaryLanguage = value.toLowerCase().split("-")[0];
    if (isUiLanguage(primaryLanguage)) return primaryLanguage;
  }
  return "en";
}
