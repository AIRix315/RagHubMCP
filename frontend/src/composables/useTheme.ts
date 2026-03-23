import { useDark } from '@vueuse/core'

/**
 * Theme management composable
 * Uses VueUse's useDark which is Tailwind-compatible by default
 * It adds/removes 'dark' class on the <html> element
 */
export function useTheme() {
  // useDark is Tailwind-compatible by default
  // It toggles 'dark' class on html element and persists to localStorage
  const isDark = useDark({
    selector: 'html',
    attribute: 'class',
    valueDark: 'dark',
    valueLight: 'light',
    storageKey: 'theme',
  })

  // Toggle function - inverts the current value
  function toggleTheme() {
    isDark.value = !isDark.value
  }

  return {
    isDark,
    toggleTheme,
  }
}