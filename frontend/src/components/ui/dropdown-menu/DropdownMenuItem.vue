<script setup lang="ts">
import { cn } from '@/lib/utils'
import { inject } from 'vue'

interface Props {
  class?: string
  disabled?: boolean
}

const props = defineProps<Props>()
const close = inject<() => void>('dropdown-close')
</script>

<template>
  <div
    :class="cn(
      'relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50 cursor-pointer',
      props.class
    )"
    role="menuitem"
    :aria-disabled="disabled"
    @click="close?.()"
  >
    <slot />
  </div>
</template>