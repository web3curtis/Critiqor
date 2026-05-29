# Aegis

Aegis is a lightweight self-verification layer for AI agents.

It wraps an existing agent with one simple self-critique step and returns a
confidence score from 0 to 100. It is intentionally small: no retries, no
dashboard, no benchmarking suite, and no complex judge framework.

```python
from aegis import Aegis

base_agent = TheirExistingAgent(model="llama3.2")
verified_agent = Aegis(base_agent)

result = verified_agent.run("Your prompt here")

print(result.answer)
print(result.confidence)
print(result.critique)
```

## Why Aegis?

Most agent reliability tools become systems of their own. Aegis is meant to be
the opposite: one clean wrapper that adds one extra check without forcing you to
rebuild your stack.

Use Aegis when you want:

- One extra self-check after an agent answers
- A simple integer confidence score
- A short critique that explains the score
- A wrapper that works with common agent interfaces

## How It Works

Every `Aegis.run(prompt)` call does exactly two things:

1. It asks your existing agent for an answer.
2. It asks that same agent to critique its answer and assign a confidence score.

The result comes back as a small structured object:

- `answer`: the original answer from your agent
- `confidence`: an integer from `0` to `100`
- `critique`: a short explanation of the score

That is the entire V1 model. Aegis does not retry, re-rank, benchmark, or route
between multiple evaluators.

## Confidence Scoring

Aegis asks the wrapped agent to critique its own answer using this exact scale:

- `90-100`: Very High - No issues, clear, well-supported answer
- `75-89`: High - Minor issues only, such as small assumptions or vagueness
- `60-74`: Moderate - Some problems, such as partial hallucination or logical gaps
- `40-59`: Low - Significant problems, such as multiple hallucinations or contradictions
- `0-39`: Very Low - Major failures, such as strong hallucinations, task failure, or tool misuse

Each score should come with a short, clear explanation in the critique.

## Onboarding

This section is the fastest path from a new repo checkout to a working Aegis
integration.

### 1. Know What Aegis Expects

Aegis can wrap any object that exposes one of these interfaces:

- `run(prompt)`
- `invoke(prompt)`
- `generate(prompt)`
- `__call__(prompt)`

The wrapped object does not need to know anything about Aegis. It only needs to
accept a prompt and return some text-like response.

Aegis can extract text from:

- Plain strings
- Objects with `.content`, `.text`, `.answer`, or `.output`
- Dictionaries with `content`, `text`, `answer`, `output`, or `response`

### 2. Install or Run Locally

For local development in this repo:

```bash
python examples/simple_usage.py
python -m unittest discover -s tests
python experiments/sandbox_eval.py
```

For editable installation in an environment where packaging dependencies are
available:

```bash
python -m pip install -e .
```

### 3. Wrap Your Existing Agent

The integration should be one new line:

```python
from aegis import Aegis

base_agent = TheirExistingAgent(model="llama3.2")
verified_agent = Aegis(base_agent)
```

From there, keep calling `run()` the way you already do:

```python
result = verified_agent.run("Summarize the design tradeoffs in this API.")
```

### 4. Read the Result

`Aegis.run()` returns an `AegisResult` object with three fields:

```python
print(result.answer)
print(result.confidence)
print(result.critique)
```

Typical usage in an app looks like this:

```python
if result.confidence < 60:
    print("This answer may need review.")

print(result.answer)
```

### 5. Verify the Integration

Use the included checks to confirm your setup behaves correctly:

```bash
python -m unittest discover -s tests -v
python experiments/sandbox_eval.py
```

The test suite covers:

- `run()`-based agents
- `invoke()`-based agents
- Loose critique formatting
- Clear failure for unsupported agent objects

## Usage Guide

### Basic Example

```python
from aegis import Aegis


class TheirExistingAgent:
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


verified_agent = Aegis(TheirExistingAgent(model="llama3.2"))
result = verified_agent.run("What does Aegis do?")

print(result.answer)
print(result.confidence)
print(result.critique)
```

### Custom Callable Agent

If your agent is just a callable object or function, that works too:

```python
from aegis import Aegis


class CallableAgent:
    def __call__(self, prompt: str) -> str:
        if "Confidence:" in prompt:
            return "Confidence: 91\nCritique: Direct, coherent, and well-supported."
        return "This answer came from a callable agent."


verified_agent = Aegis(CallableAgent())
result = verified_agent.run("Say something concise.")
```

### Dict or Object Responses

If your base agent returns a dictionary or an object-like response, Aegis will
try to extract the answer text automatically:

```python
from aegis import Aegis


class InvokeAgent:
    def invoke(self, prompt: str) -> dict[str, str]:
        if "Confidence:" in prompt:
            return {"text": "Confidence: 78\nCritique: Good answer, but slightly vague."}
        return {"text": "This answer came from invoke()."}


verified_agent = Aegis(InvokeAgent())
result = verified_agent.run("Explain the wrapper.")
```

## Designing Good Critiques

Because Aegis uses the same model for answer generation and critique, the best
results usually come from base agents that follow formatting instructions
reliably.

Good critique behavior looks like:

- Returning a single integer confidence score
- Returning one short explanation
- Calling out assumptions, vagueness, or unsupported claims directly

Aegis is forgiving if the critique is slightly messy. It will try to parse the
confidence score even if the model drifts from the exact format.

## Error Handling

If the wrapped object does not expose a supported interface, Aegis raises:

```python
TypeError("Aegis requires an agent with run(), invoke(), generate(), or __call__().")
```

That failure is intentional. V1 keeps the contract small and explicit.

## API Reference

### `Aegis`

Wraps an existing agent and adds one self-verification pass.

```python
Aegis(agent)
```

### `Aegis.run`

Runs the base agent once for the answer and once for the critique.

```python
result = verified_agent.run(prompt: str)
```

Returns an `AegisResult`.

### `AegisResult`

```python
result.answer      # str
result.confidence  # int
result.critique    # str
```

## Included Files

- [aegis/core.py](</Users/curtisqiu/Documents/Agent Evaluation/aegis/core.py:1>): Core wrapper and result object
- [examples/simple_usage.py](</Users/curtisqiu/Documents/Agent Evaluation/examples/simple_usage.py:1>): Small copy-paste example
- [experiments/sandbox_eval.py](</Users/curtisqiu/Documents/Agent Evaluation/experiments/sandbox_eval.py:1>): End-to-end local experiment
- [tests/test_core.py](</Users/curtisqiu/Documents/Agent Evaluation/tests/test_core.py:1>): Minimal regression tests

## Development

Run the local checks:

```bash
python -m unittest discover -s tests -v
```

Run the example:

```bash
python examples/simple_usage.py
```

Run the experiment:

```bash
python experiments/sandbox_eval.py
```
