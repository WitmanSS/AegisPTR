import React from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import App from '../App';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test('sign-in opens the operations shell and authenticated search palette', async () => {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith('/api/auth/login')) {
      return new Response(JSON.stringify({ access_token: 'test-token', token_type: 'bearer', role: 'admin' }), { status: 200 });
    }
    if (url.endsWith('/api/health')) return new Response(JSON.stringify({ status: 'ok' }), { status: 200 });
    if (url.endsWith('/api/assessments')) return new Response(JSON.stringify([]), { status: 200 });
    if (url.endsWith('/api/monitoring/summary')) return new Response(JSON.stringify({ status: 'ok', open_findings: 0, critical_findings: 0 }), { status: 200 });
    if (url.endsWith('/api/remediation/plans') || url.endsWith('/api/retests')) return new Response(JSON.stringify([]), { status: 200 });
    return new Response(JSON.stringify({ detail: 'Not found' }), { status: 404 });
  });
  vi.stubGlobal('fetch', fetchMock);

  render(<App />);
  fireEvent.change(screen.getByLabelText('USERNAME'), { target: { value: 'admin' } });
  fireEvent.change(screen.getByLabelText('PASSWORD'), { target: { value: 'strong-password' } });
  fireEvent.submit(screen.getByLabelText('USERNAME').closest('form')!);
  await waitFor(() => expect(fetchMock).toHaveBeenCalledWith('/api/auth/login', expect.anything()));

  expect(await screen.findByRole('link', { name: /command center/i })).toBeInTheDocument();
  await waitFor(() => expect(screen.getByText('API connected')).toBeInTheDocument());
  expect(fetchMock.mock.calls.some(([url, init]) => String(url).endsWith('/api/assessments') && new Headers(init?.headers).get('Authorization') === 'Bearer test-token')).toBe(true);

  fireEvent.click(screen.getByRole('button', { name: /search anything/i }));
  expect(screen.getByRole('dialog', { name: /command palette/i })).toBeInTheDocument();
  expect(screen.getByPlaceholderText(/search assets, findings, commands/i)).toHaveFocus();
});
