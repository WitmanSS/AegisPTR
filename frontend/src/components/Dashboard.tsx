import { useEffect, useState } from 'react';
import { getAssessments, getHealth } from '../services/api';

export function Dashboard() {
  const [health, setHealth] = useState<{ status?: string } | null>(null);
  const [assessments, setAssessments] = useState<any[]>([]);

  useEffect(() => {
    getHealth().then((data) => setHealth(data)).catch(() => setHealth({ status: 'offline' }));
    getAssessments().then((data) => setAssessments(data)).catch(() => setAssessments([]));
  }, []);

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
        <article className="stat-card critical">
          <span>Critical</span>
          <strong>8</strong>
        </article>
        <article className="stat-card high">
          <span>High</span>
          <strong>21</strong>
        </article>
        <article className="stat-card medium">
          <span>Medium</span>
          <strong>54</strong>
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
    </main>
  );
}
