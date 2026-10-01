import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAssessments, getHealth, getMonitoringSummary, getRemediationPlans, getRetests } from '../services/api';

type Summary = {
  status?: string;
  mttd_hours?: number;
  mttr_hours?: number;
  closure_rate_percent?: number;
  risk_reduction_percent?: number;
  open_findings?: number;
  critical_findings?: number;
};

type LoadState = 'loading' | 'ready' | 'error';

export function Dashboard() {
  const navigate = useNavigate();
  const [health, setHealth] = useState<{ status?: string } | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [assessments, setAssessments] = useState<any[]>([]);
  const [plans, setPlans] = useState<any[]>([]);
  const [retests, setRetests] = useState<any[]>([]);
  const [state, setState] = useState<LoadState>('loading');

  useEffect(() => {
    let active = true;
    Promise.allSettled([getHealth(), getAssessments(), getMonitoringSummary(), getRemediationPlans(), getRetests()]).then((results) => {
      if (!active) return;
      const [healthResult, assessmentResult, summaryResult, plansResult, retestsResult] = results;
      if (healthResult.status === 'fulfilled') setHealth(healthResult.value);
      if (assessmentResult.status === 'fulfilled' && Array.isArray(assessmentResult.value)) setAssessments(assessmentResult.value);
      if (summaryResult.status === 'fulfilled') setSummary(summaryResult.value);
      if (plansResult.status === 'fulfilled' && Array.isArray(plansResult.value)) setPlans(plansResult.value);
      if (retestsResult.status === 'fulfilled' && Array.isArray(retestsResult.value)) setRetests(retestsResult.value);
      setState(results.every((result) => result.status === 'fulfilled') ? 'ready' : 'error');
    });
    return () => { active = false; };
  }, []);

  const activeAssessments = assessments.filter((item) => !['COMPLETED', 'CLOSED', 'FAILED'].includes(String(item.status).toUpperCase()));
  const recentAssessments = assessments.slice(0, 3);

  return <div className="page-frame command-center">
    <section className="hero-heading">
      <div><p className="eyebrow">SECURITY COMMAND CENTER <span className="eyebrow-line" /></p><h1>See what matters.<br /><em>Act with evidence.</em></h1><p className="hero-copy">Your authorized security operation, connected from first target to verified fix.</p></div>
      <div className="hero-meta"><span className={`health-indicator ${health?.status === 'ok' ? 'online' : ''}`}><i />{health?.status === 'ok' ? 'API connected' : health?.status === 'offline' ? 'API offline' : 'Connecting'}</span><small>ASSESSMENT CONTEXT<br /><strong>{activeAssessments[0]?.name ?? 'No active assessment'}</strong></small></div>
    </section>

    <section className="posture-strip" aria-label="Current security indicators">
      <div className="posture-score"><div className="score-mark">A</div><div><small>POSTURE SUMMARY</small><h2>{summary?.status === 'ok' ? 'Configured KPI values' : 'Awaiting monitoring data'}</h2><p>Not yet calculated from persisted finding records.</p></div></div>
      <div className="posture-divider" />
      <Metric label="OPEN FINDINGS" value={summary?.open_findings} detail={summary?.critical_findings === undefined ? 'Unavailable' : `${summary.critical_findings} critical`} tone="critical" />
      <Metric label="RISK REDUCTION" value={summary?.risk_reduction_percent} suffix="%" detail="Monitoring KPI" tone="green" />
      <Metric label="ACTIVE ASSESSMENTS" value={activeAssessments.length} detail={`${assessments.length} total`} tone="blue" />
    </section>

    {state === 'error' && <div className="inline-alert" role="status"><span>!</span><div><strong>Some data could not be loaded</strong><p>Unavailable panels are left empty rather than filled with sample activity.</p></div><button className="text-button" onClick={() => window.location.reload()}>Retry</button></div>}

    <div className="section-label"><span>ATTENTION REQUIRED</span><i /><button onClick={() => navigate('/findings')}>Open findings explorer ↗</button></div>
    <section className="attention-grid">
      <button className="attention-card critical-card" onClick={() => navigate('/findings')}><span className="severity-icon">!</span><div><small>CRITICAL EXPOSURE</small><strong>{summary?.critical_findings ?? '—'} critical findings</strong><p>{summary ? 'Reported by current monitoring summary.' : 'Monitoring summary is unavailable.'}</p></div><span className="card-arrow">↗</span></button>
      <button className="attention-card amber-card" onClick={() => navigate('/remediation')}><span className="severity-icon">↗</span><div><small>REMEDIATION COVERAGE</small><strong>{summary?.closure_rate_percent ?? '—'}{summary?.closure_rate_percent !== undefined ? '%' : ''} closure rate</strong><p>{plans.length} remediation plans available.</p></div><span className="card-arrow">↗</span></button>
      <button className="attention-card blue-card" onClick={() => navigate('/retesting')}><span className="severity-icon">✓</span><div><small>VERIFICATION QUEUE</small><strong>{retests.length} retests recorded</strong><p>Review evidence and validation status.</p></div><span className="card-arrow">↗</span></button>
    </section>

    <div className="command-grid">
      <section className="surface-panel operations-panel"><div className="panel-heading"><div><small>ASSESSMENT WORKSPACE</small><h2>Current operations</h2></div><button className="text-button" onClick={() => navigate('/assessments')}>All assessments ↗</button></div>
        {state === 'loading' ? <div className="empty-inline">Loading assessment state...</div> : recentAssessments.length ? <div className="operation-list">{recentAssessments.map((item) => <button className="operation-row assessment-row" key={item.id} onClick={() => navigate('/assessments')}><div className="tool-icon blue">◈</div><div className="operation-name"><strong>{item.name}</strong><small>{item.assessment_type ?? 'Assessment'} · {item.client ?? 'Client not set'}</small></div><span className={`status-tag ${String(item.status).toLowerCase() === 'authorized' ? 'success' : 'blue'}`}>{item.status}</span><span className="row-arrow">→</span></button>)}</div> : <div className="empty-state"><span>◈</span><strong>No assessments yet</strong><p>Create an assessment and define its authorized scope to begin.</p><button className="secondary-button" onClick={() => navigate('/assessments')}>Open assessments ↗</button></div>}
      </section>
      <section className="surface-panel surface-map-panel"><div className="panel-heading"><div><small>AUTHORIZED SCOPE</small><h2>Target control</h2></div><button className="text-button" onClick={() => navigate('/targets/bulk')}>Manage targets ↗</button></div><div className="scope-preview"><div className="scope-symbol">◎</div><div><strong>{assessments.length ? 'Assessment scope' : 'No target scope configured'}</strong><p>{assessments.length ? `${assessments.length} assessment records available` : 'Add and validate targets before starting operations.'}</p></div><span className="scope-state">{assessments.length ? 'REVIEW' : 'EMPTY'}</span></div><div className="scope-flow"><span>Targets</span><i /><span>Scope approval</span><i /><span>Operations</span></div><button className="secondary-button full-button" onClick={() => navigate('/targets/bulk')}>Open target control board <span>↗</span></button></section>
    </div>

    <div className="command-grid lower-grid">
      <section className="surface-panel ai-panel"><div className="ai-panel-head"><div className="ai-sigil">✦</div><div><small>AI COPILOT</small><h2>Contextual analysis is not connected</h2></div><span className="status-tag muted-tag">API REQUIRED</span></div><p>The current backend does not expose a copilot endpoint. Findings and assessment data are not sent to an external model.</p><div className="ai-reason"><span>✓</span> No invented recommendations <span>✓</span> Evidence stays local</div><div className="panel-actions"><button className="primary-button" onClick={() => navigate('/ai')}>Open copilot workspace <span>↗</span></button></div></section>
      <section className="surface-panel trend-panel"><div className="panel-heading"><div><small>REMEDIATION METRICS</small><h2>Time to respond</h2></div><span className="status-tag blue">API KPI</span></div><div className="response-metrics"><div><small>DETECTION</small><strong>{summary?.mttd_hours ?? '—'}<i>h</i></strong><span>Mean time to detect</span></div><div><small>REMEDIATION</small><strong>{summary?.mttr_hours ?? '—'}<i>h</i></strong><span>Mean time to remediate</span></div></div><div className="metric-footnote">No historical series endpoint is available for a trend chart.</div></section>
    </div>

    <section className="activity-section"><div className="section-label"><span>ASSESSMENT SNAPSHOT</span><i /><button onClick={() => navigate('/reports')}>Open reports ↗</button></div><div className="activity-feed">{recentAssessments.length ? recentAssessments.map((item) => <div className="activity-row" key={item.id}><time>{item.status}</time><span className="activity-dot blue" /><div><strong>{item.name}</strong><p>{item.assessment_type ?? 'Assessment'} · {item.client ?? 'Client not set'}</p></div><span className="activity-context">{item.is_authorized ? 'AUTHORIZED' : 'SCOPE REVIEW'}</span></div>) : <div className="empty-inline">Assessment activity appears here when assessments are created.</div>}</div></section>
    <div className="dashboard-footer"><span><i className={`status-dot ${health?.status === 'ok' ? '' : 'offline'}`} /> API {health?.status === 'ok' ? 'connected' : 'not connected'}</span><span>{plans.length} remediation plans · {retests.length} retests · {assessments.length} assessments</span></div>
  </div>;
}

function Metric({ label, value, suffix = '', detail, tone }: { label: string; value?: number; suffix?: string; detail: string; tone: string }) {
  return <div className={`posture-stat ${tone}`}><small>{label}</small><strong>{value === undefined ? '—' : `${value}${suffix}`}</strong><span className="stat-change">{detail}</span></div>;
}
