import { useCallback, useEffect, useMemo, useState } from 'react';
import { apiRequest, getResource } from '../services/api';

type Finding = {
  finding_id: string;
  assessment_id: string;
  title: string;
  description?: string | null;
  severity: string;
  risk_score: number;
  confidence: number;
  asset?: string | null;
  cve?: string | null;
  cwe?: string | null;
  source_tool?: string | null;
  status: string;
  evidence: unknown[];
  remediation?: string | null;
  validation_status?: string;
  exposure?: string | null;
  exploitability?: string | null;
};

type Correlation = {
  correlation_id: string;
  assessment_id: string;
  asset: string;
  fingerprint: { type: string; value: string };
  title: string;
  severity: string;
  risk_score: number;
  confidence: number;
  observation_count: number;
  source_tools: string[];
  merged_from: string[];
  rules: string[];
  evidence: Array<{ source_tool: string; finding_id: string; value: unknown }>;
};

const severityOrder = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'];

function tone(value: string): string {
  return value.toLowerCase().replace(/[^a-z]+/g, '-');
}

function evidenceText(value: unknown): string {
  if (typeof value === 'string') return value;
  return JSON.stringify(value, null, 2);
}

export function FindingsExplorer() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [correlations, setCorrelations] = useState<Correlation[]>([]);
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [selectedCorrelation, setSelectedCorrelation] = useState<Correlation | null>(null);
  const [activeView, setActiveView] = useState<'findings' | 'correlations'>('findings');
  const [query, setQuery] = useState('');
  const [severity, setSeverity] = useState('ALL');
  const [status, setStatus] = useState('ALL');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const params = new URLSearchParams({ page: '1', size: '100' });
      if (query.trim()) params.set('q', query.trim());
      if (severity !== 'ALL') params.set('severity', severity);
      if (status !== 'ALL') params.set('status', status);
      const [list, groups] = await Promise.all([
        getResource<{ items: Finding[]; page: { total: number } }>(`/api/findings/explorer?${params.toString()}`),
        getResource<{ items: Correlation[] }>(`/api/findings/correlations?${new URLSearchParams({ ...(severity !== 'ALL' ? { severity } : {}), ...(status !== 'ALL' ? { status } : {}) }).toString()}`),
      ]);
      setFindings(list.items ?? []);
      setCorrelations(groups.items ?? []);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not load findings.');
    } finally { setLoading(false); }
  }, [query, severity, status]);

  useEffect(() => { const timer = window.setTimeout(() => { void load(); }, 250); return () => window.clearTimeout(timer); }, [load]);

  const distribution = useMemo(() => severityOrder.map((item) => ({ severity: item, count: findings.filter((finding) => finding.severity.toUpperCase() === item).length })), [findings]);
  const maxSeverityCount = Math.max(1, ...distribution.map((item) => item.count));

  async function updateStatus(finding: Finding, nextStatus: string) {
    setError(''); setNotice('');
    try {
      const response = await apiRequest(`/api/findings/${encodeURIComponent(finding.finding_id)}/actions`, { method: 'POST', body: JSON.stringify({ action: 'set_status', status: nextStatus }) });
      const body = await response.json().catch(() => null);
      if (!response.ok) throw new Error(body?.detail ?? `Update failed (${response.status})`);
      setSelectedFinding(body.finding as Finding);
      setNotice(`Finding moved to ${nextStatus}.`);
      await load();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not update finding.'); }
  }

  return <div className="page-frame findings-explorer">
    <header className="page-heading"><div><p className="eyebrow">PHASE 5 / EVIDENCE &amp; CORRELATION</p><h1>Findings center</h1><p className="page-description">Investigate persisted observations, compare independent tool evidence, and move findings through triage.</p></div><button className="secondary-button" onClick={() => void load()}>Refresh <span>↻</span></button></header>
    <section className="finding-toolbar"><label className="finding-search"><span>⌕</span><input aria-label="Search findings" placeholder="Search title, asset, CVE or tool" value={query} onChange={(event) => setQuery(event.target.value)} /><kbd>/</kbd></label><label className="filter-select">SEVERITY<select aria-label="Filter by severity" value={severity} onChange={(event) => setSeverity(event.target.value)}><option value="ALL">All severities</option>{severityOrder.map((item) => <option key={item}>{item}</option>)}</select></label><label className="filter-select">STATUS<select aria-label="Filter by status" value={status} onChange={(event) => setStatus(event.target.value)}><option value="ALL">All statuses</option><option>OPEN</option><option>TRIAGED</option><option>IN_PROGRESS</option><option>RESOLVED</option><option>SUPPRESSED</option></select></label></section>
    {error && <div className="inline-error" role="alert">{error}</div>}{notice && <div className="success-message" role="status">{notice}</div>}
    <section className="finding-severity-strip" aria-label="Finding severity distribution">{distribution.map((item) => <button className={`severity-distribution ${tone(item.severity)}`} key={item.severity} onClick={() => setSeverity(severity === item.severity ? 'ALL' : item.severity)} aria-pressed={severity === item.severity}><span>{item.severity}</span><strong>{item.count}</strong><i><b style={{ width: `${(item.count / maxSeverityCount) * 100}%` }} /></i></button>)}</section>
    <div className="finding-view-tabs" role="tablist" aria-label="Findings views"><button role="tab" aria-selected={activeView === 'findings'} className={activeView === 'findings' ? 'active' : ''} onClick={() => { setActiveView('findings'); setSelectedCorrelation(null); }}>Finding explorer <b>{findings.length}</b></button><button role="tab" aria-selected={activeView === 'correlations'} className={activeView === 'correlations' ? 'active' : ''} onClick={() => { setActiveView('correlations'); setSelectedFinding(null); }}>Correlations <b>{correlations.length}</b></button><small>Persisted observations · derived groups</small></div>
    <div className={`findings-split ${activeView === 'correlations' ? 'correlation-mode' : ''}`}>
      <section className="finding-list" aria-label={activeView === 'findings' ? 'Finding list' : 'Correlation groups'}>
        {loading ? <div className="finding-empty">Loading persisted findings…</div> : activeView === 'findings' ? findings.length ? findings.map((finding) => <button className={`finding-row ${selectedFinding?.finding_id === finding.finding_id ? 'selected' : ''}`} key={finding.finding_id} onClick={() => setSelectedFinding(finding)}><span className={`finding-severity-mark ${tone(finding.severity)}`} /><span className="finding-row-content"><span className="finding-title-line"><strong>{finding.title}</strong><span className={`severity-pill ${tone(finding.severity)}`}>{finding.severity}</span></span><span className="finding-row-meta"><span>{finding.asset || 'Asset not specified'}</span>{finding.cve && <span>{finding.cve}</span>}<span>{finding.source_tool || 'Unattributed'}</span></span></span><span className="finding-risk"><strong>{finding.risk_score}</strong><small>RISK</small></span></button>) : <div className="finding-empty"><strong>No findings match these filters</strong><p>Ingest observations from an assessment to populate the explorer.</p></div> : correlations.length ? correlations.map((group) => <button className={`correlation-row ${selectedCorrelation?.correlation_id === group.correlation_id ? 'selected' : ''}`} key={group.correlation_id} onClick={() => setSelectedCorrelation(group)}><span className={`finding-severity-mark ${tone(group.severity)}`} /><span className="finding-row-content"><span className="finding-title-line"><strong>{group.title}</strong><span className="correlated-tag">CORRELATED</span></span><span className="finding-row-meta"><span>{group.asset}</span><span>{group.observation_count} observations</span><span>{group.source_tools.join(' + ')}</span></span></span><span className="finding-risk"><strong>{group.confidence * 100}%</strong><small>CONFIDENCE</small></span></button>) : <div className="finding-empty"><strong>No correlated findings yet</strong><p>Correlation appears when an assessment has matching evidence from more than one observation.</p></div>}
      </section>
      {activeView === 'findings' && selectedFinding && <FindingDetail finding={selectedFinding} onStatusChange={(next) => void updateStatus(selectedFinding, next)} />}
      {activeView === 'correlations' && selectedCorrelation && <CorrelationDetail group={selectedCorrelation} />}
      {!selectedFinding && !selectedCorrelation && <aside className="finding-detail-placeholder"><span>◉</span><strong>Select a {activeView === 'findings' ? 'finding' : 'correlation'}</strong><p>Inspect risk, source observations and evidence here without losing your place in the list.</p></aside>}
    </div>
  </div>;
}

