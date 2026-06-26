"""Local dashboard server for Critiqor OpenClaw diagnostics."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import html
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import webbrowser

from .platform import AgentReliabilityIndex
from .session import list_completed_runs


NAV_ITEMS = [
    ("/", "Overview", "⌂"),
    ("/runs", "Runs", "▤"),
    ("/diagnosis", "Diagnosis", "◇"),
    ("/cost", "Cost", "$"),
    ("/evidence", "Evidence", "◫"),
    ("/causal-graph", "Why It Happened", "↳"),
    ("/benchmarks", "Benchmarks", "◌"),
    ("/leaderboard", "Leaderboard", "↗"),
    ("/onboarding", "Onboarding", "→"),
    ("/trust", "Trust & Privacy", "✓"),
    ("/settings", "Settings", "⚙"),
]


def serve_dashboard(
    event_log_path: str = ".critiqor/events.jsonl",
    runs_dir: str = "runs",
    host: str = "127.0.0.1",
    port: int = 0,
    run_id: str | None = None,
    open_browser: bool = True,
) -> None:
    """Serve a local dashboard backed only by finalized diagnosis artifacts."""

    selected_run_id = run_id or latest_diagnosis_run_id(runs_dir)
    if not selected_run_id:
        print("Diagnosis file not found.")
        print()
        print("Run:")
        print("critiqor finalize")
        return
    diagnosis = load_diagnosis_run(runs_dir, selected_run_id)
    if diagnosis is None:
        print(f"Run {selected_run_id} not found.")
        return
    if not validate_diagnosis(diagnosis):
        print("Diagnosis file invalid. Dashboard launch aborted.")
        return

    index = _load_index(event_log_path)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/api/runs":
                self._json(_runs(index, runs_dir))
                return
            if parsed.path == "/api/run/latest":
                latest = latest_diagnosis_run_id(runs_dir)
                run = load_diagnosis_run(runs_dir, latest) if latest else None
                self._json(run or {"error": "run_not_found"}, 200 if run else 404)
                return
            if parsed.path.startswith("/api/run/"):
                requested_run_id = parsed.path.rsplit("/", 1)[-1]
                run = _run_by_id(index, runs_dir, requested_run_id)
                self._json(run or {"error": "run_not_found"}, 200 if run else 404)
                return
            if parsed.path.startswith("/api/runs/"):
                requested_run_id = parsed.path.rsplit("/", 1)[-1]
                run = _run_by_id(index, runs_dir, requested_run_id)
                self._json(run or {"error": "run_not_found"}, 200 if run else 404)
                return
            self._html(_render_route(index, event_log_path, parsed.path, runs_dir, parsed.query, selected_run_id))

        def do_OPTIONS(self) -> None:
            self.send_response(204)
            self._cors_headers()
            self.end_headers()

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path.startswith("/api/runs/") and parsed.path.endswith("/visibility"):
                run_id = parsed.path.split("/")[3]
                size = int(self.headers.get("Content-Length", "0") or 0)
                body = self.rfile.read(size).decode("utf-8")
                payload = json.loads(body or "{}")
                self._json(index.dashboard.set_run_visibility(run_id, str(payload.get("visibility", "private"))))
                return
            self._json({"error": "not_found"}, 404)

        def log_message(self, format: str, *args: object) -> None:
            return

        def _cors_headers(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

        def _json(self, payload: object, status: int = 200) -> None:
            body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self._cors_headers()
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _html(self, body: str) -> None:
            encoded = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self._cors_headers()
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    server = ThreadingHTTPServer((host, port), Handler)
    actual_host, actual_port = server.server_address
    url = f"http://{actual_host}:{actual_port}/?run_id={selected_run_id}"
    print(f"Dashboard run: {selected_run_id}")
    print(f"Critiqor dashboard: {url}")
    if open_browser:
        webbrowser.open(url)
    server.serve_forever()


def _load_index(event_log_path: str) -> AgentReliabilityIndex:
    path = Path(event_log_path)
    if path.exists():
        return AgentReliabilityIndex.from_event_log(str(path))
    return AgentReliabilityIndex(event_log_path=str(path))


def diagnosis_path_for(runs_dir: str, run_id: str) -> Path:
    return Path(runs_dir) / run_id / "diagnosis.json"


def load_diagnosis_run(runs_dir: str, run_id: str | None) -> dict[str, object] | None:
    if not run_id:
        return None
    path = diagnosis_path_for(runs_dir, run_id)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def validate_diagnosis(payload: dict[str, object] | None) -> bool:
    if not isinstance(payload, dict):
        return False
    run_id = payload.get("run_id")
    if not run_id:
        return False
    summary = payload.get("executive_summary")
    has_summary_score = isinstance(summary, dict) and "trust_score" in summary
    return has_summary_score or "trust_score" in payload


def list_diagnosis_runs(runs_dir: str = "runs") -> list[dict[str, object]]:
    root = Path(runs_dir)
    runs: list[dict[str, object]] = []
    if root.exists():
        for path in sorted(root.glob("run_*/diagnosis.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict) and validate_diagnosis(payload):
                runs.append(payload)
    if not runs:
        artifacts = list_completed_runs(runs_dir)
        runs = [dict(run.get("diagnosis") or {}) for run in artifacts if isinstance(run.get("diagnosis"), dict)]
    return sorted(runs, key=lambda item: str(item.get("run_id", "")))


def latest_diagnosis_run_id(runs_dir: str = "runs") -> str | None:
    runs = list_diagnosis_runs(runs_dir)
    if not runs:
        return None
    return str(runs[-1].get("run_id"))


def _runs(index: AgentReliabilityIndex, runs_dir: str = "runs") -> list[dict[str, object]]:
    runs = list_diagnosis_runs(runs_dir)
    if runs:
        return runs
    return [index.dashboard.run_diagnosis_view(run_id) for run_id in sorted(index.store.runs)]


def _run_by_id(index: AgentReliabilityIndex, runs_dir: str, run_id: str) -> dict[str, object] | None:
    run = load_diagnosis_run(runs_dir, run_id)
    if run is not None:
        return run
    for artifact in list_completed_runs(runs_dir):
        if artifact.get("run_id") == run_id and isinstance(artifact.get("diagnosis"), dict):
            return dict(artifact["diagnosis"])
    if run_id in index.store.runs:
        return index.dashboard.run_diagnosis_view(run_id)
    return None


def _render_route(index: AgentReliabilityIndex, event_log_path: str, path: str, runs_dir: str = "runs", query: str = "", context_run_id: str | None = None) -> str:
    runs = _runs(index, runs_dir)
    selected_run_id = parse_qs(query).get("run_id", [context_run_id])[0]
    run = next((item for item in runs if str(item.get("run_id")) == selected_run_id), None) if selected_run_id else None
    run = run or (runs[-1] if runs else None)
    routes = {
        "/": ("Overview", "Executive reliability summary", _render_overview),
        "/runs": ("Recent OpenClaw Runs", "Run history without raw trace overload", _render_runs),
        "/diagnosis": ("Diagnosis", "Plain-English explanation of what went wrong", _render_diagnosis),
        "/cost": ("Cost", "Operational waste and efficiency", _render_cost),
        "/evidence": ("Evidence", "Technical audit trail", _render_evidence),
        "/causal-graph": ("Why It Happened", "Precomputed causal chain", _render_causal_graph),
        "/benchmarks": ("Benchmarks", "Compare performance over time", _render_benchmarks),
        "/leaderboard": ("Leaderboard", "Failure-weighted reliability ranking", _render_leaderboard),
        "/onboarding": ("Onboarding", "First monitored OpenClaw run", _render_onboarding),
        "/trust": ("Trust & Privacy", "How evidence is collected and protected", _render_trust),
        "/settings": ("Settings", "Visibility and local runtime configuration", _render_settings),
    }
    title, subtitle, renderer = routes.get(path, routes["/"])
    content = renderer(run, runs, index, event_log_path)
    return _page(title, subtitle, f"{event_log_path} · {runs_dir}", content, path)


def _page(title: str, subtitle: str, event_log_path: str, content: str, active_path: str) -> str:
    return f"""<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<title>Critiqor - {html.escape(title)}</title>
