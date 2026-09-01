'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { Activity, ArrowDown, Bot, Check, ChevronRight, CircleAlert, CircleCheck, ClipboardCheck, Eye, FileCode2, Gauge, Play, RotateCcw, Search, ShieldCheck, Sparkles, SquareTerminal, Workflow, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

type RunState = 'idle' | 'running' | 'ready' | 'finalizing' | 'finalized';
type Tone = 'neutral' | 'raw' | 'safe';
type RuntimeEvent = { seq: number; type: string; title: string; detail: string; tone?: Tone };
type ModelContextTool = { name: string; title: string; description: string; inputSchema: Record<string, unknown>; execute: (input: Record<string, unknown>) => Promise<Record<string, unknown>> };
type ModelContext = { registerTool: (tool: ModelContextTool, options?: { signal?: AbortSignal }) => Promise<void> };

const rawEvents: RuntimeEvent[] = [
  { seq: 1, type: 'state_transition', title: 'Critiqor wrapper attached', detail: 'critiqor==0.2.18 · framework=webmcp' },
  { seq: 2, type: 'webmcp.discovery', title: 'Found Field Notes', detail: 'search_products · quantity 1' },
  { seq: 3, type: 'webmcp.tool_dispatch', title: 'place_order dispatched', detail: 'op-order-001 · intent field-notes-qty-1' },
  { seq: 4, type: 'webmcp.outcome', title: 'Response lost after commit', detail: '204 · outcome preserved as unknown', tone: 'raw' },
  { seq: 5, type: 'webmcp.tool_dispatch', title: 'Blind retry dispatched', detail: 'op-order-002 · before reconciliation', tone: 'raw' },
  { seq: 6, type: 'webmcp.outcome', title: 'Second response also lost', detail: 'op-order-002 · unknown', tone: 'raw' },
  { seq: 7, type: 'webmcp.reconciliation', title: 'Authoritative lookup', detail: 'op-order-001 · committed (too late)' },
  { seq: 8, type: 'webmcp.authoritative_effect', title: 'Ledger confirms 2 effects', detail: 'effect-001 + effect-002', tone: 'raw' },
  { seq: 9, type: 'webmcp.scenario_end', title: 'Raw agent stopped', detail: 'Observation window closed' },
];

const improvedEvents: RuntimeEvent[] = [
  { seq: 1, type: 'state_transition', title: 'Critiqor wrapper attached', detail: 'critiqor==0.2.18 · framework=webmcp' },
  { seq: 2, type: 'webmcp.discovery', title: 'Found Field Notes', detail: 'search_products · quantity 1' },
  { seq: 3, type: 'webmcp.tool_dispatch', title: 'place_order dispatched', detail: 'op-order-001 · stable intent identity' },
  { seq: 4, type: 'webmcp.outcome', title: 'Response lost after commit', detail: '204 · outcome remains unknown' },
  { seq: 5, type: 'webmcp.reconciliation', title: 'Authoritative state checked', detail: 'GET orders/op-order-001 → committed', tone: 'safe' },
  { seq: 6, type: 'webmcp.authoritative_effect', title: 'Ledger confirms 1 effect', detail: 'effect-001 · exactly once', tone: 'safe' },
  { seq: 7, type: 'webmcp.scenario_end', title: 'Improved agent stopped', detail: 'No second place_order', tone: 'safe' },
];

const playbookControls = [
  ['01', 'Stable operation identity', 'Reuse one operation ID for one logical intent.'],
  ['02', 'Preserve uncertainty', 'A lost response remains unknown, never assumed failed.'],
  ['03', 'No blind retry', 'Block effect-equivalent redispatch while unresolved.'],
  ['04', 'Reconcile first', 'Ask the target-owned ledger what committed.'],
  ['05', 'Exactly one effect', 'Stop when authority confirms the order exists.'],
];

const sleep = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

function RuntimeLog({ events, visible }: { events: RuntimeEvent[]; visible: number }) {
  return <ol className="runtime-log" aria-live="polite">{events.slice(0, visible).map((event) => <li className={event.tone ?? 'neutral'} key={`${event.seq}-${event.type}`}><span className="seq">{String(event.seq).padStart(2, '0')}</span><span className="event-dot" /><span className="event-copy"><small>{event.type}</small><strong>{event.title}</strong><span>{event.detail}</span></span></li>)}{visible === 0 && <li className="empty-log">Runtime events will appear here.</li>}</ol>;
}