function FindingDetail({ finding, onStatusChange }: { finding: Finding; onStatusChange: (status: string) => void }) {
  return <aside className="finding-detail-panel"><div className="finding-detail-header"><span className={`severity-pill ${tone(finding.severity)}`}>{finding.severity}</span><span className="finding-id">{finding.finding_id}</span></div><h2>{finding.title}</h2><p className="finding-description">{finding.description || 'No description was provided by the source observation.'}</p><div className="finding-score-block"><div><small>RISK SCORE</small><strong>{finding.risk_score}<i>/100</i></strong></div><div><small>CONFIDENCE</small><strong>{Math.round(finding.confidence * 100)}<i>%</i></strong></div></div><dl className="finding-attributes">{[['Asset', finding.asset], ['CVE', finding.cve], ['CWE', finding.cwe], ['Tool', finding.source_tool], ['Exploitability', finding.exploitability], ['Validation', finding.validation_status], ['Exposure', finding.exposure]].filter(([, value]) => value).map(([label, value]) => <div key={String(label)}><dt>{label}</dt><dd>{String(value)}</dd></div>)}</dl><section className="finding-evidence"><h3>Source evidence</h3>{finding.evidence.length ? finding.evidence.map((item, index) => <pre key={index}>{evidenceText(item)}</pre>) : <p>No evidence payload was provided.</p>}</section>{finding.remediation && <section className="finding-evidence"><h3>Remediation</h3><p>{finding.remediation}</p></section>}<label className="finding-status-control">UPDATE STATUS<select aria-label="Update finding status" value={finding.status} onChange={(event) => onStatusChange(event.target.value)}><option>OPEN</option><option>TRIAGED</option><option>IN_PROGRESS</option><option>RESOLVED</option><option>SUPPRESSED</option></select></label></aside>;
}

