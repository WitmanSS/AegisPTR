const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';
let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export async function apiRequest(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`);
  return fetch(`${API_BASE_URL}${path}`, { ...init, headers });
}

export async function getResource<T = unknown>(path: string): Promise<T> {
  const response = await apiRequest(path);
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(body?.detail ?? `API request failed: ${response.status}`);
  }
  return body as T;
}

export async function login(username: string, password: string) {
  const response = await apiRequest('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new Error(body?.detail ?? `Login failed (${response.status})`);
  return body as { access_token: string; token_type: string; role: string };
}

export async function getHealth() {
  return getResource<{ status?: string }>('/api/health');
}

export async function getAssessments() {
  return getResource('/api/assessments');
}

export async function getMonitoringSummary() {
  return getResource<{
    status?: string;
    mttd_hours?: number;
    mttr_hours?: number;
    closure_rate_percent?: number;
    risk_reduction_percent?: number;
    open_findings?: number;
    critical_findings?: number;
  }>('/api/monitoring/summary');
}

export async function getRemediationPlans() {
  return getResource('/api/remediation/plans');
}

export async function getRetests() {
  return getResource('/api/retests');
}
