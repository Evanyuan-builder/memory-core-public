import { create } from "zustand";

type Lang = "en" | "zh";

interface AppState {
  lang: Lang;
  setLang: (l: Lang) => void;
}

export const useApp = create<AppState>((set) => ({
  lang: "en",
  setLang: (lang) => set({ lang }),
}));
