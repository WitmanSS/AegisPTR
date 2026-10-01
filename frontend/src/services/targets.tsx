import { apiRequest } from './api';

async function readResponse<T>(response: Response): Promise<T> {
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(body?.detail ?? `Request failed (${response.status})`);
  }
  return body as T;
}

export type TargetPreview = {
  count: number;
  overlaps: string[][];
  items: Array<{
    original: string;
    canonical?: string;
    type?: string;
    status?: string;
    validation?: { valid: boolean; errors?: string[] };
  }>;
};

export type BulkCreateResult = {
  total: number;
  created: number;
  failed: number;
  items?: Array<{ original: string; status: string; error?: string | null }>;
};

export async function previewBulk(text: string, resolve = false): Promise<TargetPreview> {
  const res = await apiRequest('/api/targets/bulk/preview', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, resolve }),
  });
  return readResponse<TargetPreview>(res);
}

export async function bulkCreate(items: Array<{ original: string; canonical: string; target_type: string }>): Promise<BulkCreateResult> {
  const res = await apiRequest('/api/targets/bulk', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items }),
  });
  return readResponse<BulkCreateResult>(res);
}
