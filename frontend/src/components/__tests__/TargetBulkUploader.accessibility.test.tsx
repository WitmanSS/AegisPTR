import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import TargetBulkUploader from '../TargetBulkUploader'
import { vi, expect, test } from 'vitest'

vi.mock('../../services/targets', () => ({
  previewBulk: async () => ({
    count: 2,
    overlaps: [],
    items: [
      { original: '1.1.1.1', canonical: '1.1.1.1', type: 'ip', validation: { valid: true } },
      { original: 'example.com', canonical: 'example.com', type: 'fqdn', validation: { valid: true } },
    ],
  }),
  bulkCreate: async () => ({ created: 2, total: 2, failed: 0 }),
}))

test('TargetBulkUploader renders preview and modal with correct ARIA attributes', async () => {
  render(<TargetBulkUploader />)

  // Trigger preview
  const previewBtn = screen.getByText('Parse Preview')
  fireEvent.click(previewBtn)

  // Wait for preview items to render
  await waitFor(() => expect(screen.getByText('1.1.1.1')).toBeTruthy())

  // Check that per-row inputs have aria-labels
  expect(screen.getByLabelText('Select 1.1.1.1')).toBeInTheDocument()
  expect(screen.getByLabelText('Canonical for 1.1.1.1')).toBeInTheDocument()
  expect(screen.getByLabelText('Type for 1.1.1.1')).toBeInTheDocument()

  // Open confirmation modal
  const addBtn = screen.getByText('Add to Scope')
  fireEvent.click(addBtn)

  // Modal should appear with role dialog and labelledby
  const dialog = await waitFor(() => screen.getByRole('dialog'))
  expect(dialog).toHaveAttribute('aria-modal', 'true')
  expect(screen.getByText(/Confirm Add to Scope/i)).toBeInTheDocument()
})
