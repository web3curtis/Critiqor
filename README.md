# Aegis

Lightweight self-verification for AI agents: one critique, one confidence score.

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-alpha-orange)

Aegis wraps an existing agent with one simple self-critique step and returns a
confidence score from `0` to `100`. It is intentionally small: no retries, no
dashboard, no benchmarking suite, and no complex judge framework.

## Quick Start

```bash
python -m pip install -e .
```

After a PyPI release, install with:

```bash
pip install aegis-ai
```

```python
from aegis import Aegis

base_agent = TheirExistingAgent(model="llama3.2")
agent = Aegis(base_agent)

result = agent.run("Explain vector databases in one paragraph.")

print(result.answer)
print(result.confidence)
print(result.critique)
```

See [Usage Guide](#usage-guide) for supported agent shapes and local examples.

## Philosophy / Non-Goals

Aegis is a minimal reliability wrapper, not a full evaluation platform.

It does:

- Run your existing agent once for an answer
- Run one self-critique pass
- Return `answer`, `confidence`, and `critique`

It does not:

- Retry failed answers
- Compare multiple models
- Act as an external AI judge
- Provide dashboards, benchmarks, queues, or tracing
- Replace human review for high-stakes work

## When To Use

Use Aegis when:

- You already have an agent and want a lightweight confidence signal.
- You want one extra self-check without changing your agent architecture.
- You need a simple result object for routing, logging, or review thresholds.
- Your team wants a small reliability layer before investing in a full eval stack.

Do not use Aegis when:

- You need rigorous offline benchmarking or dataset-based evaluation.
- You need independent model grading instead of self-critique.
- You need automatic retries, tool repair, or autonomous correction.
- You are making high-stakes decisions that require audited verification.

## How It Works

Every `Aegis.run(prompt)` call does two things:

1. Ask your existing agent for an answer.
2. Ask the same agent to critique that answer and assign a confidence score.

The result is an `AegisResult`:

```python
result.answer      # str
result.confidence  # int, 0-100
result.critique    # str
```

See [Confidence Scoring](#confidence-scoring) for the scoring rubric.

## Confidence Scoring

Aegis asks the wrapped agent to score its answer using this exact rubric:

| Score | Label | Justification |
| --- | --- | --- |
| `90-100` | Very High | No visible issues; answer is clear, complete, and well-supported. |
| `75-89` | High | Minor issues only, such as small assumptions, mild vagueness, or missing nuance. |
| `60-74` | Moderate | Some problems, such as partial hallucination risk, logical gaps, or incomplete coverage. |
| `40-59` | Low | Significant problems, such as multiple unsupported claims, contradictions, or weak task fit. |
| `0-39` | Very Low | Major failures, such as strong hallucinations, task failure, tool misuse, or unusable output. |

Each score should include a short critique explaining why the answer landed in
that band.

## Usage Guide

### Supported Agents

Aegis can wrap any object that exposes one of these interfaces:

- `run(prompt)`
- `invoke(prompt)`
- `generate(prompt)`
- `__call__(prompt)`

The base agent only needs to accept a prompt and return a text-like response.

Aegis can extract text from:

- Plain strings
- Objects with `.content`, `.text`, `.answer`, or `.output`
- Dictionaries with `content`, `text`, `answer`, `output`, or `response`

### Basic Example

```python
from aegis import Aegis


class TheirExistingAgent:
    def run(self, prompt: str) -> str:
        if "Confidence:" in prompt:
            return (
                "Confidence: 86\n"
                "Critique: Clear and useful overall, with minor assumptions that "
                "are not fully supported by evidence."
            )

        return "Aegis adds one self-critique step and returns a confidence score."


agent = Aegis(TheirExistingAgent())
result = agent.run("What does Aegis do?")

print(result.answer)
print(result.confidence)
print(result.critique)
```

### Callable Agent

```python
from aegis import Aegis


def agent_fn(prompt: str) -> str:
    if "Confidence:" in prompt:
        return "Confidence: 91\nCritique: Direct, coherent, and well-supported."
    return "This answer came from a callable agent."


agent = Aegis(agent_fn)
result = agent.run("Say something concise.")
```

### Dict Response

```python
from aegis import Aegis


class InvokeAgent:
    def invoke(self, prompt: str) -> dict[str, str]:
        if "Confidence:" in prompt:
            return {"text": "Confidence: 78\nCritique: Good answer, but slightly vague."}
        return {"text": "This answer came from invoke()."}


agent = Aegis(InvokeAgent())
result = agent.run("Explain the wrapper.")
```

## Local Verification

Run the example:

```bash
python examples/simple_usage.py
```

Run the smoke experiment:

```bash
python experiments/sandbox_eval.py
```

Run tests:

```bash
python -m unittest discover -s tests -v
```

The tests cover `run`, `invoke`, loose critique parsing, and clear failure for
unsupported agent objects.

## API Reference

### `Aegis(agent)`

Wraps an existing agent and adds one self-verification pass.

### `Aegis.run(prompt, *args, **kwargs)`

Runs the base agent once for the answer and once for the critique. Extra
arguments are forwarded to the answer-generation call.

### `AegisResult`

```python
answer: str
confidence: int
critique: str
```

## Roadmap / Status

Aegis is currently `0.1.0` alpha. V1 is intentionally minimal and focused on
the wrapper contract.

Planned future directions:

- Optional external critic agents
- Configurable critique prompts
- Retry or repair hooks
- Dataset-based evaluation examples
- Packaging and release automation

These are intentionally out of scope for V1. The current goal is a tiny,
developer-first wrapper that is easy to understand and easy to remove.

## Included Files

- [aegis/core.py](</Users/curtisqiu/Documents/Agent Evaluation/aegis/core.py:1>): Core wrapper and result object
- [examples/simple_usage.py](</Users/curtisqiu/Documents/Agent Evaluation/examples/simple_usage.py:1>): Minimal copy-paste example
- [experiments/sandbox_eval.py](</Users/curtisqiu/Documents/Agent Evaluation/experiments/sandbox_eval.py:1>): End-to-end smoke demo
- [tests/test_core.py](</Users/curtisqiu/Documents/Agent Evaluation/tests/test_core.py:1>): Focused regression tests
