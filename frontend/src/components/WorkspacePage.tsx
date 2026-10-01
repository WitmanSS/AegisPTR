import { FormEvent, useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiRequest, getResource } from '../services/api';

type RecordData = Record<string, unknown>;
type PageConfig = { kicker: string; title: string; description: string; action: string; endpoint?: string; unavailable?: string };

const pages: Record<string, PageConfig> = {
  Assessments: { kicker: 'ASSESSMENT WORKSPACE', title: 'Assessments', description: 'Coordinate authorized testing from scope validation through verified remediation.', action: 'New assessment', endpoint: '/api/assessments' },
  Operations: { kicker: 'MISSION CONTROL', title: 'Operations board', description: 'Review tasks currently exposed by the orchestration API. Live progress and event streaming are not yet available.', action: 'Add targets', endpoint: '/api/tasks' },
  'Attack surface': { kicker: 'EXPOSURE INTELLIGENCE', title: 'Attack surface', description: 'Review target records currently stored in the authorized scope.', action: 'Add targets', endpoint: '/api/targets/?limit=100' },
  Findings: { kicker: 'EVIDENCE EXPLORER', title: 'Findings center', description: 'Inspect finding records exposed by the backend. Correlation details and evidence attachments are not currently available.', action: 'Refresh findings', endpoint: '/api/findings' },
  'Risk center': { kicker: 'RISK INTELLIGENCE', title: 'Risk center', description: 'Review configured monitoring KPIs. Historical risk series and asset-level risk APIs are not yet available.', action: 'Refresh metrics', endpoint: '/api/monitoring/summary' },
  Remediation: { kicker: 'REMEDIATION CONTROL', title: 'Remediation board', description: 'Review plans returned by the remediation service. Assignment updates are not exposed in the current API.', action: 'Refresh plans', endpoint: '/api/remediation/plans' },
  Retesting: { kicker: 'VERIFICATION LOOP', title: 'Retesting board', description: 'Review recorded retests and their current validation state.', action: 'Refresh retests', endpoint: '/api/retests' },
  'AI copilot': { kicker: 'EVIDENCE-GROUNDED AI', title: 'AI security copilot', description: 'Check the configured AI provider. The current API exposes status only; it does not provide chat, context retrieval, or approved actions.', action: 'Check provider', endpoint: '/api/ai/status' },
  Monitoring: { kicker: 'CONTINUOUS MONITORING', title: 'Monitoring', description: 'Review current KPI values from the monitoring service. No event feed or historical metric series is available.', action: 'Refresh metrics', endpoint: '/api/monitoring/summary' },
  Reports: { kicker: 'DECISION SUPPORT', title: 'Reports', description: 'The current report summary endpoint returns static demonstration findings and is intentionally not rendered as production report data.', action: 'Open assessments', unavailable: 'Reports are not connected to persisted assessment and finding records yet.' },
};

function labelValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return 'Not provided';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

function humanize(value: string): string {
  return value.replace(/_/g, ' ');
}

function titleFor(record: RecordData, section: string, index: number): string {
  const keys = ['name', 'title', 'canonical', 'target', 'finding_id', 'plan_id', 'retest_id', 'task_id', 'metric'];
  for (const key of keys) if (record[key]) return String(record[key]);
  return `${section} record ${index + 1}`;
}

