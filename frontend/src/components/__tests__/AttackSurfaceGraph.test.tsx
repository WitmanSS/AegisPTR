import React from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import { AttackSurfaceGraph } from '../AttackSurfaceGraph';

const mocks = vi.hoisted(() => {
  const layout = { run: vi.fn() };
  const collection = { removeClass: vi.fn(), addClass: vi.fn(), connectedEdges: vi.fn(), connectedNodes: vi.fn() };
  collection.connectedEdges.mockReturnValue(collection);
  collection.connectedNodes.mockReturnValue(collection);
  const cy = {
    on: vi.fn(), elements: vi.fn(() => ({ remove: vi.fn() })), add: vi.fn(),
    layout: vi.fn(() => layout), fit: vi.fn(), zoom: vi.fn(() => 1), width: vi.fn(() => 500), height: vi.fn(() => 400),
    nodes: vi.fn(() => ({ filter: vi.fn(() => collection) })), destroy: vi.fn(),
  };
  return { cy, layout, getResource: vi.fn() };
});

vi.mock('cytoscape', () => ({ default: vi.fn(() => mocks.cy) }));
vi.mock('../../services/api', () => ({ getResource: mocks.getResource }));

afterEach(() => { cleanup(); vi.clearAllMocks(); });

const emptyGraph = { elements: { nodes: [], edges: [] }, counts: { nodes: 0, edges: 0 } };

test('loads graph data and refetches with assessment and severity filters', async () => {
  mocks.getResource.mockImplementation(async (path: string) => path === '/api/assessments'
    ? [{ id: 'A-1', name: 'External review', is_authorized: true, status: 'AUTHORIZED' }]
    : emptyGraph);

  render(<AttackSurfaceGraph />);
  expect(await screen.findByText(/No graph data yet/i)).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Filter graph assessment'), { target: { value: 'A-1' } });
  await waitFor(() => expect(mocks.getResource).toHaveBeenCalledWith(expect.stringContaining('assessment_id=A-1')));
  fireEvent.change(screen.getByLabelText('Filter graph severity'), { target: { value: 'HIGH' } });
  await waitFor(() => expect(mocks.getResource).toHaveBeenCalledWith(expect.stringContaining('severity=HIGH')));
});

test('allows switching layout and fitting the graph viewport', async () => {
  mocks.getResource.mockResolvedValue(emptyGraph);
  render(<AttackSurfaceGraph />);
  const switchLayout = await screen.findByRole('button', { name: /layout: force/i });
  fireEvent.click(switchLayout);
  expect(await screen.findByRole('button', { name: /layout: hierarchy/i })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /fit graph/i }));
  expect(mocks.cy.fit).toHaveBeenCalled();
});
