<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { SelectContent as RadixSelectContent, SelectPortal, type SelectContentProps, useForwardProps } from 'radix-vue'

const props = defineProps<SelectContentProps & { class?: HTMLAttributes['class'] }>()

const forwarded = useForwardProps(props)
</script>

<template>
  <SelectPortal>
    <RadixSelectContent
      v-bind="forwarded"
      :class="[
        'relative z-50 max-h-96 min-w-[8rem] overflow-hidden rounded-md border bg-popover text-popover-foreground shadow-md data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2',
        props.class,
      ]"
      position="popper"
      :side-offset="4"
    >
      <slot />
    </RadixSelectContent>
  </SelectPortal>
</template>