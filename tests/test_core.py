"""Stdlib tests for the minimal Aegis wrapper."""

from __future__ import annotations

import unittest

from aegis import Aegis


class RunAgent:
    def run(self, prompt: str) -> str:
        if "Confidence:" in prompt:
            return "Confidence: 92\nCritique: Clear, supported answer with no visible issues."
        return "Paris is the capital of France."


class InvokeAgent:
    def invoke(self, prompt: str) -> dict[str, str]:
        if "Confidence:" in prompt:
            return {
                "text": "Confidence: 68\nCritique: Useful, but it makes a couple of unsupported assumptions."
            }
        return {"text": "This is an answer from invoke()."}


class UnstructuredCritiqueAgent:
    def run(self, prompt: str) -> str:
        if "Confidence:" in prompt:
            return "81 Clear overall, but slightly vague in one place."
        return "An otherwise decent answer."


class UnsupportedAgent:
    pass


class AegisTests(unittest.TestCase):
    def test_run_returns_structured_result(self) -> None:
        result = Aegis(RunAgent()).run("What is the capital of France?")

        self.assertEqual(result.answer, "Paris is the capital of France.")
        self.assertEqual(result.confidence, 92)
        self.assertEqual(
            result.critique,
            "Clear, supported answer with no visible issues.",
        )

    def test_invoke_agents_are_supported(self) -> None:
        result = Aegis(InvokeAgent()).run("Say something helpful.")

        self.assertEqual(result.answer, "This is an answer from invoke().")
        self.assertEqual(result.confidence, 68)
        self.assertEqual(
            result.critique,
            "Useful, but it makes a couple of unsupported assumptions.",
        )

    def test_unstructured_critique_still_parses(self) -> None:
        result = Aegis(UnstructuredCritiqueAgent()).run("Try a fuzzy task.")

        self.assertEqual(result.confidence, 81)
        self.assertEqual(
            result.critique,
            "81 Clear overall, but slightly vague in one place.",
        )

    def test_unsupported_agents_raise_a_clear_error(self) -> None:
        with self.assertRaises(TypeError):
            Aegis(UnsupportedAgent()).run("Hello")


if __name__ == "__main__":
    unittest.main()
