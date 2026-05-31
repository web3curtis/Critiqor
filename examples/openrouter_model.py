"""Run Aegis with an OpenRouter text model.

Set OPENROUTER_API_KEY before running, or create a local .env file:

    cp .env.example .env
    # edit .env and replace the placeholder key
    python3 examples/openrouter_model.py
"""

from __future__ import annotations

import os
from pathlib import Path
import sys

from openai import OpenAI
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aegis import Aegis


MODEL = "deepseek/deepseek-v4-flash:free"


class OpenRouterAgent:
    """Small OpenRouter-backed agent compatible with Aegis."""

    def __init__(self, model: str):
        self.model = model
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ["OPENROUTER_API_KEY"],
            default_headers={
                "HTTP-Referer": "https://github.com/web3curtis/aegis",
                "X-Title": "Aegis",
            },
        )

    def run(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content
        return content or ""


def main() -> None:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    if "OPENROUTER_API_KEY" not in os.environ:
        raise SystemExit(
            "Missing OPENROUTER_API_KEY. Copy .env.example to .env and add your key."
        )

    agent = Aegis(OpenRouterAgent(MODEL))
    result = agent.run("Explain what Aegis does in one paragraph.")

    print("Answer:", result.answer)
    print("Confidence:", result.confidence)
    print("Critique:", result.critique)


if __name__ == "__main__":
    main()
