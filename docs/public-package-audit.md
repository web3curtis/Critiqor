# Critiqor Repository Architecture

Critiqor is distributed as one local-first public package.

## Package boundaries

- `critiqor/diagnosis/` classifies recorded events and assembles diagnosis artifacts.
- `critiqor/session.py` owns observation-session state and artifact persistence.
- `critiqor/runtime.py` coordinates framework processes and CLI workflows.
- `critiqor/dashboard.py` discovers artifacts, starts the dashboard, and creates private access sessions.
- `critiqor/frameworks.py` manages built-in and custom framework configuration.
- `critiqor/schemas.py` contains shared event and diagnosis data contracts.

Runtime data under `runs/` is user-owned and excluded from source distributions.
Generated caches, dashboard state, tests, and build output are also excluded from
the wheel.

The diagnosis pipeline runs locally and does not require a hosted backend,
plugin package, API URL, or API key.