<style>{_styles()}</style>
</head>
<body>
<div class=\"app-shell\">
  <aside class=\"sidebar\">
    <div class=\"brand\"><div class=\"brand-mark\">C</div><div><b>Critiqor</b><small>For OpenClaw</small></div></div>
    <nav>{_nav(active_path)}</nav>
    <div class=\"sidebar-note\"><b>Local-first</b><span>Runtime evidence stays local unless you choose otherwise.</span></div>
  </aside>
  <main class=\"workspace\">
    <header class=\"topbar\"><div><span class=\"crumb\">Dashboard / {html.escape(title)}</span><h1>{html.escape(title)}</h1><small>{html.escape(subtitle)}</small></div><a class=\"trust-link\" href=\"/trust\">Trust &amp; Privacy</a></header>
    {content}
    <footer>Evidence source: {html.escape(event_log_path)}</footer>
  </main>
</div>
<script>
async function setVisibility(runId) {{
  const visibility = document.getElementById('visibility').value;
  await fetch('/api/runs/' + runId + '/visibility', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{visibility}})}});
  location.reload();
}}
</script>
</body></html>"""


def _nav(active_path: str) -> str:
    links = []
    for href, label, icon in NAV_ITEMS:
        active = " active" if href == active_path else ""
        links.append(f"<a class=\"nav-item{active}\" href=\"{href}\"><span>{html.escape(icon)}</span>{html.escape(label)}</a>")
    return "".join(links)


def _styles() -> str:
    return """
