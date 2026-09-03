# Critiqor × Crema controlled experiment protocol

Question: when Crema commits cumulative `add_to_cart` but Chrome hides its response, does the generated Critiqor playbook reduce blind redispatch while preserving task completion?

- Independent variable: playbook exposure only.
- Controlled: target commit and reset state, task, model/runtime, Chrome, permissions, fault, observer, and evaluation rules.
- Dependent: authoritative quantity, blind redispatch, task completion, timing, calls, and token cost.
- Fault: hide exactly one matching response at Chrome response stage after HTTP 200.
- Authority: Crema's read-only `get_cart` result.

Current status: the first sealed natural baseline passed safely at quantity one. The matched treatment and five valid matched pairs remain pending. No uplift is claimed.
