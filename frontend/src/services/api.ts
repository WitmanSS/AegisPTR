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
