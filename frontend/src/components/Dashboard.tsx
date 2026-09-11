import { useEffect, useState } from 'react';
import {
  getAssessments,
  getHealth,
  getMonitoringSummary,
  getRemediationPlans,
  getRetests,
} from '../services/api';

type MonitoringSummary = {
  status?: string;
  mttd_hours?: number;
  mttr_hours?: number;
  closure_rate_percent?: number;
  risk_reduction_percent?: number;
  open_findings?: number;
  critical_findings?: number;
};

export function Dashboard() {
  const [health, setHealth] = useState<{ status?: string } | null>(null);
  const [assessments, setAssessments] = useState<any[]>([]);
  const [summary, setSummary] = useState<MonitoringSummary | null>(null);
  const [plans, setPlans] = useState<any[]>([]);
  const [retests, setRetests] = useState<any[]>([]);

  useEffect(() => {
    getHealth().then((data) => setHealth(data)).catch(() => setHealth({ status: 'offline' }));
    getAssessments().then((data) => setAssessments(data)).catch(() => setAssessments([]));
    getMonitoringSummary().then((data) => setSummary(data)).catch(() => setSummary(null));
    getRemediationPlans().then((data) => setPlans(data)).catch(() => setPlans([]));
    getRetests().then((data) => setRetests(data)).catch(() => setRetests([]));
  }, []);

  const metricCards = [
    { label: 'Critical findings', value: summary?.critical_findings ?? 0, tone: 'critical' },
    { label: 'Open findings', value: summary?.open_findings ?? 0, tone: 'high' },
    { label: 'Closure rate', value: `${summary?.closure_rate_percent ?? 0}%`, tone: 'medium' },
  ];

  return (
    <main className="dashboard-shell">
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">AEGIS PTR</p>
          <h1>Security Operations Dashboard</h1>
        </div>
        <div className="status-pill">Status: {health?.status ?? 'checking...'}</div>
      </header>

      <section className="stats-grid">
        {metricCards.map((card) => (
          <article key={card.label} className={`stat-card ${card.tone}`}>
            <span>{card.label}</span>
            <strong>{card.value}</strong>
          </article>
        ))}
      </section>

      <section className="metrics-row">
        <article className="mini-card">
          <span>MTTD</span>
          <strong>{summary?.mttd_hours ?? 0}h</strong>
        </article>
        <article className="mini-card">
          <span>MTTR</span>
          <strong>{summary?.mttr_hours ?? 0}h</strong>
        </article>
        <article className="mini-card">
          <span>Risk reduction</span>
          <strong>{summary?.risk_reduction_percent ?? 0}%</strong>
        </article>
      </section>

      <section className="panel-grid">
        <article className="panel">
          <h2>Assessment Overview</h2>
          {assessments.length ? (
            assessments.map((assessment) => (
              <div key={assessment.id} className="assessment-item">
                <strong>{assessment.name}</strong>
                <p>{assessment.status}</p>
              </div>
            ))
          ) : (
            <p>No active assessments.</p>
          )}
        </article>

        <article className="panel">
          <h2>Risk Trend</h2>
          <div className="chart-bars">
            <span style={{ height: '60%' }} />
            <span style={{ height: '80%' }} />
            <span style={{ height: '70%' }} />
            <span style={{ height: '55%' }} />
            <span style={{ height: '40%' }} />
          </div>
        </article>
      </section>

      <section className="panel-grid bottom-grid">
        <article className="panel">
          <h2>Remediation Plans</h2>
          {plans.length ? (
            plans.map((plan) => (
              <div key={plan.plan_id} className="assessment-item">
                <strong>{plan.plan_id}</strong>
                <p>{plan.status}</p>
              </div>
            ))
          ) : (
            <p>No remediation plans yet.</p>
          )}
        </article>

        <article className="panel">
          <h2>Retest Queue</h2>
          {retests.length ? (
            retests.map((item) => (
              <div key={item.retest_id} className="assessment-item">
                <strong>{item.finding_id}</strong>
                <p>{item.status}</p>
              </div>
            ))
          ) : (
            <p>No retests scheduled.</p>
          )}
        </article>
      </section>
    </main>
  );
}
