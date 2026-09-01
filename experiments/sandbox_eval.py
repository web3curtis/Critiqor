"""Minimal sandbox experiment for validating Critiqor end to end."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from critiqor import Critiqor


class DemoAgent:
    def __init__(self, model: str) -> None:
        self.model = model

    def run(self, prompt: str) -> str:
        if "Hallucination:" in prompt:
            return (
                "Hallucination: 82\n"
                "Reasoning: 78\n"
                "Tool Reliability: 76\n"
                "Consistency: 84\n"
                "Task Completion: 80\n"
                "Confidence Calibration: 74\n"
                "Execution Efficiency: 79\n"
                "Evidence Level: response_only\n"
                "Summary: Mostly reliable, but command and tool-use details should be verified.\n"
                "Findings:\n"
                "- The answer is useful but makes a few assumptions about the agent environment."
            )

        return (
            "Critiqor evaluates an agent response against observable evidence "
            "and returns structured scoring for agent-specific risks."
        )


def main() -> None:
    verified_agent = Critiqor(DemoAgent(model="llama3.2"))
    result = verified_agent.run("Explain Critiqor in one sentence.")

    print("answer:", result.answer)
    print("confidence:", result.confidence)
    print("evaluation_confidence:", result.evaluation_confidence)
    print("deployment_recommendation:", result.deployment_recommendation)
    print("failure_causes:", result.failure_causes)
    print("trust_level:", result.trust_level)
    print("critique:", result.critique)


if __name__ == "__main__":
    main()
