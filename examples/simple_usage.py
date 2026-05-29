"""Simple Aegis usage example."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aegis import Aegis


class TheirExistingAgent:
    """Tiny stand-in for an Ollama, LangChain, or custom agent."""

    def __init__(self, model: str):
        self.model = model

    def run(self, prompt: str) -> str:
        if "Confidence:" in prompt:
            return (
                "Confidence: 86\n"
                "Critique: Clear and useful overall, with minor assumptions that "
                "are not fully supported by evidence."
            )

        return "Aegis adds one self-critique step and returns a confidence score."


base_agent = TheirExistingAgent(model="llama3.2")

verified_agent = Aegis(base_agent)

result = verified_agent.run("What does Aegis do?")

print(result.answer)
print(result.confidence)
print(result.critique)
