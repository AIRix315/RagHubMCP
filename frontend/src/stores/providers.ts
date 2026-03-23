import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type {
  ProvidersListResponse,
  ProviderInfo,
  ProviderCreateRequest,
  ProviderType,
  RerankTestRequest,
  RerankTestResponse,
  RerankCompareRequest,
  RerankCompareResponse,
} from '@/types'
import {
  listProviders,
  getProvider as fetchProvider,
  createOrUpdateProvider,
  deleteProvider as removeProvider,
  setDefaultProvider as setDefault,
  testRerankProvider,
  compareRerankEngines,
} from '@/api'
import { getErrorMessage } from '@/api/errors'

export const useProvidersStore = defineStore('providers', () => {
  // State
  const providers = ref<ProvidersListResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastUpdated = ref<Date | null>(null)

  // Testing state
  const testLoading = ref(false)
  const testResult = ref<RerankTestResponse | null>(null)
  const testError = ref<string | null>(null)

  // Compare state
  const compareLoading = ref(false)
  const compareResult = ref<RerankCompareResponse | null>(null)
  const compareError = ref<string | null>(null)

  // Computed - provider counts
  const embeddingCount = computed(() => providers.value?.embedding.length ?? 0)
  const rerankCount = computed(() => providers.value?.rerank.length ?? 0)
  const llmCount = computed(() => providers.value?.llm.length ?? 0)
  const vectorstoreCount = computed(() => providers.value?.vectorstore.length ?? 0)
  const totalCount = computed(
    () => embeddingCount.value + rerankCount.value + llmCount.value + vectorstoreCount.value
  )

  // Computed - default providers
  const defaultEmbedding = computed(
    () => providers.value?.embedding.find((p) => p.is_default) ?? null
  )
  const defaultRerank = computed(
    () => providers.value?.rerank.find((p) => p.is_default) ?? null
  )
  const defaultLLM = computed(
    () => providers.value?.llm.find((p) => p.is_default) ?? null
  )
  const defaultVectorstore = computed(
    () => providers.value?.vectorstore.find((p) => p.is_default) ?? null
  )

  // Computed - active providers (status === 'active')
  const activeProviders = computed(() => {
    if (!providers.value) return { embedding: [], rerank: [], llm: [], vectorstore: [] }
    return {
      embedding: providers.value.embedding.filter((p) => p.status === 'active'),
      rerank: providers.value.rerank.filter((p) => p.status === 'active'),
      llm: providers.value.llm.filter((p) => p.status === 'active'),
      vectorstore: providers.value.vectorstore.filter((p) => p.status === 'active'),
    }
  })

  // Actions
  async function loadProviders() {
    loading.value = true
    error.value = null
    try {
      providers.value = await listProviders()
      lastUpdated.value = new Date()
    } catch (e) {
      error.value = getErrorMessage(e)
    } finally {
      loading.value = false
    }
  }

  async function getProviderDetail(type: ProviderType, name: string): Promise<ProviderInfo | null> {
    try {
      return await fetchProvider(type, name)
    } catch (e) {
      error.value = getErrorMessage(e)
      return null
    }
  }

  async function addProvider(
    type: ProviderType,
    name: string,
    config: ProviderCreateRequest
  ): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await createOrUpdateProvider(type, name, config)
      await loadProviders()
      return true
    } catch (e) {
      error.value = getErrorMessage(e)
      return false
    } finally {
      loading.value = false
    }
  }

  async function updateProvider(
    type: ProviderType,
    name: string,
    config: ProviderCreateRequest
  ): Promise<boolean> {
    return addProvider(type, name, config)
  }

  async function deleteProvider(type: ProviderType, name: string): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await removeProvider(type, name)
      await loadProviders()
      return true
    } catch (e) {
      error.value = getErrorMessage(e)
      return false
    } finally {
      loading.value = false
    }
  }

  async function setDefaultProvider(type: ProviderType, name: string): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await setDefault(type, name)
      await loadProviders()
      return true
    } catch (e) {
      error.value = getErrorMessage(e)
      return false
    } finally {
      loading.value = false
    }
  }

  // Rerank testing
  async function testRerank(name: string, request: RerankTestRequest): Promise<boolean> {
    testLoading.value = true
    testError.value = null
    testResult.value = null
    try {
      testResult.value = await testRerankProvider(name, request)
      return true
    } catch (e) {
      testError.value = getErrorMessage(e)
      return false
    } finally {
      testLoading.value = false
    }
  }

  async function compareRerank(request: RerankCompareRequest): Promise<boolean> {
    compareLoading.value = true
    compareError.value = null
    compareResult.value = null
    try {
      compareResult.value = await compareRerankEngines(request)
      return true
    } catch (e) {
      compareError.value = getErrorMessage(e)
      return false
    } finally {
      compareLoading.value = false
    }
  }

  function clearTestResult() {
    testResult.value = null
    testError.value = null
  }

  function clearCompareResult() {
    compareResult.value = null
    compareError.value = null
  }

  return {
    // State
    providers,
    loading,
    error,
    lastUpdated,
    // Test state
    testLoading,
    testResult,
    testError,
    // Compare state
    compareLoading,
    compareResult,
    compareError,
    // Computed counts
    embeddingCount,
    rerankCount,
    llmCount,
    vectorstoreCount,
    totalCount,
    // Computed defaults
    defaultEmbedding,
    defaultRerank,
    defaultLLM,
    defaultVectorstore,
    // Computed active
    activeProviders,
    // Actions
    loadProviders,
    getProviderDetail,
    addProvider,
    updateProvider,
    deleteProvider,
    setDefaultProvider,
    // Rerank testing
    testRerank,
    compareRerank,
    clearTestResult,
    clearCompareResult,
  }
})
