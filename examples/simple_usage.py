"""Simple Critiqor usage example."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from critiqor import Critiqor


class TheirExistingAgent:
    """Tiny stand-in for an Ollama, LangChain, or custom agent."""

    def __init__(self, model: str):
        self.model = model

    def run(self, prompt: str) -> str:
        if "Hallucination:" in prompt:
            return (
                "Hallucination: 88\n"
                "Reasoning: 84\n"
                "Tool Reliability: 90\n"
                "Consistency: 86\n"
                "Task Completion: 82\n"
                "Confidence Calibration: 80\n"
                "Execution Efficiency: 92\n"
                "Evidence Level: response_only\n"
                "Summary: Reliable overall, with minor assumptions that are not fully supported.\n"
                "Findings:\n"
                "- The answer is clear but lightly underspecified."
            )

        return "Critiqor adds one agent-focused reliability critique step."


base_agent = TheirExistingAgent(model="llama3.2")

verified_agent = Critiqor(base_agent)

result = verified_agent.run("What does Critiqor do?")

print(result.answer)
print(result.confidence)
print(result.evaluation_confidence)
print(result.deployment_recommendation)
print(result.trust_level)
print(result.critique.evidence_level)
print(result.failure_causes)
print(result.critique)
