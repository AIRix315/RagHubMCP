import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { ConfigModel, ConfigUpdateRequest } from '@/types'
import { getConfig as fetchConfig, updateConfig as saveConfig } from '@/api'

export const useConfigStore = defineStore('config', () => {
  const config = ref<ConfigModel | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function loadConfig() {
    loading.value = true
    error.value = null
    try {
      config.value = await fetchConfig()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load config'
    } finally {
      loading.value = false
    }
  }

  async function saveConfigData(data: ConfigUpdateRequest) {
    loading.value = true
    error.value = null
    try {
      await saveConfig(data)
      // Reload config after save
      await loadConfig()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to save config'
    } finally {
      loading.value = false
    }
  }

  return {
    config,
    loading,
    error,
    loadConfig,
    saveConfigData,
  }
})