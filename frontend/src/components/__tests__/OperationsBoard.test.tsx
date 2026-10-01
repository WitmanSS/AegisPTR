import React from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import { OperationsBoard } from '../OperationsBoard';

const apiMocks = vi.hoisted(() => ({ apiRequest: vi.fn(), getResource: vi.fn() }));
vi.mock('../../services/api', () => apiMocks);

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

test('shows queued task and requires confirmation before executing it', async () => {
  const operation = {
    task_id: 'task-12345678',
    assessment_id: 'assessment-1',
    tool_id: 'nmap',
    target: 'example.com',
    status: 'QUEUED',
  };
  apiMocks.getResource.mockImplementation(async (path: string) => {
    if (path === '/api/assessments') return [{ id: 'assessment-1', name: 'External test', status: 'AUTHORIZED', is_authorized: true, scope_text: 'example.com' }];
    if (path === '/api/tools/inventory') return { tools: { nmap: { available: true, status: 'ready', version: 'test' } } };
    return [operation];
  });
  apiMocks.apiRequest.mockResolvedValue(new Response(JSON.stringify({
    ...operation,
    status: 'SUCCESS',
    exit_code: 0,
    parsed_results: [{ title: 'Network service detected', evidence: '443/tcp open' }],
  }), { status: 200 }));
  vi.spyOn(window, 'confirm').mockReturnValue(true);

  render(<OperationsBoard />);
  const runButton = await screen.findByRole('button', { name: /run now/i });
  fireEvent.click(runButton);

  await waitFor(() => expect(apiMocks.apiRequest).toHaveBeenCalledWith('/api/tasks/task-12345678/execute', { method: 'POST' }));
  expect(window.confirm).toHaveBeenCalledWith(expect.stringContaining('example.com'));
  expect(await screen.findByText(/execution finished with status success/i)).toBeInTheDocument();
});

test('locks operation creation when there are no authorized assessments', async () => {
  apiMocks.getResource.mockImplementation(async (path: string) => {
    if (path === '/api/assessments') return [{ id: 'assessment-1', name: 'Draft test', status: 'DRAFT', is_authorized: false, scope_text: 'example.com' }];
    if (path === '/api/tools/inventory') return { tools: {} };
    return [];
  });

  render(<OperationsBoard />);
  expect(await screen.findByText(/no authorized assessment/i)).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /queue operation/i }));
  expect(screen.getByText(/no authorized assessment/i)).toBeInTheDocument();
});
