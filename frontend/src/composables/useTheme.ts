import { useColorMode } from '@vueuse/core'
import { computed } from 'vue'

export function useTheme() {
  const mode = useColorMode({
    emitAuto: true,
    modes: {
      light: 'light',
      dark: 'dark',
      auto: 'auto',
    },
    storageKey: 'theme',
  })

  const isDark = computed(() => mode.value === 'dark')

  function toggleTheme() {
    mode.value = mode.value === 'dark' ? 'light' : 'dark'
  }

  return {
    mode,
    isDark,
    toggleTheme,
  }
}