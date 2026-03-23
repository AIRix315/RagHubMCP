/**
 * Global test setup for Vitest
 * Provides mocks and plugins commonly needed by component tests
 */
import { vi } from 'vitest'

// Mock lucide-vue-next icons - export all icons as simple mock components
vi.mock('lucide-vue-next', async () => {
  // Create a mock component factory that renders SVG
  const createMockIcon = (name: string) => ({
    name,
    template: `<svg class="icon-${name.toLowerCase()}" />`,
    props: ['class', 'size'],
  })

  // Common icons used across components
  return {
    Home: createMockIcon('home'),
    Settings: createMockIcon('settings'),
    Database: createMockIcon('database'),
    BarChart3: createMockIcon('chart'),
    SlidersHorizontal: createMockIcon('sliders'),
    Languages: createMockIcon('languages'),
    Sun: createMockIcon('sun'),
    Moon: createMockIcon('moon'),
    Zap: createMockIcon('zap'),
    Plus: createMockIcon('plus'),
    Trash2: createMockIcon('trash'),
    RefreshCw: createMockIcon('refresh'),
    Eye: createMockIcon('eye'),
    Search: createMockIcon('search'),
    FileText: createMockIcon('filetext'),
    Clock: createMockIcon('clock'),
    Brain: createMockIcon('brain'),
    Cpu: createMockIcon('cpu'),
    Play: createMockIcon('play'),
    Download: createMockIcon('download'),
    Star: createMockIcon('star'),
    AlertCircle: createMockIcon('alert'),
    Activity: createMockIcon('activity'),
    Server: createMockIcon('server'),
    Link: createMockIcon('link'),
    Copy: createMockIcon('copy'),
    Check: createMockIcon('check'),
    X: createMockIcon('x'),
    Wrench: createMockIcon('wrench'),
    Info: createMockIcon('info'),
    Table: createMockIcon('table'),
    Radar: createMockIcon('radar'),
    // Additional icons
    ChevronDown: createMockIcon('chevrondown'),
    ChevronRight: createMockIcon('chevronright'),
    ExternalLink: createMockIcon('externallink'),
    Folder: createMockIcon('folder'),
    FileCode: createMockIcon('filecode'),
    Terminal: createMockIcon('terminal'),
    Globe: createMockIcon('globe'),
    Menu: createMockIcon('menu'),
    ArrowLeft: createMockIcon('arrowleft'),
    ArrowRight: createMockIcon('arrowright'),
    Loader2: createMockIcon('loader2'),
    TestTube: createMockIcon('testtube'),
    FlaskConical: createMockIcon('flask'),
    Pencil: createMockIcon('pencil'),
  }
})

// Global clipboard mock
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn().mockResolvedValue(undefined),
    readText: vi.fn().mockResolvedValue(''),
  },
})