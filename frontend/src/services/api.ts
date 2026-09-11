export async function getHealth() {
  const response = await fetch('http://localhost:8000/api/health');
  if (!response.ok) {
    throw new Error('Health check failed');
  }
  return response.json();
}

export async function getAssessments() {
  const response = await fetch('http://localhost:8000/api/assessments');
  if (!response.ok) {
    throw new Error('Assesments fetch failed');
  }
  return response.json();
}

export async function getMonitoringSummary() {
  const response = await fetch('http://localhost:8000/api/monitoring/summary');
  if (!response.ok) {
    throw new Error('Monitoring summary fetch failed');
  }
  return response.json();
}

export async function getRemediationPlans() {
  const response = await fetch('http://localhost:8000/api/remediation/plans');
  if (!response.ok) {
    throw new Error('Remediation plans fetch failed');
  }
  return response.json();
}

export async function getRetests() {
  const response = await fetch('http://localhost:8000/api/retests');
  if (!response.ok) {
    throw new Error('Retests fetch failed');
  }
  return response.json();
}