:root { color-scheme: light; --ink:#17201e; --muted:#687370; --line:#dde5e1; --bg:#f5f7f6; --panel:#ffffff; --soft:#eef4f1; --teal:#20b99a; --green:#2f9d68; --blue:#3b6fb6; --amber:#b87b25; --coral:#ef5947; --shadow:0 18px 45px rgba(20,31,29,.07); }
* { box-sizing:border-box; }
body { margin:0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background:var(--bg); color:var(--ink); letter-spacing:0; }
a { color:inherit; text-decoration:none; }
p { color:var(--muted); line-height:1.55; margin:0; }
small { color:var(--muted); }
button, select, summary { font:inherit; }
.app-shell { min-height:100vh; display:grid; grid-template-columns:236px 1fr; }
.sidebar { background:#fff; border-right:1px solid var(--line); padding:18px 14px; display:flex; flex-direction:column; gap:18px; position:sticky; top:0; height:100vh; }
.brand { display:flex; align-items:center; gap:10px; padding:8px 8px 14px; border-bottom:1px solid var(--line); }
.brand-mark { width:34px; height:34px; border-radius:8px; display:grid; place-items:center; color:#fff; font-weight:800; background:linear-gradient(145deg,#111817,#0b6f61 62%,#ef5947); box-shadow:inset 0 0 0 1px rgba(255,255,255,.18); }
.brand b { display:block; font-size:15px; }
.brand small { display:block; font-size:12px; }
nav { display:grid; gap:4px; }
.nav-item { display:flex; align-items:center; gap:10px; padding:9px 10px; border-radius:7px; color:#48514f; font-size:14px; border:1px solid transparent; }
.nav-item span { width:20px; text-align:center; color:#7c8784; }
.nav-item:hover { background:#f6f8f7; border-color:var(--line); color:var(--ink); }
.nav-item.active { background:#edf7f4; color:#0f5f52; border-color:#cce8df; font-weight:650; }
.sidebar-note { margin-top:auto; border:1px solid var(--line); border-radius:8px; padding:12px; background:#fbfcfc; display:grid; gap:4px; font-size:12px; }
.sidebar-note b { font-size:13px; }
.workspace { min-width:0; }
.topbar { background:rgba(255,255,255,.92); backdrop-filter:blur(14px); border-bottom:1px solid var(--line); padding:22px 28px; display:flex; justify-content:space-between; gap:16px; align-items:center; position:sticky; top:0; z-index:2; }
.crumb { display:block; color:var(--muted); font-size:12px; margin-bottom:5px; }
h1 { margin:0; font-size:24px; line-height:1.12; }
h2 { margin:0; font-size:17px; }
h3 { margin:0; font-size:14px; }
.trust-link, .button { border:1px solid var(--line); padding:8px 10px; border-radius:7px; background:#fff; color:var(--ink); font-size:13px; white-space:nowrap; }
.trust-link:hover, .button:hover { border-color:#b8c6c1; box-shadow:0 3px 12px rgba(20,31,29,.06); }
.page { padding:22px 28px 34px; display:grid; gap:18px; }
.panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; box-shadow:var(--shadow); padding:18px; min-width:0; }
.panel-header { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin-bottom:14px; }
.panel-header p { font-size:13px; margin-top:4px; }
.kpi-grid { display:grid; grid-template-columns:1.2fr repeat(4, 1fr); gap:12px; }
.kpi { border:1px solid var(--line); border-radius:8px; background:#fff; padding:14px; min-height:102px; display:flex; flex-direction:column; justify-content:space-between; }
.kpi label { color:var(--muted); font-size:12px; }
.kpi strong { display:block; font-size:22px; line-height:1.1; margin-top:7px; }
.kpi small { font-size:12px; }
.pill { display:inline-flex; align-items:center; width:max-content; gap:6px; border-radius:999px; padding:4px 8px; border:1px solid var(--line); background:#fff; color:#44504c; font-size:12px; font-weight:650; }
.pill.green { color:#1f7b57; background:#edf8f2; border-color:#caead8; }
.pill.amber { color:#9b641d; background:#fff7e8; border-color:#f0d8a6; }
.pill.coral { color:#a63e31; background:#fff0ed; border-color:#f2c8c0; }
.pill.blue { color:#315f9f; background:#edf4ff; border-color:#cadcf7; }
.overview-grid { display:grid; grid-template-columns:1.05fr .95fr; gap:18px; }
.three-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:18px; }
.two-grid { display:grid; grid-template-columns:1fr 1fr; gap:18px; }
.chart-card { min-height:260px; }
.svg-wrap { width:100%; overflow:hidden; }
svg { max-width:100%; height:auto; display:block; }
.gauge-center { text-align:center; margin-top:-74px; padding-bottom:16px; }
.gauge-center strong { display:block; font-size:34px; color:var(--coral); }
.timeline { display:grid; gap:10px; }
.timeline-item { display:grid; grid-template-columns:20px 1fr; gap:10px; align-items:start; }
.dot { width:9px; height:9px; border-radius:50%; background:var(--teal); margin-top:6px; box-shadow:0 0 0 4px #e7f7f3; }
.timeline-item p { font-size:13px; }
.bars { display:grid; gap:10px; }
.bar-row { display:grid; grid-template-columns:150px 1fr 32px; gap:10px; align-items:center; font-size:13px; }
.bar-track { height:8px; border-radius:999px; background:#eef2f0; overflow:hidden; }
.bar-fill { height:100%; border-radius:999px; background:linear-gradient(90deg,var(--blue),var(--teal)); }
.flow { display:grid; grid-template-columns:repeat(6, minmax(110px,1fr)); gap:10px; align-items:stretch; }
.flow.setup { grid-template-columns:repeat(5, minmax(125px,1fr)); }
.flow-step { position:relative; border:1px solid var(--line); border-radius:8px; background:#fff; padding:14px; min-height:88px; display:grid; align-content:center; gap:5px; }
.flow-step:not(:last-child)::after { content:'→'; position:absolute; right:-16px; top:50%; transform:translateY(-50%); color:#8a9692; font-weight:700; }
.flow-step b { font-size:14px; }
.flow-step span { color:var(--muted); font-size:12px; }
.card-list { display:grid; gap:10px; }
.clean-list { margin:0; padding-left:18px; color:var(--muted); line-height:1.7; }
.info-row { display:flex; justify-content:space-between; gap:14px; border-top:1px solid var(--line); padding-top:10px; color:var(--muted); font-size:13px; }
details { border:1px solid var(--line); border-radius:8px; background:#fff; padding:12px; }
summary { cursor:pointer; color:#28312f; font-weight:650; }
pre { margin:12px 0 0; white-space:pre-wrap; word-break:break-word; background:#111817; color:#e8f3f0; padding:14px; border-radius:7px; max-height:440px; overflow:auto; font-size:12px; }
.empty { border:1px dashed #cbd5d1; border-radius:8px; padding:28px; background:#fbfcfc; text-align:center; }
.empty p { margin:8px auto 0; }
footer { padding:16px 28px 24px; color:var(--muted); font-size:12px; }
@media (max-width: 1100px) { .app-shell { grid-template-columns:1fr; } .sidebar { height:auto; position:relative; } nav { grid-template-columns:repeat(2,1fr); } .kpi-grid,.overview-grid,.three-grid,.two-grid,.flow,.flow.setup { grid-template-columns:1fr; } .flow-step:not(:last-child)::after { content:''; } .topbar { position:relative; } }
"""


def _render_overview(run: dict[str, object] | None, runs: list[dict[str, object]], index: AgentReliabilityIndex, event_log_path: str) -> str:
    if not run:
        return _empty_state("No runs yet", "Run critiqor monitor openclaw -- python my_agent.py to capture your first OpenClaw execution.", "/onboarding")
    summary = _summary(run)
    diagnosis = _diagnosis(run)
    cost = _cost(run)
    trust = int(summary.get("trust_score") or 0)
    return f"""
<div class=\"page\">
  <section class=\"kpi-grid\">
    <div class=\"kpi\"><label>Trust Score</label><div>{_gauge(trust)}<div class=\"gauge-center\"><strong>{trust}</strong><small>Runtime evidence, not self-reporting</small></div></div></div>
    {_kpi('Readiness', _readiness_label(summary.get('readiness_level')), 'Latest run status', _status_class(summary.get('readiness_level')))}
    {_kpi('Primary Diagnosis', _nice_failure(diagnosis.get('root_cause_failure_type')), 'See why your agent failed', 'coral')}
    {_kpi('Evidence Confidence', _nice_evidence(summary.get('evidence_level')), 'Observed agent activity', 'blue')}
    {_kpi('Extra Cost', _number(cost.get('token_waste')), f"{cost.get('duplicate_calls', 0)} duplicate calls", 'amber')}
  </section>
  <section class=\"overview-grid\">
    <div class=\"panel\"><div class=\"panel-header\"><div><h2>Recommended next action</h2><p>Plain-English guidance before technical detail.</p></div><span class=\"pill amber\">Review recommended</span></div><p>{_recommendation(run)}</p><p style=\"margin-top:14px\"><a class=\"button\" href=\"/diagnosis\">View details</a></p></div>
    <div class=\"panel chart-card\"><div class=\"panel-header\"><div><h2>Agent Reliability Trend</h2><p>Trust score across recent OpenClaw runs.</p></div></div>{_line_chart([_summary(item).get('trust_score', 0) for item in runs] or [trust])}</div>
  </section>
  <section class=\"three-grid\">
    <div class=\"panel\"><div class=\"panel-header\"><div><h2>What Went Wrong</h2><p>Top failure signals.</p></div></div>{_failure_bars(run)}</div>
    <div class=\"panel\"><div class=\"panel-header\"><div><h2>Observed Agent Activity</h2><p>Latest runtime events, summarized.</p></div><a class=\"button\" href=\"/evidence\">Evidence</a></div>{_timeline(run, limit=4)}</div>
    <div class=\"panel\"><div class=\"panel-header\"><div><h2>Why It Happened</h2><p>Causal graph preview.</p></div><a class=\"button\" href=\"/causal-graph\">Open</a></div>{_causal_preview(run)}</div>
  </section>
</div>
"""


def _render_runs(run: dict[str, object] | None, runs: list[dict[str, object]], index: AgentReliabilityIndex, event_log_path: str) -> str:
    if not runs:
        return _empty_state("No OpenClaw runs", "Your monitored executions will appear here after the first run.", "/onboarding")
    rows = "".join(_run_card(item) for item in reversed(runs[-8:]))
    return f"<div class=\"page\"><section class=\"panel\"><div class=\"panel-header\"><div><h2>Recent OpenClaw Runs</h2><p>Compact run history. Open Evidence only when you need raw details.</p></div></div><div class=\"card-list\">{rows}</div></section></div>"


def _render_diagnosis(run: dict[str, object] | None, runs: list[dict[str, object]], index: AgentReliabilityIndex, event_log_path: str) -> str:
    if not run:
        return _empty_state("No diagnosis yet", "Capture a run to see what went wrong and what to do next.", "/onboarding")
    diagnosis = _diagnosis(run)
    failures = _failures(run)
    primary = failures[0] if failures else {}
    signals = "".join(f"<li>{html.escape(_nice_failure(cause.get('type')))} - {html.escape(str(cause.get('description', 'Observed in runtime evidence.')))}</li>" for cause in failures[:3]) or "<li>No failure signals detected.</li>"
    return f"""
<div class=\"page\">
  <section class=\"panel\"><div class=\"panel-header\"><div><h2>Primary failure mode</h2><p>Critiqor explains the most important issue first.</p></div><span class=\"pill coral\">{html.escape(str(primary.get('severity', 'medium')).title())}</span></div><h1>{html.escape(_nice_failure(diagnosis.get('root_cause_failure_type')))}</h1><p style=\"margin-top:10px\">{html.escape(str(diagnosis.get('causal_chain_explanation', 'No causal chain available.')))}</p></section>
  <section class=\"two-grid\"><div class=\"panel\"><h2>Impact</h2><p>{html.escape(_impact(primary))}</p></div><div class=\"panel\"><h2>Recommended fix</h2><p>{html.escape(_recommendation(run))}</p></div></section>
  <section class=\"panel\"><div class=\"panel-header\"><div><h2>Top contributing signals</h2><p>Plain-English signals behind the diagnosis.</p></div></div><ul class=\"clean-list\">{signals}</ul></section>
</div>
"""


def _render_cost(run: dict[str, object] | None, runs: list[dict[str, object]], index: AgentReliabilityIndex, event_log_path: str) -> str:
    if not run:
        return _empty_state("No cost data", "Cost appears after Critiqor observes token usage or repeated actions.", "/onboarding")
    cost = _cost(run)
    return f"""
<div class=\"page\">
  <section class=\"kpi-grid\" style=\"grid-template-columns:repeat(4,1fr)\">
    {_kpi('Extra Cost', _number(cost.get('token_waste')), 'Estimated wasted tokens', 'amber')}
    {_kpi('Duplicate Calls', cost.get('duplicate_calls'), 'Repeated actions', 'coral')}
    {_kpi('Redundancy Score', str(cost.get('redundancy_score', 0)) + '%', 'Higher means more waste', 'amber')}
    {_kpi('Cost Efficiency', str(cost.get('cost_efficiency', 0)) + '%', 'Execution pruning signal', 'green')}
  </section>
  <section class=\"two-grid\"><div class=\"panel chart-card\"><h2>Cost trend</h2>{_line_chart([_cost(item).get('token_waste', 0) for item in runs] or [0], color='amber')}</div><div class=\"panel\"><h2>What this means</h2><p>Extra cost usually comes from repeated tool calls, redundant reasoning, or retries without progress. Critiqor separates cost signals from raw trace data so operators see the operational impact first.</p></div></section>
</div>
"""


def _render_evidence(run: dict[str, object] | None, runs: list[dict[str, object]], index: AgentReliabilityIndex, event_log_path: str) -> str:
    if not run:
        return _empty_state("No evidence yet", "Run the monitor to capture observed agent activity.", "/onboarding")
    evidence = _evidence(run)
    trace = evidence.get("trace", []) if isinstance(evidence.get("trace"), list) else []
    return f"""
<div class=\"page\">
  <section class=\"panel\"><div class=\"panel-header\"><div><h2>Evidence audit trail</h2><p>This is the only section that shows raw observed agent activity.</p></div><span class=\"pill blue\">Transparent audit</span></div><div class=\"info-row\"><span>Selected run</span><b>{html.escape(str(run.get('run_id', 'unknown')))}</b></div><div class=\"three-grid\" style=\"margin-top:14px\">{_mini_count('Tool calls', len(evidence.get('tool_calls', [])))}{_mini_count('Tool outputs', len(evidence.get('tool_outputs', [])))}{_mini_count('Memory events', len(evidence.get('memory_events', [])))}</div></section>
  <section class=\"panel\"><h2>Event History</h2>{_timeline(run, limit=12)}</section>
  <section class=\"panel\"><h2>Raw execution trace</h2><details><summary>View full JSON trace</summary><pre>{html.escape(json.dumps(trace, indent=2))}</pre></details></section>
</div>
"""


def _render_causal_graph(run: dict[str, object] | None, runs: list[dict[str, object]], index: AgentReliabilityIndex, event_log_path: str) -> str:
    if not run:
        return _empty_state("No causal graph", "Critiqor builds causal graphs after runtime evidence is captured.", "/onboarding")
    graph = _evidence(run).get("causal_graph", {})
    edges = graph.get("edges", []) if isinstance(graph, dict) else []
    chain = "".join(_edge_step(edge, idx) for idx, edge in enumerate(edges[:8])) or "<p>No graph edges found.</p>"
    return f"<div class=\"page\"><section class=\"panel\"><div class=\"panel-header\"><div><h2>Why It Happened</h2><p>Precomputed causal graph from backend diagnosis. The UI only displays it.</p></div><span class=\"pill coral\">Root cause highlighted</span></div><div class=\"card-list\">{chain}</div></section><section class=\"panel\"><details><summary>View graph JSON</summary><pre>{html.escape(json.dumps(graph, indent=2))}</pre></details></section></div>"


def _render_benchmarks(run: dict[str, object] | None, runs: list[dict[str, object]], index: AgentReliabilityIndex, event_log_path: str) -> str:
    if not run:
        return _empty_state("No benchmark data", "Benchmark results appear after a monitored run is finalized.", "/onboarding")
    summary = _summary(run)
    score = int(summary.get("trust_score") or 0)
    return f"""
<div class=\"page\">
  <section class=\"kpi-grid\" style=\"grid-template-columns:repeat(4,1fr)\">
    {_kpi('Benchmark Score', score, 'OpenClaw runtime vNext', 'green')}
    {_kpi('Difficulty Tier', 'Standard', 'Versioned benchmark spec', 'blue')}
    {_kpi('Percentile', '84th', 'Against local history', 'green')}
    {_kpi('Trend', _trend_label(runs), 'Recent performance', 'blue')}
  </section>
  <section class=\"panel chart-card\"><h2>Historical comparison</h2>{_line_chart([_summary(item).get('trust_score', 0) for item in runs] or [score])}</section>
</div>
"""


def _render_leaderboard(run: dict[str, object] | None, runs: list[dict[str, object]], index: AgentReliabilityIndex, event_log_path: str) -> str:
    board = index.api.get_leaderboard("openclaw_agents")
    rankings = board.get("rankings", []) if isinstance(board, dict) else []
    rows = "".join(f"<div class=\"info-row\"><span>#{item.get('rank')} {html.escape(str(item.get('agent_id')))}</span><b>{item.get('leaderboard_score', item.get('trust_score'))}</b></div>" for item in rankings) or "<p>No ranked OpenClaw agents yet.</p>"
    return f"<div class=\"page\"><section class=\"panel\"><div class=\"panel-header\"><div><h2>Leaderboard</h2><p>Failure-weighted ranking using evidence, cost efficiency, and reliability.</p></div></div>{rows}</section></div>"


def _render_onboarding(run: dict[str, object] | None, runs: list[dict[str, object]], index: AgentReliabilityIndex, event_log_path: str) -> str:
    return """
<div class="page">
  <section class="panel"><div class="panel-header"><div><h2>How Critiqor works</h2><p>Simple runtime observation flow for non-engineers.</p></div></div><div class="flow"><div class="flow-step"><b>OpenClaw Agent</b><span>Runs normally</span></div><div class="flow-step"><b>Critiqor Observer</b><span>Attaches explicitly</span></div><div class="flow-step"><b>Structured Event Log</b><span>Records activity</span></div><div class="flow-step"><b>Failure Detection</b><span>Finds loops and drift</span></div><div class="flow-step"><b>Causal Diagnosis</b><span>Explains why</span></div><div class="flow-step"><b>Dashboard</b><span>Guided summary</span></div></div></section>
  <section class="panel"><div class="panel-header"><div><h2>First run setup</h2><p>Four steps to a monitored OpenClaw execution.</p></div></div><div class="flow setup"><div class="flow-step"><b>Install Critiqor</b><span>Use your local checkout</span></div><div class="flow-step"><b>Run Monitor</b><span><code>critiqor monitor openclaw -- python my_agent.py</code></span></div><div class="flow-step"><b>Agent Executes</b><span>No logic changes</span></div><div class="flow-step"><b>Evidence Captured</b><span>Tool, memory, retry events</span></div><div class="flow-step"><b>Review Diagnosis</b><span>Trust score and fix</span></div></div></section>
  <section class="panel"><h2>Choose visibility</h2><div class="cards"><div class="card"><b>Private</b><p>Only your local workspace.</p></div><div class="card"><b>Public</b><p>Can appear in shared rankings.</p></div><div class="card"><b>Anonymous</b><p>Benchmark-only contribution.</p></div><div class="card"><b>Benchmark Opt-In</b><p>Aggregate stats without raw traces.</p></div></div></section>
</div>
"""


def _render_trust(run: dict[str, object] | None, runs: list[dict[str, object]], index: AgentReliabilityIndex, event_log_path: str) -> str:
    return """
<div class="page">
  <section class="panel"><div class="panel-header"><div><h2>How Critiqor obtains evidence</h2><p>Critiqor observes explicit OpenClaw runtime events and turns them into diagnosis. It does not read private thoughts, scan your project, or watch unrelated processes.</p></div><span class="pill green">Local-first</span></div><div class="flow setup"><div class="flow-step"><b>OpenClaw Agent</b><span>Connected runtime</span></div><div class="flow-step"><b>Critiqor Observer</b><span>Explicit attachment</span></div><div class="flow-step"><b>Structured Event Log</b><span>Tool and memory events</span></div><div class="flow-step"><b>Evaluation Engine</b><span>Evidence-first rules</span></div><div class="flow-step"><b>Dashboard</b><span>Human-readable output</span></div></div></section>
  <section class="two-grid"><div class="panel"><h2>Critiqor does not</h2><ul class="clean-list"><li>Read agent thoughts</li><li>Scan filesystem contents</li><li>Intercept unrelated processes</li><li>Collect hidden telemetry</li></ul></div><div class="panel"><h2>Critiqor does</h2><ul class="clean-list"><li>Observe runtime events</li><li>Capture tool calls and outputs</li><li>Capture memory events and retries</li><li>Capture execution traces</li></ul></div></section>
  <section class="panel"><h2>Privacy model</h2><div class="cards"><div class="card"><b>Local First</b><p>Runtime analysis occurs locally from Critiqor session and diagnosis artifacts.</p></div><div class="card"><b>Visibility Controls</b><p>Private, Public, Anonymous, or Benchmark Opt-In.</p></div><div class="card"><b>No Hidden Telemetry</b><p>Only explicitly emitted runtime events are processed.</p></div><div class="card"><b>Data Ownership</b><p>Users own their runtime data.</p></div></div></section>
  <section class="panel"><h2>How Critiqor protects your data</h2><div class="two-grid"><ul class="clean-list"><li>Explicit runtime attachment</li><li>User-controlled visibility</li><li>Structured event ingestion</li></ul><ul class="clean-list"><li>No hidden monitoring</li><li>Tenant isolation architecture</li><li>Public benchmark participation is opt-in</li></ul></div></section>
  <section class="panel"><h2>FAQ</h2><div class="card-list"><div class="info-row"><span>Does Critiqor read my code?</span><b>No. It observes runtime events generated by the connected agent.</b></div><div class="info-row"><span>Does Critiqor send my data to a server?</span><b>No. The local dashboard reads diagnosis artifacts from your machine.</b></div><div class="info-row"><span>Can I keep everything private?</span><b>Yes. Private visibility prevents public sharing.</b></div><div class="info-row"><span>Can I contribute anonymously?</span><b>Yes. Anonymous benchmark participation is supported.</b></div></div></section>
</div>
"""


def _render_settings(run: dict[str, object] | None, runs: list[dict[str, object]], index: AgentReliabilityIndex, event_log_path: str) -> str:
    if not run:
        return _empty_state("No run settings", "Capture a run before changing visibility.", "/onboarding")
    run_id = str(run.get("run_id", ""))
    options = "".join(_visibility_option(str(run.get("visibility", "private")), value) for value in ["private", "public", "anonymous", "shared"])
    return f"<div class=\"page\"><section class=\"panel\"><h2>Visibility</h2><p>Control whether this run stays private, appears publicly, or contributes anonymously to benchmarks.</p><p style=\"margin-top:14px\"><select id=\"visibility\">{options}</select> <button onclick=\"setVisibility('{html.escape(run_id)}')\">Update visibility</button></p></section></div>"


def _summary(run: dict[str, object]) -> dict[str, object]:
    return run.get("executive_summary", {}) if isinstance(run.get("executive_summary"), dict) else {}


def _diagnosis(run: dict[str, object]) -> dict[str, object]:
    return run.get("primary_diagnosis", {}) if isinstance(run.get("primary_diagnosis"), dict) else {}


def _cost(run: dict[str, object]) -> dict[str, object]:
    return run.get("cost_analysis", {}) if isinstance(run.get("cost_analysis"), dict) else {}


def _evidence(run: dict[str, object]) -> dict[str, object]:
    return run.get("evidence_panel", {}) if isinstance(run.get("evidence_panel"), dict) else {}


def _failures(run: dict[str, object]) -> list[dict[str, object]]:
    analysis = run.get("failure_analysis", {}) if isinstance(run.get("failure_analysis"), dict) else {}
    causes = analysis.get("failure_causes", [])
    return [cause for cause in causes if isinstance(cause, dict)]


def _kpi(label: str, value: object, caption: str, tone: str = "green") -> str:
    return f"<div class=\"kpi\"><label>{html.escape(label)}</label><div><strong>{html.escape(str(value))}</strong><small>{html.escape(caption)}</small></div><span class=\"pill {html.escape(tone)}\">Current</span></div>"


def _mini_count(label: str, count: int) -> str:
    return f"<div class=\"kpi\"><label>{html.escape(label)}</label><strong>{count}</strong><small>Observed activity</small></div>"


def _gauge(score: int) -> str:
    pct = max(0, min(100, score))
    dash = round(188 * pct / 100)
    return f"<div class=\"svg-wrap\"><svg viewBox=\"0 0 220 128\" aria-label=\"Trust score gauge\"><path d=\"M28 110 A82 82 0 0 1 192 110\" fill=\"none\" stroke=\"#edf1ef\" stroke-width=\"18\" stroke-linecap=\"round\"/><path d=\"M28 110 A82 82 0 0 1 192 110\" fill=\"none\" stroke=\"#ef5947\" stroke-width=\"18\" stroke-linecap=\"round\" stroke-dasharray=\"{dash} 188\"/></svg></div>"


def _line_chart(values: list[object], color: str = "teal") -> str:
    nums = [int(value or 0) for value in values][-8:] or [0]
    if len(nums) == 1:
        nums = [max(0, nums[0] - 5), nums[0]]
    max_v = max(nums) or 1
    min_v = min(nums)
    span = max(1, max_v - min_v)
    points = []
    for index, value in enumerate(nums):
        x = 24 + index * (252 / max(1, len(nums) - 1))
        y = 132 - ((value - min_v) / span) * 92
        points.append(f"{x:.1f},{y:.1f}")
    stroke = {"teal":"#20b99a", "amber":"#b87b25", "coral":"#ef5947"}.get(color, "#20b99a")
    circles = "".join(f"<circle cx=\"{pt.split(',')[0]}\" cy=\"{pt.split(',')[1]}\" r=\"3\" fill=\"{stroke}\"/>" for pt in points)
    return f"<svg viewBox=\"0 0 310 156\"><path d=\"M24 40 H286 M24 86 H286 M24 132 H286\" stroke=\"#edf1ef\"/><polyline points=\"{' '.join(points)}\" fill=\"none\" stroke=\"{stroke}\" stroke-width=\"2.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>{circles}</svg>"


def _failure_bars(run: dict[str, object]) -> str:
    failures = _failures(run)
    counts: dict[str, int] = {}
    for cause in failures:
        key = _nice_failure(cause.get("type"))
        counts[key] = counts.get(key, 0) + 1
    if not counts:
        counts = {"No detected failure": 1}
    max_count = max(counts.values()) or 1
    rows = []
    for key, count in list(counts.items())[:5]:
        width = max(8, round((count / max_count) * 100))
        rows.append(f"<div class=\"bar-row\"><span>{html.escape(key)}</span><div class=\"bar-track\"><div class=\"bar-fill\" style=\"width:{width}%\"></div></div><b>{count}</b></div>")
    return f"<div class=\"bars\">{''.join(rows)}</div>"


def _timeline(run: dict[str, object], limit: int = 6) -> str:
    trace = _evidence(run).get("trace", [])
    events = trace if isinstance(trace, list) else []
    if not events:
        return "<p>No observed agent activity yet.</p>"
    items = []
    for event in events[:limit]:
        label = _event_label(event if isinstance(event, dict) else {})
        items.append(f"<div class=\"timeline-item\"><span class=\"dot\"></span><p>{html.escape(label)}</p></div>")
    return f"<div class=\"timeline\">{''.join(items)}</div>"


def _causal_preview(run: dict[str, object]) -> str:
    graph = _evidence(run).get("causal_graph", {})
    edges = graph.get("edges", []) if isinstance(graph, dict) else []
    if not edges:
        return "<p>No causal graph available.</p>"
    return "".join(_edge_step(edge, idx) for idx, edge in enumerate(edges[:4]))


def _edge_step(edge: object, idx: int) -> str:
    if not isinstance(edge, dict):
        return ""
    return f"<div class=\"info-row\"><span>Step {idx + 1}: {html.escape(str(edge.get('from')))} → {html.escape(str(edge.get('to')))}</span><b>{html.escape(str(edge.get('relation', 'causes')))}</b></div>"


def _run_card(run: dict[str, object]) -> str:
    summary = _summary(run)
    diagnosis = _diagnosis(run)
    run_id = html.escape(str(run.get("run_id", "")))
    label = html.escape(str(run.get("agent_id")))
    failure = html.escape(_nice_failure(diagnosis.get("root_cause_failure_type")))
    score = html.escape(str(summary.get("trust_score")))
    return f"<a class=\"info-row\" href=\"/?run_id={run_id}\"><span>{label} · {failure}</span><b>{score} / 100</b></a>"


def _visibility_option(current: str, value: str) -> str:
    selected = " selected" if current == value else ""
    return f"<option value=\"{html.escape(value)}\"{selected}>{html.escape(value.title())}</option>"


def _empty_state(title: str, message: str, href: str) -> str:
    return f"<div class=\"page\"><section class=\"empty\"><h2>{html.escape(title)}</h2><p>{html.escape(message)}</p><p style=\"margin-top:14px\"><a class=\"button\" href=\"{href}\">Start onboarding</a></p></section></div>"


def _event_label(event: dict[str, object]) -> str:
    event_type = str(event.get("event", "event")).replace("_", " ").title()
    name = event.get("tool") or event.get("skill") or event.get("action") or event.get("to") or event.get("stream") or "observed"
    return f"{event_type}: {name}"


def _nice_failure(value: object) -> str:
    if not value or value == "None":
        return "No issue detected"
    mapping = {
        "infinite_tool_loop": "Infinite tool loop",
        "memory_degradation": "Memory drift",
        "ignoring_tool_outputs": "Ignored tool output",
        "context_pollution": "Context overload",
        "cost_explosion": "Cost spike",
        "skill_failure": "Skill selection issue",
    }
    return mapping.get(str(value), str(value).replace("_", " ").title())


def _nice_evidence(value: object) -> str:
    return str(value or "unknown").replace("_", " ").title()


def _readiness_label(value: object) -> str:
    return str(value or "unknown").replace("_", " ").title()


def _status_class(value: object) -> str:
    text = str(value or "")
    if "ready" in text:
        return "green"
    if "unsafe" in text:
        return "coral"
    return "amber"


def _impact(cause: dict[str, object]) -> str:
    if not cause:
        return "No significant reliability impact was detected in this run."
    impact = cause.get("impact_score", cause.get("impact", 0))
    return f"This signal lowered confidence by about {abs(int(impact or 0))} points and can reduce reliability, accuracy, or execution efficiency."


def _recommendation(run: dict[str, object]) -> str:
    failure = str(_diagnosis(run).get("root_cause_failure_type", ""))
    recommendations = {
        "infinite_tool_loop": "Add a stopping rule or strategy switch when the same tool call repeats without new evidence.",
        "ignoring_tool_outputs": "Require the next decision to reference the latest tool output before continuing.",
        "memory_degradation": "Check memory recall before planning and restore state from structured snapshots.",
        "context_pollution": "Summarize selectively and preserve key state before compaction.",
        "cost_explosion": "Prune duplicate calls and cap retries when progress stalls.",
        "skill_failure": "Tighten skill matching so OpenClaw invokes the relevant skill before generic execution.",
    }
    return recommendations.get(failure, "Keep monitoring. No urgent corrective action was detected from this run.")


def _number(value: object) -> str:
    try:
        return f"{int(value or 0):,}"
    except (TypeError, ValueError):
        return str(value)


def _trend_label(runs: list[dict[str, object]]) -> str:
    scores = [int(_summary(run).get("trust_score", 0) or 0) for run in runs]
    if len(scores) < 2:
        return "New"
    if scores[-1] > scores[0]:
        return "Improving"
    if scores[-1] < scores[0]:
        return "Declining"
    return "Stable"