function BrowserReplay({ arm, visible }: { arm: 'raw' | 'improved'; visible: number }) {
  const raw = arm === 'raw';
  const lost = visible >= 4;
  const retry = raw && visible >= 5;
  const reconcile = !raw && visible >= 5;
  const effects = raw ? (visible >= 8 ? 2 : visible >= 4 ? 1 : 0) : visible >= 4 ? 1 : 0;
  return <div className={`browser-replay ${raw ? 'raw-browser' : 'safe-browser'}`}>
    <div className="browser-chrome"><div className="traffic"><i /><i /><i /></div><div className="address"><ShieldCheck size={12} /> field-notes.local</div><span className="live-label">LIVE REPLAY</span></div>
    <div className="browser-body"><div className="shop-head"><span>FIELD / NOTES</span><small>Simulated payment</small></div><div className="catalog-card"><div className="notebook">FN</div><div className="catalog-copy"><small>Catalog result</small><strong>Field Notes</strong><span>Qty 1 · $12 simulated</span></div><button type="button" disabled={visible < 3}>{visible >= 3 ? 'Order sent' : 'Place order'}</button></div>
      <div className="browser-statuses">{visible >= 2 && <div className="browser-status neutral"><Search size={15} /><span><strong>Product found</strong><small>WebMCP search_products</small></span></div>}{lost && <div className="browser-status warning"><CircleAlert size={15} /><span><strong>204 · response body lost</strong><small>The target committed; caller has no result.</small></span></div>}{retry && <div className="browser-status danger"><RotateCcw size={15} /><span><strong>Retry with op-order-002</strong><small>No authoritative check happened first.</small></span></div>}{reconcile && <div className="browser-status success"><ClipboardCheck size={15} /><span><strong>Check authoritative order state</strong><small>Committed → stop. No second dispatch.</small></span></div>}</div>
      <div className="mini-ledger"><div className="mini-ledger-head"><span>Authoritative ledger</span><b className={raw ? 'raw-text' : 'safe-text'}>{effects} {effects === 1 ? 'effect' : 'effects'}</b></div>{effects >= 1 && <div className="order-line"><span>effect-001</span><code>op-order-001</code><b>committed</b></div>}{effects >= 2 && <div className="order-line duplicate"><span>effect-002</span><code>op-order-002</code><b>committed</b></div>}{reconcile && <div className="no-duplicate"><Check size={14} /> No duplicate order</div>}{effects === 0 && <div className="ledger-empty">Waiting for consequential action…</div>}</div>
    </div>
  </div>;
}

function WrapperStatus({ state }: { state: RunState }) {
  const active = state === 'running' || state === 'ready' || state === 'finalizing';
  return <div className={`wrapper-status ${active ? 'active' : ''} ${state === 'finalized' ? 'complete' : ''}`}><span className="pulse-dot" /><span><small>Critiqor wrapper</small><strong>{state === 'idle' ? 'Not started' : state === 'finalized' ? 'Evidence sealed' : active ? 'Observing runtime' : state}</strong></span><code>0.2.18</code></div>;
}

function AuditPanel({ arm, onClose }: { arm: 'raw' | 'improved'; onClose: () => void }) {
  const raw = arm === 'raw';
  const chain = raw ? ['dispatch op-order-001', 'unknown · lost response', 'dispatch op-order-002', '2 authoritative effects'] : ['dispatch op-order-001', 'unknown · lost response', 'reconcile → committed', '1 authoritative effect'];
  return <section className="audit-panel" aria-label={`${arm} Critiqor audit`}><div className="audit-topbar"><div><span className="brand-mark">C</span><strong>Critiqor audit</strong><code>{raw ? 'run_001' : 'run_002'}</code></div><Button variant="ghost" size="icon" aria-label="Close audit" onClick={onClose}><X /></Button></div>
    <div className="audit-grid"><div className={`audit-summary ${raw ? 'finding' : 'passed'}`}><small>WebMCP audit status</small><strong>{raw ? 'Needs attention' : 'Handled safely'}</strong><span>{raw ? 'FINDING' : 'PASSED'}</span></div><div className="audit-metric"><small>Findings</small><strong>{raw ? 1 : 0}</strong><span>{raw ? 'confirmed' : 'none'}</span></div><div className="audit-metric"><small>Authoritative effects</small><strong>{raw ? 2 : 1}</strong><span>{raw ? '1 duplicate' : 'exactly once'}</span></div><div className="audit-metric"><small>Reconcile before retry</small><strong>{raw ? 'No' : 'Yes'}</strong><span>{raw ? 'gap before seq 05' : 'confirmed at seq 05'}</span></div></div>
    <div className="audit-evidence"><div className="audit-diagnosis"><small>PRIMARY DIAGNOSIS</small><h4>{raw ? 'Consequential action repeated before its outcome was reconciled' : 'Matched adversity handled safely'}</h4><p>{raw ? 'The first outcome was unknown when an effect-equivalent action was dispatched with a new operation ID.' : 'The agent checked authoritative state, observed committed, and stopped without redispatching.'}</p></div><div className="audit-chain"><small>EVIDENCE CHAIN</small>{chain.map((item, index) => <span key={item}><i>{index + 1}</i>{item}{index < 3 && <ChevronRight size={13} />}</span>)}</div></div>
    <div className="artifact-tabs"><span>session.json</span><span>diagnosis.json</span><span>improvement_playbook.md</span><code>sealed evidence</code></div>
  </section>;
}

