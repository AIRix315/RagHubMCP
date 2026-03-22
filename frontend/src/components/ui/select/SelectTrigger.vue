<script setup lang="ts">
import { type HTMLAttributes, computed } from 'vue'
import { SelectTrigger as RadixSelectTrigger, SelectIcon } from 'radix-vue'
import { ChevronDown } from 'lucide-vue-next'

const props = defineProps<{
  class?: HTMLAttributes['class']
  disabled?: boolean
}>()
</script>

<template>
  <RadixSelectTrigger
    :class="[
      'flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 [&>span]:line-clamp-1',
      props.class,
    ]"
    :disabled="disabled"
  >
    <slot />
    <SelectIcon as-child>
      <ChevronDown class="h-4 w-4 opacity-50" />
    </SelectIcon>
  </RadixSelectTrigger>
</template>