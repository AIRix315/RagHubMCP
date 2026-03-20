import { defineConfig, configDefaults } from 'vitest/config'
import viteConfig from './vite.config'

export default defineConfig({
  ...viteConfig,
  test: {
    environment: 'jsdom',
    exclude: [...configDefaults.exclude, 'e2e/**'],
    globals: true,
    coverage: {
      exclude: [
        'postcss.config.js',
        'tailwind.config.js',
        'src/types/*.ts',
        'src/main.ts',
        'vite.config.ts',
        'vitest.config.ts',
        'dist/**',
      ],
    },
  },
})