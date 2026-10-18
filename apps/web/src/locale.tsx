import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { en } from "./locales/en";
import { workflow, liveEn } from "./locales/workflow";

export type Locale = "zh" | "en";
export function answerLanguage(text: string, previous: Locale | undefined, fallback: Locale): Locale {
  const directives: { index: number; locale: Locale }[] = [];
  for (const [language, pattern] of [
    ["en", /(?:用|使用|请以|以)\s*(?:英文|英语)|(?:answer|respond|reply|write)\s+(?:only\s+)?in\s+English|English\s+please/gi],
    ["zh", /(?:用|使用|请以|以)\s*中文|(?:answer|respond|reply|write)\s+(?:only\s+)?in\s+Chinese|Chinese\s+please/gi],
  ] as [Locale, RegExp][]) {
    for (const match of text.matchAll(pattern)) directives.push({ index: match.index!, locale: language });
  }
  if (directives.length) return directives.sort((a, b) => b.index - a.index)[0].locale;
  const prose = text.replace(/```[\s\S]*?```|"[^"\n]*"|“[^”]*”/g, "");
  const chinese = (prose.match(/[\u3400-\u9fff]/g) || []).length;
  const words = prose.match(/[A-Za-z]{2,}/g) || [];
  if (!chinese && /^\s*(why|how|what|when|where|who|which|can|could|would|should|is|are|does|do|please|hello|hi)\b/i.test(prose)) return "en";
  if (words.length >= 3 && words.join("").length > chinese * 2) return "en";
  return chinese ? "zh" : previous || fallback;
}
export const languagePreferenceKey = "asiatax.language";
export function translate(text: string, locale: Locale): string {
  if (workflow[text]) return workflow[text][locale === "en" ? 1 : 0];
  return locale === "en" ? (liveEn[text] ?? en[text] ?? text) : text;
}
const LocaleContext = createContext({
  locale: "zh" as Locale,
  setLocale: (_locale: Locale) => {},
  t: (text: string): string => text,
});

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => {
    try {
      return localStorage.getItem(languagePreferenceKey) === "en" ? "en" : "zh";
    } catch {
      return "zh";
    }
  });
  function setLocale(next: Locale) {
    setLocaleState(next);
    try {
      localStorage.setItem(languagePreferenceKey, next);
    } catch {
      /* Private browsing can disallow storage. */
    }
  }
  useEffect(() => {
    document.documentElement.lang = locale === "zh" ? "zh-CN" : "en";
    document.title =
      locale === "zh"
        ? "Taxrora · 税务研究助手"
        : "Taxrora · Tax Research Assistant";
  }, [locale]);
  return (
    <LocaleContext.Provider
      value={{ locale, setLocale, t: (text) => translate(text, locale) }}
    >
      {children}
    </LocaleContext.Provider>
  );
}
export function useLocale() {
  return useContext(LocaleContext);
}
