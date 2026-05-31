"""Core Aegis evaluator wrapper implementation."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class RunnableAgent(Protocol):
    """Protocol for agents that expose a run method."""

    def run(self, prompt: str, *args: Any, **kwargs: Any) -> Any:
        """Run the agent for a prompt."""


@dataclass(frozen=True)
class AegisResult:
    """The result returned by Aegis.

    Attributes:
        answer: The original answer from the wrapped agent.
        confidence: An integer confidence score from 0 to 100.
        critique: A short explanation of the confidence score.
    """

    answer: str
    confidence: int
    critique: str


class Aegis:
    """A minimal evaluator wrapper for existing AI agents.

    Aegis calls the wrapped agent once to answer the user's prompt, then calls it
    once more to produce a short critique and confidence score.
    """

    def __init__(self, agent: Any):
        """Create an Aegis wrapper.

        Args:
            agent: Any object that can be called via ``run(prompt)``,
                ``invoke(prompt)``, ``generate(prompt)``, or ``agent(prompt)``.
        """

        self.agent = agent

    def run(self, prompt: str, *args: Any, **kwargs: Any) -> AegisResult:
        """Run the wrapped agent and return an answer with self-verification.

        Args:
            prompt: The user's prompt.
            *args: Extra positional arguments forwarded to the base agent for
                the answer-generation call.
            **kwargs: Extra keyword arguments forwarded to the base agent for
                the answer-generation call.

        Returns:
            AegisResult containing the answer, confidence score, and critique.
        """

        raw_answer = self._call_agent(prompt, *args, **kwargs)
        answer = self._extract_text(raw_answer)

        critique_prompt = self._build_critique_prompt(prompt, answer)
        raw_critique = self._call_agent(critique_prompt)
        critique_text = self._extract_text(raw_critique)

        confidence = self._parse_confidence(critique_text)
        critique = self._parse_critique(critique_text)

        return AegisResult(
            answer=answer,
            confidence=confidence,
            critique=critique,
        )

    def _call_agent(self, prompt: str, *args: Any, **kwargs: Any) -> Any:
        """Call a broad range of common agent interfaces."""

        if hasattr(self.agent, "run"):
            return self.agent.run(prompt, *args, **kwargs)
        if hasattr(self.agent, "invoke"):
            return self.agent.invoke(prompt, *args, **kwargs)
        if hasattr(self.agent, "generate"):
            return self.agent.generate(prompt, *args, **kwargs)
        if callable(self.agent):
            return self.agent(prompt, *args, **kwargs)

        raise TypeError(
            "Aegis requires an agent with run(), invoke(), generate(), or __call__()."
        )

    @staticmethod
    def _extract_text(value: Any) -> str:
        """Extract text from common agent response shapes."""

        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()

        for attribute in ("content", "text", "answer", "output"):
            if hasattr(value, attribute):
                return str(getattr(value, attribute)).strip()

        if isinstance(value, dict):
            for key in ("content", "text", "answer", "output", "response"):
                if key in value:
                    return str(value[key]).strip()

        return str(value).strip()

    @staticmethod
    def _build_critique_prompt(prompt: str, answer: str) -> str:
        """Build the single evaluator prompt used by Aegis V1."""

        return f"""You are Aegis, a lightweight evaluator wrapper for AI agents.

Review the answer below against the user's prompt. Give a confidence score from
0 to 100 using this exact scale:

90-100: Very High - No issues, clear, well-supported answer
75-89: High - Minor issues only, such as small assumptions or vagueness
60-74: Moderate - Some problems, such as partial hallucination or logical gaps
40-59: Low - Significant problems, such as multiple hallucinations or contradictions
0-39: Very Low - Major failures, such as strong hallucinations, task failure, or tool misuse

Return only this format:
Confidence: <integer 0-100>
Critique: <one short, clear explanation>

User prompt:
{prompt}

Answer:
{answer}
"""

    @staticmethod
    def _parse_confidence(critique_text: str) -> int:
        """Parse and clamp the confidence score from critique text."""

        confidence_match = re.search(
            r"confidence\s*:\s*(\d{1,3})", critique_text, re.IGNORECASE
        )
        if confidence_match:
            return _clamp_score(int(confidence_match.group(1)))

        first_number = re.search(r"\b(\d{1,3})\b", critique_text)
        if first_number:
            return _clamp_score(int(first_number.group(1)))

        return 50

    @staticmethod
    def _parse_critique(critique_text: str) -> str:
        """Parse the short critique from critique text."""

        critique_match = re.search(
            r"critique\s*:\s*(.+)", critique_text, re.IGNORECASE | re.DOTALL
        )
        if critique_match:
            return _single_line(critique_match.group(1))

        cleaned = _single_line(critique_text)
        return cleaned or "Unable to parse critique; defaulted to moderate confidence."


def _clamp_score(score: int) -> int:
    """Clamp a score to the required 0-100 range."""

    return max(0, min(100, score))


def _single_line(text: str) -> str:
    """Normalize generated text into a compact single-line critique."""

    return " ".join(text.strip().split())
