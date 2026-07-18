import { createContext, useContext, type ReactNode } from "react";
import { translate, type MessageKey, type UiLanguage } from "./catalog";

export * from "./catalog";

type MessageParams = Record<string, string | number>;
const I18nContext = createContext<UiLanguage>("en");

export function I18nProvider({ language, children }: { language: UiLanguage; children: ReactNode }) {
  return <I18nContext.Provider value={language}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const language = useContext(I18nContext);
  return {
    language,
    t: (key: MessageKey, params: MessageParams = {}) => translate(language, key, params)
  };
}
