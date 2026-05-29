"""Minimal sandbox experiment for validating Aegis end to end."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aegis import Aegis


class DemoAgent:
    def __init__(self, model: str) -> None:
        self.model = model

    def run(self, prompt: str) -> str:
        if "Confidence:" in prompt:
            return (
                "Confidence: 84\n"
                "Critique: Accurate and clear overall, with a small assumption about "
                "performance that is not explicitly supported."
            )

        return (
            "Aegis wraps an existing agent, asks it for one self-critique, and "
            "returns the original answer with a confidence score."
        )


def main() -> None:
    verified_agent = Aegis(DemoAgent(model="llama3.2"))
    result = verified_agent.run("Explain Aegis in one sentence.")

    print("answer:", result.answer)
    print("confidence:", result.confidence)
    print("critique:", result.critique)


if __name__ == "__main__":
    main()
