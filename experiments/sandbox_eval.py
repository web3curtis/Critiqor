"""Small end-to-end local diagnosis experiment."""

from __future__ import annotations

from critiqor import generate_diagnosis


def main() -> None:
    diagnosis = generate_diagnosis(
        run_id="sandbox_run",
        metadata={"framework": "custom", "agent_id": "demo_agent"},
        events=[
            {"event": "tool_call", "tool": "search", "message": "Search started"},
            {"event": "tool_output", "tool": "search", "message": "Search completed"},
        ],
        session_json="runs/sandbox_run/session.json",
    )
    print(diagnosis)


if __name__ == "__main__":
    main()
