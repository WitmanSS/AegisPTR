import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: './vitest.setup.ts',
    include: ['src/**/*.test.*', 'src/**/*.spec.*', 'src/**/__tests__/**/*.{test,spec}.{ts,tsx,js,jsx}'],
  },
})