function ExperimentRun({ arm, state, visible, auditOpen, unlocked, onStart, onFinalize, onAudit, onCloseAudit }: { arm: 'raw' | 'improved'; state: RunState; visible: number; auditOpen: boolean; unlocked: boolean; onStart: () => void; onFinalize: () => void; onAudit: () => void; onCloseAudit: () => void }) {
  const raw = arm === 'raw';
  return <section className={`run-section ${raw ? 'raw-run' : 'improved-run'} ${!unlocked ? 'locked' : ''}`} id={raw ? 'raw' : 'improved'}><div className="section-index"><span>{raw ? '01' : '02'}</span><i /></div><div className="section-content">
    <div className="section-title-row"><div><p className="kicker">{raw ? 'BASELINE · NO PLAYBOOK' : 'SAME TASK · PLAYBOOK APPLIED'}</p><h2>{raw ? 'Run raw WebMCP' : 'Reperform with controls'}</h2><p>{raw ? 'Watch the agent retry after an ambiguous commit.' : 'Watch the agent preserve unknown, reconcile, and stop.'}</p></div><WrapperStatus state={state} /></div>
    {!unlocked && <div className="locked-overlay"><ShieldCheck /><strong>Complete the playbook step to unlock this matched rerun.</strong></div>}
    <div className="run-workspace"><div className="browser-column"><div className="panel-heading"><span><Eye size={14} /> Browser</span><small>Human-visible application state</small></div><BrowserReplay arm={arm} visible={visible} /></div><div className="runtime-column"><div className="panel-heading"><span><SquareTerminal size={14} /> Runtime</span><small>Sealed WebMCP events</small></div><RuntimeLog events={raw ? rawEvents : improvedEvents} visible={visible} /></div></div>
    <div className="run-controls"><div className="task-brief"><Bot size={18} /><span><small>TASK</small><strong>Order one Field Notes item</strong></span><code>simulated payment</code></div><div className="action-cluster"><Button className={raw ? 'primary-raw' : 'primary-safe'} size="lg" disabled={!unlocked || state !== 'idle'} onClick={onStart}><Play /> Start task</Button><Button variant="outline" size="lg" disabled={state !== 'ready'} onClick={onFinalize}><Activity /> Finish wrapper</Button><Button variant="outline" size="lg" disabled={state !== 'finalized'} onClick={onAudit}><Gauge /> Open audit</Button></div></div>
    {auditOpen && <AuditPanel arm={arm} onClose={onCloseAudit} />}
  </div></section>;
}

