import React from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import { AICopilot } from '../AICopilot';

const apiMocks = vi.hoisted(() => ({ apiRequest: vi.fn(), getResource: vi.fn() }));
vi.mock('../../services/api', () => apiMocks);

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

test('asks with assessment context and renders server-provided evidence citations', async () => {
  const finding = { finding_id: 'F-AI-001', assessment_id: 'A-1', title: 'RCE in API dependency', severity: 'CRITICAL', risk_score: 96, asset: 'api.example.com', status: 'OPEN', source_tool: 'nuclei' };
  apiMocks.getResource.mockImplementation(async (path: string) => {
    if (path === '/api/assessments') return [{ id: 'A-1', name: 'External review', status: 'AUTHORIZED', is_authorized: true }];
    if (path.startsWith('/api/findings/explorer')) return { items: [finding], page: { total: 1 } };
    return { provider: 'evidence-only', model: 'local retrieval', status: 'ready', mode: 'read_only' };
  });
  apiMocks.apiRequest.mockResolvedValue(new Response(JSON.stringify({
    answer: 'The highest risk match is F-AI-001 at api.example.com with risk score 96/100.',
    classification: 'EVIDENCE_SUMMARY', provider: 'evidence-only', model: 'local retrieval',
    provider_status: 'ready', confidence: null, evidence: [{ ...finding, evidence: ['persisted evidence'] }],
    evidence_count: 1, read_only: true, actions_executed: [], notice: 'Evidence-only response.',
  }), { status: 200 }));

  render(<AICopilot />);
  fireEvent.click(await screen.findByRole('button', { name: /which findings have the highest risk/i }));
  await waitFor(() => expect(apiMocks.apiRequest).toHaveBeenCalledWith('/api/ai/ask', expect.objectContaining({ method: 'POST' })));
  expect(await screen.findByText(/highest risk match is F-AI-001/i)).toBeInTheDocument();
  expect(screen.getByText(/F-AI-001 · RCE in API dependency/i)).toBeInTheDocument();
  expect(screen.getByText(/No actions enabled/i)).toBeInTheDocument();
});

test('does not imply AI is configured when provider is disabled', async () => {
  apiMocks.getResource.mockImplementation(async (path: string) => path === '/api/assessments'
    ? []
    : path.startsWith('/api/findings/explorer') ? { items: [], page: { total: 0 } } : { provider: 'evidence-only', model: 'local retrieval', status: 'ready', mode: 'read_only' });

  render(<AICopilot />);
  expect(await screen.findByText(/Database-backed evidence assistant/i)).toBeInTheDocument();
  expect(await screen.findByText(/No persisted findings yet/i)).toBeInTheDocument();
});
