import { ref, computed, watch } from 'vue'
import { useMediaQuery, useStorage } from '@vueuse/core'

export interface SidebarState {
  isCollapsed: boolean
  isMobileOpen: boolean
}

const SIDEBAR_COLLAPSED_KEY = 'sidebar-collapsed'
const SIDEBAR_WIDTH_EXPANDED = 256
const SIDEBAR_WIDTH_COLLAPSED = 72

export function useSidebar() {
  // Persist collapsed state
  const isCollapsed = useStorage(SIDEBAR_COLLAPSED_KEY, false)
  
  // Mobile state (not persisted)
  const isMobileOpen = ref(false)
  
  // Detect mobile viewport
  const isMobile = useMediaQuery('(max-width: 768px)')
  
  // Detect system preference for reduced motion
  const prefersReducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)')
  
  // Computed sidebar width
  const sidebarWidth = computed(() => {
    if (isMobile.value) return SIDEBAR_WIDTH_EXPANDED
    return isCollapsed.value ? SIDEBAR_WIDTH_COLLAPSED : SIDEBAR_WIDTH_EXPANDED
  })
  
  // Toggle collapsed state
  function toggleCollapsed() {
    isCollapsed.value = !isCollapsed.value
  }
  
  // Expand sidebar
  function expand() {
    isCollapsed.value = false
  }
  
  // Collapse sidebar
  function collapse() {
    isCollapsed.value = true
  }
  
  // Toggle mobile drawer
  function toggleMobile() {
    isMobileOpen.value = !isMobileOpen.value
  }
  
  // Open mobile drawer
  function openMobile() {
    isMobileOpen.value = true
  }
  
  // Close mobile drawer
  function closeMobile() {
    isMobileOpen.value = false
  }
  
  // Close mobile drawer on route change or screen resize
  watch(isMobile, (mobile) => {
    if (!mobile) {
      isMobileOpen.value = false
    }
  })
  
  return {
    // State
    isCollapsed,
    isMobileOpen,
    isMobile,
    prefersReducedMotion,
    
    // Computed
    sidebarWidth,
    
    // Constants
    SIDEBAR_WIDTH_EXPANDED,
    SIDEBAR_WIDTH_COLLAPSED,
    
    // Actions
    toggleCollapsed,
    expand,
    collapse,
    toggleMobile,
    openMobile,
    closeMobile,
  }
}
