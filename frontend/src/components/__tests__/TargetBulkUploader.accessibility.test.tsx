import React from 'react'
import { render } from '@testing-library/react'
import TargetBulkUploader from '../TargetBulkUploader'
import axe from 'axe-core'
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

test('TargetBulkUploader has no accessibility violations (basic)', async () => {
  const { container } = render(<TargetBulkUploader />)
  const results = await axe.run(container)
  expect(results.violations).toHaveLength(0)
})
