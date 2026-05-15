"""
Thin LLM client over OpenAI-compatible chat completions.

Heterogeneous by design: planner/reviewer use Xiaomi MiMo, coder uses
Featherless's Qwen2.5-Coder. Each agent picks the LLM that fits its role.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


MOCK_RESPONSES: dict[str, str] = {
    "planner": "1. Read settings page\n2. Add toggle component\n3. Wire theme state",
    "coder": "diff --git a/Settings.tsx b/Settings.tsx\n+<DarkModeToggle />",
    "reviewer": "LGTM. Consider extracting useTheme() hook.",
}


@dataclass
class LLM:
    name: str
    base_url: str
    model: str
    api_key: str | None
    role: str

    def chat(self, messages: list[dict[str, str]], *, temperature: float = 0.2) -> str:
        if not self.api_key:
            return MOCK_RESPONSES[self.role]
        with httpx.Client(timeout=60.0, trust_env=False) as client:
            r = client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                },
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]


def get_planner_llm() -> LLM:
    return LLM(
        name="mimo",
        base_url=os.getenv("MIMO_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1"),
        model=os.getenv("MIMO_MODEL", "mimo-v2.5"),
        api_key=os.getenv("MIMO_API_KEY"),
        role="planner",
    )


def get_reviewer_llm() -> LLM:
    return LLM(
        name="mimo",
        base_url=os.getenv("MIMO_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1"),
        model=os.getenv("MIMO_MODEL", "mimo-v2.5"),
        api_key=os.getenv("MIMO_API_KEY"),
        role="reviewer",
    )


def get_coder_llm() -> LLM:
    # Until Featherless promo code lands at hackathon kickoff (May 13),
    # fall back to mimo so the coder runs against a real LLM. Filling
    # FEATHERLESS_API_KEY in .env transparently switches it over.
    fl_key = os.getenv("FEATHERLESS_API_KEY")
    if not fl_key:
        return LLM(
            name="mimo (coder fallback)",
            base_url=os.getenv("MIMO_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1"),
            model=os.getenv("MIMO_MODEL", "mimo-v2.5"),
            api_key=os.getenv("MIMO_API_KEY"),
            role="coder",
        )
    return LLM(
        name="featherless",
        base_url=os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1"),
        model=os.getenv("FEATHERLESS_MODEL", "Qwen/Qwen2.5-Coder-32B-Instruct"),
        api_key=fl_key,
        role="coder",
    )
