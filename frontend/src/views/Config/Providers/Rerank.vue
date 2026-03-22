<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Plus, Pencil, Trash2, TestTube, Star, Loader2 } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useRerankStore } from '@/stores/rerank'

const { t } = useI18n()
const rerankStore = useRerankStore()

const loading = computed(() => rerankStore.loading)
const error = computed(() => rerankStore.error)
const providers = computed(() => rerankStore.providers)

const testingProvider = ref<string | null>(null)
const testResult = ref<{ latency_ms: number } | null>(null)

onMounted(() => {
  rerankStore.loadProviders()
})

function getStatusBadge(status: string) {
  return status === 'active' ? 'default' : 'secondary'
}

async function handleTest(name: string) {
  testingProvider.value = name
  testResult.value = null
  try {
    const result = await rerankStore.testProvider(name)
    testResult.value = result
  } finally {
    testingProvider.value = null
  }
}

async function handleSetDefault(name: string) {
  await rerankStore.setDefault(name)
}

async function handleDelete(name: string) {
  if (confirm(t('rerank.delete_confirm'))) {
    await rerankStore.deleteProvider(name)
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">{{ t('rerank.providers') }}</h1>
        <p class="text-muted-foreground">{{ t('rerank.description') }}</p>
      </div>
      <Button>
        <Plus class="mr-2 h-4 w-4" />
        {{ t('rerank.add_provider') }}
      </Button>
    </div>

    <!-- Loading State -->
    <div v-if="loading && providers.length === 0" class="text-center py-8">
      <Loader2 class="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
      <p class="mt-2 text-muted-foreground">{{ t('common.loading') }}</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-8 text-destructive">
      {{ error }}
    </div>

    <!-- Provider List -->
    <Card v-else>
      <CardHeader>
        <CardTitle>{{ t('rerank.providers') }}</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{{ t('common.name') }}</TableHead>
              <TableHead>{{ t('common.type') }}</TableHead>
              <TableHead>{{ t('common.model') }}</TableHead>
              <TableHead>{{ t('common.status') }}</TableHead>
              <TableHead>{{ t('rerank.batch_size') }}</TableHead>
              <TableHead>{{ t('common.action') }}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="provider in providers" :key="provider.name">
              <TableCell class="font-medium">
                <div class="flex items-center gap-2">
                  {{ provider.name }}
                  <Badge v-if="provider.is_default" variant="default">
                    {{ t('common.default') }}
                  </Badge>
                </div>
              </TableCell>
              <TableCell>
                <Badge variant="outline">{{ provider.type.toUpperCase() }}</Badge>
              </TableCell>
              <TableCell>{{ provider.model }}</TableCell>
              <TableCell>
                <Badge :variant="getStatusBadge(provider.status)">
                  {{ provider.status === 'active' ? t('common.active') : t('common.inactive') }}
                </Badge>
              </TableCell>
              <TableCell>{{ provider.config?.batch_size || 32 }}</TableCell>
              <TableCell>
                <div class="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    :disabled="testingProvider === provider.name"
                    @click="handleTest(provider.name)"
                  >
                    <Loader2 v-if="testingProvider === provider.name" class="h-4 w-4 animate-spin" />
                    <TestTube v-else class="h-4 w-4" />
                    {{ t('common.test') }}
                  </Button>
                  <Button variant="ghost" size="sm" :aria-label="t('common.default')" @click="handleSetDefault(provider.name)">
                    <Star class="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm">
                    <Pencil class="h-4 w-4" />
                    {{ t('common.edit') }}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    class="text-destructive"
                    @click="handleDelete(provider.name)"
                  >
                    <Trash2 class="h-4 w-4" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  </div>
</template>