export function WorkspacePage({ section }: { section: string }) {
  const navigate = useNavigate();
  const view = pages[section] ?? pages.Assessments;
  const [data, setData] = useState<unknown>(null);
  const [selected, setSelected] = useState<RecordData | null>(null);
  const [loading, setLoading] = useState(Boolean(view.endpoint));
  const [error, setError] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [createdMessage, setCreatedMessage] = useState('');

  const load = useCallback(async () => {
    if (!view.endpoint) return;
    setLoading(true); setError('');
    try { setData(await getResource(view.endpoint)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not load this workspace.'); }
    finally { setLoading(false); }
  }, [view.endpoint]);

  useEffect(() => { void load(); }, [load]);

  async function createAssessment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const splitTargets = (key: string) => String(form.get(key) ?? '').split(/\r?\n|,/).map((value) => value.trim()).filter(Boolean);
    setSaving(true); setSaveError('');
    try {
      const response = await apiRequest('/api/assessments', { method: 'POST', body: JSON.stringify({ name: form.get('name'), client: form.get('client'), assessment_type: form.get('assessment_type'), status: 'DRAFT', scope: splitTargets('scope'), exclusions: splitTargets('exclusions') }) });
      const body = await response.json().catch(() => null);
      if (!response.ok) throw new Error(body?.detail ?? `Could not create assessment (${response.status})`);
      setCreateOpen(false); setCreatedMessage('Draft assessment created. Review scope and authorization before running tools.');
      await load();
    } catch (cause) { setSaveError(cause instanceof Error ? cause.message : 'Assessment creation failed.'); }
    finally { setSaving(false); }
  }

  const records: RecordData[] = Array.isArray(data) ? data.filter((item): item is RecordData => Boolean(item && typeof item === 'object')) : [];
  const metrics = data && !Array.isArray(data) && typeof data === 'object' ? Object.entries(data as RecordData) : [];
  const isUnavailable = Boolean(view.unavailable);
  const action = () => {
    if (section === 'Assessments') setCreateOpen(true);
    else if (section === 'Attack surface' || section === 'Operations') navigate('/targets/bulk');
    else if (view.endpoint) void load();
  };

  return <div className="page-frame workspace-page"><div className="page-heading"><div><p className="eyebrow">{view.kicker}</p><h1>{view.title}</h1><p className="page-description">{view.description}</p></div><button className="primary-button" onClick={action}>{view.action}<span>{section === 'Assessments' ? '＋' : '↻'}</span></button></div>
    <div className="workspace-banner"><div className="banner-orbit"><span /><span /><span /></div><div><small>DATA SOURCE</small><strong>{view.endpoint ?? 'Not connected'}</strong><p>{view.endpoint ? 'Authenticated backend API · live request' : 'No production API contract configured'}</p></div><div className="banner-actions"><span className={`status-tag ${view.endpoint ? 'success' : 'muted-tag'}`}>{view.endpoint ? 'API CONNECTED' : 'UNAVAILABLE'}</span></div></div>
    {createdMessage && <div className="success-message" role="status">{createdMessage}</div>}
    {isUnavailable ? <section className="surface-panel unavailable-panel"><span className="unavailable-mark">○</span><div><strong>Not available in this backend yet</strong><p>{view.unavailable}</p></div></section> : <div className={`workspace-data-grid ${selected ? 'has-selection' : ''}`}>
      <section className="surface-panel data-list-panel"><div className="panel-heading"><div><small>{section.toUpperCase()} / API RECORDS</small><h2>{section === 'Risk center' || section === 'Monitoring' || section === 'AI copilot' ? 'Current service state' : 'Current records'}</h2></div>{!loading && <span className="status-tag blue">{Array.isArray(data) ? `${records.length} RECORDS` : data ? 'CURRENT' : 'READY'}</span>}</div>
        {error && <div className="inline-error" role="alert">{error}</div>}
        {loading ? <div className="empty-inline">Loading current API data…</div> : Array.isArray(data) ? records.length ? <div className="record-list">{records.map((record, index) => <button className={`record-row ${selected === record ? 'selected' : ''}`} key={String(record.id ?? record.task_id ?? record.finding_id ?? record.plan_id ?? record.retest_id ?? index)} onClick={() => setSelected(record)}><span className="record-index">{String(index + 1).padStart(2, '0')}</span><span className="record-main"><strong>{titleFor(record, section, index)}</strong><small>{Object.entries(record).filter(([key]) => !['name', 'title', 'canonical', 'target', 'finding_id', 'plan_id', 'retest_id', 'task_id', 'metric'].includes(key)).slice(0, 3).map(([key, value]) => `${humanize(key)}: ${labelValue(value)}`).join(' · ')}</small></span><span className="row-arrow">→</span></button>)}</div> : <div className="empty-state"><span>◈</span><strong>No records returned</strong><p>This endpoint is connected, but it currently has no records to show.</p></div> : metrics.length ? <div className="metrics-records">{metrics.map(([key, value]) => <button className="metric-record" key={key} onClick={() => setSelected({ [key]: value })}><small>{humanize(key).toUpperCase()}</small><strong>{labelValue(value)}</strong></button>)}</div> : <div className="empty-inline">No response data returned by the API.</div>}
      </section>
      {selected && <aside className="surface-panel record-detail"><div className="panel-heading"><div><small>RECORD DETAILS</small><h2>{titleFor(selected, section, 0)}</h2></div><button className="text-button" onClick={() => setSelected(null)} aria-label="Close record details">×</button></div><dl>{Object.entries(selected).map(([key, value]) => <div key={key}><dt>{humanize(key)}</dt><dd>{labelValue(value)}</dd></div>)}</dl><div className="record-trust-note">Values are displayed as received from the backend. Treat scanner and finding content as untrusted evidence.</div></aside>}
    </div>}
    {createOpen && <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setCreateOpen(false); }}><form className="modal assessment-form" onSubmit={createAssessment}><p className="eyebrow">ASSESSMENT / DRAFT</p><h2>Create assessment</h2><p>A new assessment starts as DRAFT. Tool execution requires separately reviewed authorization.</p><label>Name<input name="name" required maxLength={160} /></label><label>Client<input name="client" required maxLength={160} /></label><label>Type<select name="assessment_type"><option>External</option><option>Internal</option><option>Web application</option><option>Cloud</option></select></label><label>Initial scope<textarea name="scope" placeholder="One target per line" /></label><label>Exclusions<textarea name="exclusions" placeholder="Optional, one target per line" /></label>{saveError && <div className="inline-error" role="alert">{saveError}</div>}<div className="modal-actions"><button type="button" className="btn-cancel" onClick={() => setCreateOpen(false)}>Cancel</button><button className="primary-button" disabled={saving}>{saving ? 'Creating…' : 'Create draft'}</button></div></form></div>}
  </div>;
}
