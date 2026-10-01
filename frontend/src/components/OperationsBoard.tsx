import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import { apiRequest, getResource } from '../services/api';

type Assessment = {
  id: string;
  name: string;
  status: string;
  is_authorized: boolean;
  scope_text?: string | null;
  exclusions?: string | null;
};

type Operation = {
  task_id: string;
  assessment_id: string;
  tool_id: string;
  target: string;
  status: string;
  started_at?: string | null;
  ended_at?: string | null;
  exit_code?: number | null;
  parsed_results?: Array<Record<string, unknown>>;
  stdout?: string;
  stderr?: string;
};
type ToolInventory = Record<string, { available: boolean; status: string; version: string }>;

const columns = [
  { label: 'QUEUED', status: 'QUEUED' },
  { label: 'RUNNING', status: 'RUNNING' },
  { label: 'COMPLETED', status: 'SUCCESS' },
  { label: 'NEEDS REVIEW', status: 'SKIPPED' },
];

function displayValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return 'Not reported';
  if (typeof value === 'object') return JSON.stringify(value, null, 2);
  return String(value);
}

export function OperationsBoard() {
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [operations, setOperations] = useState<Operation[]>([]);
  const [toolInventory, setToolInventory] = useState<ToolInventory>({});
  const [selected, setSelected] = useState<Operation | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [runningId, setRunningId] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [assessmentRows, taskRows] = await Promise.all([
        getResource<Assessment[]>('/api/assessments'),
        getResource<Operation[]>('/api/tasks'),
      ]);
      const inventory = await getResource<{ tools?: ToolInventory }>('/api/tools/inventory').catch(() => ({ tools: {} }));
      setAssessments(Array.isArray(assessmentRows) ? assessmentRows : []);
      setToolInventory(inventory.tools ?? {});
      const normalized = Array.isArray(taskRows) ? taskRows : [];
      setOperations(normalized);
      setSelected((current) => current ? normalized.find((item) => item.task_id === current.task_id) ?? current : null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not load operations.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    if (!operations.some((operation) => operation.status === 'RUNNING')) return;
    const timer = window.setInterval(() => { void load(); }, 2500);
    return () => window.clearInterval(timer);
  }, [load, operations]);

  const authorizedAssessments = useMemo(() => assessments.filter((assessment) => assessment.is_authorized), [assessments]);

  async function createOperation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const payload = {
      assessment_id: String(form.get('assessment_id') ?? ''),
      tool_id: String(form.get('tool_id') ?? ''),
      target: String(form.get('target') ?? '').trim(),
    };
    setSaving(true); setError(''); setNotice('');
    try {
      const response = await apiRequest('/api/tasks', { method: 'POST', body: JSON.stringify(payload) });
      const body = await response.json().catch(() => null);
      if (!response.ok) throw new Error(body?.detail ?? `Could not queue operation (${response.status})`);
      setCreating(false);
      setNotice('Operation queued. It can only execute while the assessment and target remain authorized.');
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not queue operation.');
    } finally { setSaving(false); }
  }

  async function runOperation(operation: Operation) {
    const assessment = assessments.find((item) => item.id === operation.assessment_id);
    if (!toolInventory[operation.tool_id]?.available) {
      setError(`${operation.tool_id} is not installed in the configured execution environment. Install it in the backend runner before starting this operation.`);
      return;
    }
    if (!assessment?.is_authorized || !window.confirm(`Run ${operation.tool_id} against ${operation.target}? This executes the configured security tool within the authorized assessment scope.`)) return;
    setRunningId(operation.task_id); setError(''); setNotice('');
    setOperations((current) => current.map((item) => item.task_id === operation.task_id ? { ...item, status: 'RUNNING' } : item));
    setSelected((current) => current?.task_id === operation.task_id ? { ...current, status: 'RUNNING' } : current);
    try {
      const response = await apiRequest(`/api/tasks/${encodeURIComponent(operation.task_id)}/execute`, { method: 'POST' });
      const body = await response.json().catch(() => null);
      if (!response.ok) throw new Error(body?.detail ?? `Operation failed (${response.status})`);
      setSelected(body as Operation);
      setNotice(`Execution finished with status ${String(body.status)}.`);
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not execute operation.');
      await load();
    } finally { setRunningId(''); }
  }

  return <div className="page-frame operations-board">
    <header className="page-heading"><div><p className="eyebrow">PHASE 4 / MISSION CONTROL</p><h1>Operations board</h1><p className="page-description">Queue tool tasks, run them only against authorized assessment scope, and inspect the returned evidence.</p></div><div className="operations-heading-actions"><span className="status-tag success">SERVER-SIDE SCOPE GATE</span><button className="primary-button" onClick={() => { setError(''); setCreating(true); }}>Queue operation <span>＋</span></button></div></header>
    <div className="operation-safety-banner"><span>!</span><div><strong>Execution requires an authorized assessment.</strong><small>Targets outside the assessment's allowed scope are rejected by the API. Tool execution may contact real systems.</small></div><button className="text-button" onClick={() => void load()}>Refresh ↻</button></div>
    {error && <div className="inline-error" role="alert">{error}</div>}{notice && <div className="success-message" role="status">{notice}</div>}
    {authorizedAssessments.length === 0 && <div className="inline-alert" role="status"><span>!</span><div><strong>No authorized assessment</strong><p>Create an assessment, review its scope, then authorize it before queuing operations.</p></div><span className="status-tag muted-tag">EXECUTION LOCKED</span></div>}
    <div className="operation-board-meta"><div><small>ORCHESTRATOR TASKS</small><strong>{operations.length} queued or recorded</strong></div><div className="tool-availability">{['nmap', 'nuclei', 'zap'].map((tool) => <span className={toolInventory[tool]?.available ? 'tool-ready' : 'tool-missing'} key={tool} title={toolInventory[tool]?.version ?? 'Not installed'}>{tool} · {toolInventory[tool]?.available ? 'ready' : 'missing'}</span>)}<small>Detected by the backend runner.</small></div></div>
    {loading ? <div className="empty-inline">Loading operation queue…</div> : <div className="operation-kanban">{columns.map((column) => {
      const items = operations.filter((operation) => operation.status.toUpperCase() === column.status);
      return <section className="operation-column" key={column.status}><header><span className={`column-marker ${column.status.toLowerCase()}`} /><strong>{column.label}</strong><b>{items.length}</b></header>{items.length ? items.map((operation) => <article className={`operation-card ${selected?.task_id === operation.task_id ? 'selected' : ''}`} key={operation.task_id}><button className="operation-card-main" onClick={() => setSelected(operation)}><span className={`tool-icon ${operation.tool_id}`}>{operation.tool_id.slice(0, 1).toUpperCase()}</span><span><strong>{operation.tool_id}</strong><small>{operation.target}</small></span><span className="card-arrow">↗</span></button><div className="operation-card-meta"><span>{assessments.find((item) => item.id === operation.assessment_id)?.name ?? 'Assessment'}</span><span>{operation.task_id.slice(0, 8)}</span></div>{operation.status === 'QUEUED' && <button className="run-operation-button" disabled={runningId === operation.task_id || !assessments.find((item) => item.id === operation.assessment_id)?.is_authorized || !toolInventory[operation.tool_id]?.available} onClick={() => void runOperation(operation)}>{runningId === operation.task_id ? 'Running…' : toolInventory[operation.tool_id]?.available ? 'Run now' : 'Tool unavailable'} <span>↗</span></button>}</article>) : <div className="column-empty">{column.status === 'QUEUED' && authorizedAssessments.length ? 'Queue a scoped tool task to begin.' : column.status === 'RUNNING' ? 'No task is running.' : `No ${column.label.toLowerCase()} operations yet.`}</div>}</section>;
    })}</div>}
    {selected && <section className="surface-panel operation-inspector"><div className="panel-heading"><div><small>OPERATION DETAIL / {selected.status}</small><h2>{selected.tool_id} · {selected.target}</h2></div><button className="text-button" onClick={() => setSelected(null)} aria-label="Close operation details">×</button></div><div className="operation-detail-grid"><div><small>ASSESSMENT</small><strong>{assessments.find((item) => item.id === selected.assessment_id)?.name ?? selected.assessment_id}</strong></div><div><small>STARTED</small><strong>{selected.started_at ? new Date(selected.started_at).toLocaleString() : 'Not started'}</strong></div><div><small>EXIT CODE</small><strong>{selected.exit_code ?? '—'}</strong></div><div><small>PARSED RESULTS</small><strong>{selected.parsed_results?.length ?? 0}</strong></div></div>{selected.parsed_results?.length ? <div className="operation-results"><small>NORMALIZED RESULTS</small>{selected.parsed_results.map((result, index) => <pre key={index}>{displayValue(result)}</pre>)}</div> : selected.status !== 'QUEUED' && <div className="empty-inline">The tool returned no normalized result records.</div>}{selected.stderr && <details className="operation-logs"><summary>Execution diagnostics</summary><pre>{selected.stderr}</pre></details>}{selected.stdout && <details className="operation-logs"><summary>Tool output</summary><pre>{selected.stdout}</pre></details>}</section>}
    {creating && <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setCreating(false); }}><form className="modal assessment-form operation-form" onSubmit={createOperation}><p className="eyebrow">OPERATION / QUEUE</p><h2>Queue a scoped operation</h2><p>The backend validates the selected target against the assessment's authorized scope again before accepting it.</p><label>AUTHORIZED ASSESSMENT<select name="assessment_id" required defaultValue=""><option value="" disabled>Select assessment</option>{authorizedAssessments.map((assessment) => <option key={assessment.id} value={assessment.id}>{assessment.name}</option>)}</select></label><label>TOOL<select name="tool_id"><option value="nmap">Nmap discovery</option><option value="nuclei">Nuclei web scan</option><option value="zap">OWASP ZAP scan</option></select></label><label>AUTHORIZED TARGET<input name="target" required placeholder="Use an exact target from this assessment's scope" /></label><div className="modal-actions"><button type="button" className="btn-cancel" onClick={() => setCreating(false)}>Cancel</button><button className="primary-button" disabled={saving || !authorizedAssessments.length}>{saving ? 'Queueing…' : 'Queue operation'}</button></div></form></div>}
  </div>;
}