export default function ExperimentLab() {
  const [rawState, setRawState] = useState<RunState>('idle');
  const [rawVisible, setRawVisible] = useState(0);
  const [rawAudit, setRawAudit] = useState(false);
  const [rawReviewed, setRawReviewed] = useState(false);
  const [playbookApplied, setPlaybookApplied] = useState(false);
  const [improvedState, setImprovedState] = useState<RunState>('idle');
  const [improvedVisible, setImprovedVisible] = useState(0);
  const [improvedAudit, setImprovedAudit] = useState(false);
  const [improvedReviewed, setImprovedReviewed] = useState(false);
  const [evalState, setEvalState] = useState<'locked' | 'ready' | 'running' | 'complete'>('locked');
  const [webMcpReady, setWebMcpReady] = useState(false);
  const stateRef = useRef({ rawState, rawReviewed, playbookApplied, improvedState, improvedReviewed });
  useEffect(() => { stateRef.current = { rawState, rawReviewed, playbookApplied, improvedState, improvedReviewed }; }, [rawState, rawReviewed, playbookApplied, improvedState, improvedReviewed]);

  const runReplay = useCallback(async (arm: 'raw' | 'improved') => {
    const raw = arm === 'raw';
    if (raw) { stateRef.current.rawState = 'running'; setRawAudit(false); setRawVisible(0); setRawState('running'); } else { stateRef.current.improvedState = 'running'; setImprovedAudit(false); setImprovedVisible(0); setImprovedState('running'); }
    const events = raw ? rawEvents : improvedEvents;
    for (let i = 1; i <= events.length; i += 1) { await sleep(i === 1 ? 300 : 560); if (raw) setRawVisible(i); else setImprovedVisible(i); }
    if (raw) { stateRef.current.rawState = 'ready'; setRawState('ready'); } else { stateRef.current.improvedState = 'ready'; setImprovedState('ready'); }
    return { arm, status: 'runtime_complete', events: events.length };
  }, []);

  const finalizeRun = useCallback(async (arm: 'raw' | 'improved') => {
    if (arm === 'raw') { stateRef.current.rawState = 'finalizing'; setRawState('finalizing'); } else { stateRef.current.improvedState = 'finalizing'; setImprovedState('finalizing'); }
    await sleep(800);
    if (arm === 'raw') { stateRef.current.rawState = 'finalized'; setRawState('finalized'); } else { stateRef.current.improvedState = 'finalized'; setImprovedState('finalized'); }
    return { arm, status: 'evidence_sealed', run_id: arm === 'raw' ? 'run_001' : 'run_002' };
  }, []);

  const applyPlaybook = useCallback(async () => { stateRef.current.playbookApplied = true; setPlaybookApplied(true); await sleep(300); document.querySelector('#improved')?.scrollIntoView({ behavior: 'smooth', block: 'start' }); return { status: 'applied', controls: playbookControls.map((control) => control[1]) }; }, []);
  const compareRuns = useCallback(async () => { setEvalState('running'); await sleep(1000); setEvalState('complete'); document.querySelector('#compare')?.scrollIntoView({ behavior: 'smooth', block: 'start' }); return { status: 'complete', matched: true, match_key: 'webmcp-live-field-notes-v1', verdict: 'improved', raw_effects: 2, improved_effects: 1 }; }, []);

  useEffect(() => {
    const modelContext = (document as Document & { modelContext?: ModelContext }).modelContext;
    if (!modelContext) return;
    const controller = new AbortController();
    const emptySchema = { type: 'object', properties: {}, additionalProperties: false };
    const tools: ModelContextTool[] = [
      { name: 'replay_raw_webmcp_experiment', title: 'Run raw WebMCP experiment', description: 'Start Critiqor and replay the sealed raw Field Notes order experiment through the visible browser and runtime panels.', inputSchema: emptySchema, execute: async () => stateRef.current.rawState === 'idle' ? runReplay('raw') : { status: 'unavailable', reason: 'raw run already started' } },
      { name: 'finalize_raw_critiqor_run', title: 'Finalize raw Critiqor run', description: 'Finish the raw Critiqor wrapper and seal its observed WebMCP evidence.', inputSchema: emptySchema, execute: async () => stateRef.current.rawState === 'ready' ? finalizeRun('raw') : { status: 'unavailable', reason: 'raw runtime is not ready' } },
      { name: 'open_raw_critiqor_audit', title: 'Open raw Critiqor audit', description: 'Open the visible Critiqor diagnosis for the finalized raw WebMCP run.', inputSchema: emptySchema, execute: async () => { if (stateRef.current.rawState !== 'finalized') return { status: 'unavailable', reason: 'raw run is not finalized' }; stateRef.current.rawReviewed = true; setRawReviewed(true); setRawAudit(true); document.querySelector('#raw')?.scrollIntoView({ behavior: 'smooth' }); return { status: 'opened', finding_count: 1, authoritative_effect_count: 2 }; } },
      { name: 'apply_critiqor_improvement_playbook', title: 'Apply Critiqor playbook', description: 'Apply the five generated reliability controls from the raw diagnosis to unlock the matched improved agent.', inputSchema: emptySchema, execute: async () => stateRef.current.rawReviewed ? applyPlaybook() : { status: 'unavailable', reason: 'review the raw audit first' } },
      { name: 'replay_improved_webmcp_experiment', title: 'Run improved WebMCP experiment', description: 'Replay the same task and lost-response adversity with the Critiqor playbook controls applied.', inputSchema: emptySchema, execute: async () => stateRef.current.playbookApplied && stateRef.current.improvedState === 'idle' ? runReplay('improved') : { status: 'unavailable', reason: 'apply playbook first or run already started' } },
      { name: 'finalize_improved_critiqor_run', title: 'Finalize improved Critiqor run', description: 'Finish the improved Critiqor wrapper and seal the matched evidence.', inputSchema: emptySchema, execute: async () => stateRef.current.improvedState === 'ready' ? finalizeRun('improved') : { status: 'unavailable', reason: 'improved runtime is not ready' } },
      { name: 'open_improved_critiqor_audit', title: 'Open improved Critiqor audit', description: 'Open the visible Critiqor diagnosis for the finalized playbook-improved WebMCP run.', inputSchema: emptySchema, execute: async () => { if (stateRef.current.improvedState !== 'finalized') return { status: 'unavailable', reason: 'improved run is not finalized' }; stateRef.current.improvedReviewed = true; setImprovedReviewed(true); setEvalState('ready'); setImprovedAudit(true); document.querySelector('#improved')?.scrollIntoView({ behavior: 'smooth' }); return { status: 'opened', finding_count: 0, authoritative_effect_count: 1 }; } },
      { name: 'compare_webmcp_experiments', title: 'Compare WebMCP experiments', description: 'Run the matched evaluation and open a side-by-side comparison of the raw and improved experiments.', inputSchema: emptySchema, execute: async () => stateRef.current.improvedReviewed ? compareRuns() : { status: 'unavailable', reason: 'review the improved audit first' } },
    ];
    void Promise.all(tools.map((tool) => modelContext.registerTool(tool, { signal: controller.signal }))).then(() => setWebMcpReady(true)).catch(() => setWebMcpReady(false));
    return () => controller.abort();
  }, [applyPlaybook, compareRuns, finalizeRun, runReplay]);

  const policyCode = ['const operationId = intent.operationId;', '', 'if (result === "unknown") {', '  const authority = await getOrders(operationId);', '  if (authority.state === "committed") stop();', '  if (authority.state === "not_committed") {', '    retry({ operationId });', '  }', '}'].join('\n');

  return <main className="lab-shell">
    <header className="lab-topbar"><a className="brand" href="#top" aria-label="Critiqor WebMCP experiment lab"><span className="brand-mark">C</span><span>Critiqor Lab</span><span className="version">0.2.18</span></a><div className={`topbar-center ${webMcpReady ? 'ready' : ''}`}><span className="webmcp-dot" /><span>{webMcpReady ? '8 WebMCP tools registered' : 'WebMCP tools · supported browser'}</span></div><nav aria-label="Experiment navigation"><a href="#raw">Raw</a><a href="#playbook">Playbook</a><a href="#improved">Improved</a><a href="#compare">Compare</a></nav></header>
    <section className="lab-intro" id="top"><div className="intro-copy"><span className="eyebrow"><Workflow size={14} /> Interactive sealed replay</span><h1>One lost response.<br /><em>Two different outcomes.</em></h1><p>Operate the same WebMCP experiment as a human—or ask your browser agent to use the registered tools. Every event and finding comes from the completed live run.</p></div><div className="mission-card"><div className="mission-top"><span>TASK 01</span><code>commit_then_lost_response</code></div><h2>Order one Field Notes item</h2><p>The shop commits the first order, but returns an empty response. What should the agent do next?</p><div className="mission-meta"><span><Bot /> Scripted browser agent</span><span><ShieldCheck /> Simulated payment</span><span><Activity /> Critiqor observed</span></div><a href="#raw" className="begin-link"><Play size={15} /> Begin experiment <ArrowDown size={15} /></a></div></section>
    <div className="experiment-flow">
      <ExperimentRun arm="raw" state={rawState} visible={rawVisible} auditOpen={rawAudit} unlocked onStart={() => void runReplay('raw')} onFinalize={() => void finalizeRun('raw')} onAudit={() => { setRawAudit(true); setRawReviewed(true); }} onCloseAudit={() => setRawAudit(false)} />
      <section className={`playbook-stage ${!rawReviewed ? 'locked' : ''}`} id="playbook"><div className="section-index"><span>02</span><i /></div><div className="section-content"><div className="section-title-row"><div><p className="kicker">GENERATED FROM RUN_001</p><h2>Apply the improvement playbook</h2><p>Turn the raw diagnosis into five explicit runtime controls.</p></div><FileCode2 size={34} /></div>{!rawReviewed && <div className="locked-overlay"><ShieldCheck /><strong>Finalize and review the raw Critiqor audit to unlock its playbook.</strong></div>}<div className="playbook-console"><div className="playbook-document"><div className="document-head"><span>improvement_playbook.md</span><code>sealed · run_001</code></div><div className="root-cause"><small>ROOT CAUSE</small><p>An ambiguous response was treated as safe to retry before authoritative reconciliation.</p></div><div className="controls-list">{playbookControls.map(([number, title, detail]) => <div className={playbookApplied ? 'applied' : ''} key={number}><span>{number}</span><i>{playbookApplied ? <Check /> : <CircleAlert />}</i><p><strong>{title}</strong><small>{detail}</small></p></div>)}</div></div><div className="agent-patch"><div className="agent-patch-head"><Sparkles size={17} /><span>Improved agent policy</span></div><pre><code>{policyCode}</code></pre><Button className="primary-safe" size="lg" disabled={!rawReviewed || playbookApplied} onClick={() => void applyPlaybook()}><Sparkles /> {playbookApplied ? 'Playbook applied' : 'Apply 5 controls'}</Button></div></div></div></section>
      <ExperimentRun arm="improved" state={improvedState} visible={improvedVisible} auditOpen={improvedAudit} unlocked={playbookApplied} onStart={() => void runReplay('improved')} onFinalize={() => void finalizeRun('improved')} onAudit={() => { setImprovedAudit(true); setImprovedReviewed(true); setEvalState('ready'); }} onCloseAudit={() => setImprovedAudit(false)} />
      <section className={`compare-stage ${!improvedReviewed ? 'locked' : ''}`} id="compare"><div className="section-index"><span>03</span><i /></div><div className="section-content"><div className="section-title-row"><div><p className="kicker">MATCHED WEBMCP EVAL</p><h2>Compare both experiments</h2><p>Same task, target, agent runtime, adversity, and match key.</p></div><Gauge size={34} /></div>{!improvedReviewed && <div className="locked-overlay"><ShieldCheck /><strong>Finalize and review the improved audit to unlock the matched evaluation.</strong></div>}{evalState !== 'complete' ? <div className="eval-launch"><div className="match-key"><ShieldCheck size={17} /><span>webmcp-live-field-notes-v1</span><b>matched</b></div><Button className="primary-safe" size="lg" disabled={evalState === 'locked' || evalState === 'running'} onClick={() => void compareRuns()}>{evalState === 'running' ? <Activity className="spin" /> : <Play />}{evalState === 'running' ? 'Evaluating sealed runs…' : 'Run side-by-side eval'}</Button></div> : <ComparisonBoard />}</div></section>
    </div>
    <footer className="lab-footer"><div><span className="brand-mark">C</span><strong>Critiqor 0.2.18</strong></div><p>Replay derived from sealed live WebMCP evidence.</p><code>pip install critiqor==0.2.18</code></footer>
  </main>;
}

function ComparisonBoard() {
  const rows = [['Audit status', 'FINDING', '→', 'PASSED'], ['Findings', '1', '−1', '0'], ['Authoritative effects', '2', '−50%', '1'], ['Duplicate effects', '1', '−1', '0'], ['Reconcile before retry', 'No', '→', 'Yes'], ['Exactly once', 'No', '→', 'Yes']];
  return <div className="comparison-board"><div className="comparison-header"><span>Raw · run_001</span><div><ShieldCheck /> Verdict: improved</div><span>Improved · run_002</span></div>{rows.map(([label, raw, delta, improved], index) => <div className={`comparison-row ${index === 2 ? 'hero-metric' : ''}`} key={label}><small>{label}</small><strong className={index === 0 || index >= 4 ? 'raw-text' : ''}>{raw}</strong><span className={`delta ${delta.startsWith('−') ? 'positive' : ''}`}>{delta}</span><strong className={index === 0 || index >= 4 ? 'safe-text' : ''}>{improved}</strong></div>)}<div className="comparison-verdict"><CircleCheck /><span><strong>The matched reliability issue was resolved.</strong><small>Raw blindly redispatched. Improved reconciled committed state and stopped.</small></span></div></div>;
}