function CorrelationDetail({ group }: { group: Correlation }) {
  return <aside className="finding-detail-panel"><div className="finding-detail-header"><span className="correlated-tag">CORRELATION / {group.correlation_id}</span><span className={`severity-pill ${tone(group.severity)}`}>{group.severity}</span></div><h2>{group.title}</h2><p className="finding-description">{group.observation_count} observations map to one issue fingerprint on {group.asset}.</p><div className="finding-score-block"><div><small>MAX RISK</small><strong>{group.risk_score}<i>/100</i></strong></div><div><small>CONFIDENCE</small><strong>{Math.round(group.confidence * 100)}<i>%</i></strong></div></div><section className="finding-evidence"><h3>Why these were grouped</h3>{group.rules.map((rule) => <div className="correlation-rule" key={rule}><span>✓</span>{rule}</div>)}<p>Fingerprint: <code>{group.fingerprint.type}: {group.fingerprint.value}</code></p></section><section className="finding-evidence"><h3>Independent sources</h3><div className="source-chips">{group.source_tools.map((tool) => <span key={tool}>{tool}</span>)}</div>{group.evidence.map((item, index) => <div className="correlated-evidence" key={`${item.finding_id}-${index}`}><small>{item.source_tool} · {item.finding_id}</small><pre>{evidenceText(item.value)}</pre></div>)}</section></aside>;
}
