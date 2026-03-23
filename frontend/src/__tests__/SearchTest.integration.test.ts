import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { createI18n } from 'vue-i18n'
import SearchTest from '../views/Test/SearchTest.vue'

// Create mock function before vi.mock
const mockExecuteSearch = vi.fn()

// Mock executeSearch API - using hoisted function
vi.mock('@/api/search', () => ({
  executeSearch: (...args: unknown[]) => mockExecuteSearch(...args),
}))

// Mock lucide-vue-next icons
vi.mock('lucide-vue-next', async () => {
  const actual = await vi.importActual('lucide-vue-next')
  return {
    ...actual,
    Search: {
      name: 'Search',
      template: '<svg class="lucide-search"></svg>',
    },
    ChevronDown: {
      name: 'ChevronDown',
      template: '<svg></svg>',
    },
    ChevronUp: {
      name: 'ChevronUp',
      template: '<svg></svg>',
    },
  }
})

// Mock vue-i18n
const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: {
      searchTest: {
        title: 'Search Test',
        subtitle: 'Test your search configuration',
        query: 'Query',
        queryPlaceholder: 'Enter your search query...',
        search: 'Search',
        advanced: 'Advanced',
        collection: 'Collection',
        topK: 'Top K',
        profile: 'Profile',
        enableRerank: 'Enable Rerank',
        noResults: 'No results yet. Enter a query and search.',
        results: 'Results',
        resultsCount: 'results',
      },
      profile: {
        fast: 'Fast',
        balanced: 'Balanced',
        accurate: 'Accurate',
      },
      common: {
        loading: 'Loading...',
      },
    },
    zh: {
      searchTest: {
        title: '检索测试',
        subtitle: '测试您的检索配置',
        query: '查询',
        queryPlaceholder: '输入您的搜索查询...',
        search: '搜索',
        advanced: '高级选项',
        collection: '集合',
        topK: 'Top K',
        profile: '配置',
        enableRerank: '启用重排',
        noResults: '暂无结果。请输入查询并搜索。',
        results: '结果',
        resultsCount: '条结果',
      },
      profile: {
        fast: '快速',
        balanced: '均衡',
        accurate: '精确',
      },
      common: {
        loading: '加载中...',
      },
    },
  },
})

describe('SearchTest API Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should call search API when search button clicked', async () => {
    const mockResponse = {
      query: 'test query',
      results: [
        {
          id: 'doc-1',
          text: 'Result document 1',
          score: 0.95,
          metadata: { source: 'test.ts' },
          rerank_score: 0.92,
        },
        {
          id: 'doc-2',
          text: 'Result document 2',
          score: 0.88,
          metadata: { source: 'test2.ts' },
          rerank_score: 0.85,
        },
      ],
      total: 2,
      collection: 'default',
      embedding_provider: 'ollama-bge-m3',
      rerank_provider: 'flashrank-tiny',
    }

    mockExecuteSearch.mockResolvedValueOnce(mockResponse)

    const wrapper = mount(SearchTest, {
      global: {
        plugins: [i18n],
      },
    })

    // Enter query
    await wrapper.find('textarea').setValue('test query')

    // Click search button
    await wrapper.find('button:has(.lucide-search)').trigger('click')

    // Wait for async operation
    await nextTick()

    // Verify API was called with correct parameters
    expect(mockExecuteSearch).toHaveBeenCalledWith({
      query: 'test query',
      collection_name: 'default',
      top_k: 10,
      use_rerank: true,
    })
  })

  it('should display search results after successful search', async () => {
    const mockResponse = {
      query: 'authentication',
      results: [
        {
          id: 'auth-1',
          text: 'JWT authentication implementation',
          score: 0.95,
          metadata: { source: 'auth.py' },
          rerank_score: 0.93,
        },
      ],
      total: 1,
      collection: 'default',
      embedding_provider: 'ollama-bge-m3',
      rerank_provider: 'flashrank-tiny',
    }

    mockExecuteSearch.mockResolvedValueOnce(mockResponse)

    const wrapper = mount(SearchTest, {
      global: {
        plugins: [i18n],
      },
    })

    // Enter query and search
    await wrapper.find('textarea').setValue('authentication')
    await wrapper.find('button:has(.lucide-search)').trigger('click')

    // Wait for async operation
    await nextTick()
    await nextTick()

    // Verify results are displayed (placeholder should be replaced)
    const resultsContainer = wrapper.find('.space-y-4')
    expect(resultsContainer.exists()).toBe(true)
  })

  it('should handle search error gracefully', async () => {
    mockExecuteSearch.mockRejectedValueOnce(new Error('Network error'))

    const wrapper = mount(SearchTest, {
      global: {
        plugins: [i18n],
      },
    })

    // Enter query and search
    await wrapper.find('textarea').setValue('test')
    await wrapper.find('button:has(.lucide-search)').trigger('click')

    // Wait for async operation
    await nextTick()
    await nextTick()

    // Should still have button enabled after error
    const button = wrapper.find('button:has(.lucide-search)')
    expect(button.attributes('disabled')).toBeUndefined()
  })

  it('should not search when query is empty', async () => {
    const wrapper = mount(SearchTest, {
      global: {
        plugins: [i18n],
      },
    })

    // Click search without entering query
    await wrapper.find('button:has(.lucide-search)').trigger('click')

    // API should not be called
    expect(mockExecuteSearch).not.toHaveBeenCalled()
  })

  it('should pass advanced options to API', async () => {
    const mockResponse = {
      query: 'test',
      results: [],
      total: 0,
      collection: 'docs',
      embedding_provider: 'ollama-bge-m3',
      rerank_provider: null,
    }

    mockExecuteSearch.mockResolvedValueOnce(mockResponse)

    const wrapper = mount(SearchTest, {
      global: {
        plugins: [i18n],
      },
    })

    // Expand advanced options - find by text content
    const advancedButton = wrapper.findAll('button').find(btn => btn.text().includes('Advanced'))
    await advancedButton?.trigger('click')
    await nextTick()

    // Change collection to docs (first select option)
    const selects = wrapper.findAll('select')
    await selects[0].setValue('docs')

    // Change topK
    const topKInput = wrapper.find('input[type="number"]')
    await topKInput.setValue(20)

    // Search
    await wrapper.find('textarea').setValue('test')
    await wrapper.find('button:has(.lucide-search)').trigger('click')
    await nextTick()

    expect(mockExecuteSearch).toHaveBeenCalledWith({
      query: 'test',
      collection_name: 'docs',
      top_k: 20,
      use_rerank: true,
    })
  })
})