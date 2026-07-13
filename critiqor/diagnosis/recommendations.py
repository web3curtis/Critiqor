from __future__ import annotations


def recommendation_for(event_name: str) -> str:
    normalized = event_name.casefold()
    if "retry" in normalized:
        return "Inspect repeated requests and add a loop guard or strategy switch."
    if "timeout" in normalized:
        return "Review timeout thresholds and the external dependency involved in the failure."
    if "tool" in normalized:
        return "Inspect the tool call, its arguments, and the corresponding tool output."
    if "memory" in normalized:
        return "Review retrieved memory/context and confirm it was used in the final decision."
    return "Review the supporting runtime evidence around this event."
