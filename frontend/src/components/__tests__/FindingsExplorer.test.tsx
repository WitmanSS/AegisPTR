import React from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import { FindingsExplorer } from '../FindingsExplorer';

const apiMocks = vi.hoisted(() => ({ apiRequest: vi.fn(), getResource: vi.fn() }));
vi.mock('../../services/api', () => apiMocks);

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

const finding = {
  finding_id: 'F-ABC123', assessment_id: 'A-1', title: 'Remote code execution in package',
  description: 'A vulnerable dependency is exposed.', severity: 'CRITICAL', risk_score: 94,
  confidence: 0.92, asset: 'api.example.com', cve: 'CVE-2025-1234', source_tool: 'nuclei',
  status: 'OPEN', evidence: ['matched template'], remediation: 'Upgrade the dependency',
};

test('filters persisted findings and shows evidence in the split detail panel', async () => {
  apiMocks.getResource.mockImplementation(async (url: string) => url.startsWith('/api/findings/explorer')
    ? { items: [finding], page: { page: 1, size: 25, total: 1 } }
    : { items: [] });

  render(<FindingsExplorer />);
  expect(await screen.findByText('Remote code execution in package')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /remote code execution in package/i }));
  expect(await screen.findByText('matched template')).toBeInTheDocument();
  expect(screen.getAllByText('CVE-2025-1234').length).toBeGreaterThan(0);
  fireEvent.change(screen.getByLabelText('Filter by severity'), { target: { value: 'CRITICAL' } });
  await waitFor(() => expect(apiMocks.getResource).toHaveBeenCalledWith(expect.stringContaining('severity=CRITICAL')));
});

test('correlation view explains matched observations from independent tools', async () => {
  const group = {
    correlation_id: 'COR-123', assessment_id: 'A-1', asset: 'api example com',
    fingerprint: { type: 'cve', value: 'cve 2025 1234' }, title: finding.title,
    severity: 'CRITICAL', risk_score: 94, confidence: 0.91, observation_count: 2,
    source_tools: ['nuclei', 'zap'], merged_from: ['F-ABC123', 'F-DEF456'],
    statuses: ['OPEN'], rules: ['same assessment', 'same normalized asset', 'same vulnerability fingerprint'],
    evidence: [{ source_tool: 'nuclei', finding_id: 'F-ABC123', value: 'template matched' }],
  };
  apiMocks.getResource.mockImplementation(async (url: string) => url.startsWith('/api/findings/explorer')
    ? { items: [finding], page: { page: 1, size: 25, total: 1 } }
    : { items: [group] });

  render(<FindingsExplorer />);
  fireEvent.click(await screen.findByRole('tab', { name: /correlations/i }));
  fireEvent.click(await screen.findByRole('button', { name: /correlated/i }));
  expect(await screen.findByText('same vulnerability fingerprint')).toBeInTheDocument();
  expect(screen.getByText('nuclei + zap')).toBeInTheDocument();
});
