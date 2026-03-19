<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useCollectionStore } from '@/stores/collection'
import type { CollectionInfo } from '@/types'

const collectionStore = useCollectionStore()
const selectedCollection = ref<CollectionInfo | null>(null)
const showDeleteConfirm = ref(false)
const deleting = ref(false)

onMounted(async () => {
  await collectionStore.loadCollections()
})

function confirmDelete(collection: CollectionInfo) {
  selectedCollection.value = collection
  showDeleteConfirm.value = true
}

async function handleDelete() {
  if (!selectedCollection.value) return

  deleting.value = true
  try {
    await collectionStore.removeCollection(selectedCollection.value.name)
    showDeleteConfirm.value = false
    selectedCollection.value = null
  } finally {
    deleting.value = false
  }
}

function cancelDelete() {
  showDeleteConfirm.value = false
  selectedCollection.value = null
}

function formatDate(timestamp: unknown): string {
  if (!timestamp) return '-'
  return new Date(timestamp as number).toLocaleString()
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">Collection 管理</h1>
        <p class="text-muted-foreground mt-2">查看和管理向量数据库中的 Collections</p>
      </div>
      <button
        @click="collectionStore.loadCollections()"
        :disabled="collectionStore.loading"
        class="rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted disabled:opacity-50"
      >
        {{ collectionStore.loading ? '刷新中...' : '刷新' }}
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="collectionStore.loading && collectionStore.collections.length === 0" class="flex items-center justify-center p-8">
      <span class="text-muted-foreground">加载中...</span>
    </div>

    <!-- Error State -->
    <div v-if="collectionStore.error" class="rounded-lg border border-destructive bg-destructive/10 p-4">
      <p class="text-destructive">{{ collectionStore.error }}</p>
    </div>

    <!-- Collections Table -->
    <div v-if="collectionStore.collections.length > 0" class="rounded-lg border">
      <table class="w-full">
        <thead>
          <tr class="border-b bg-muted/50">
            <th class="px-4 py-3 text-left text-sm font-medium">名称</th>
            <th class="px-4 py-3 text-left text-sm font-medium">文档数</th>
            <th class="px-4 py-3 text-left text-sm font-medium">创建时间</th>
            <th class="px-4 py-3 text-right text-sm font-medium">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="collection in collectionStore.collections"
            :key="collection.name"
            class="border-b last:border-0 hover:bg-muted/50"
          >
            <td class="px-4 py-3 text-sm font-medium">{{ collection.name }}</td>
            <td class="px-4 py-3 text-sm">{{ collection.count }}</td>
            <td class="px-4 py-3 text-sm text-muted-foreground">
              {{ formatDate(collection.metadata.created_at) }}
            </td>
            <td class="px-4 py-3 text-right">
              <button
                @click="confirmDelete(collection)"
                class="rounded-md px-3 py-1 text-sm text-destructive hover:bg-destructive/10"
              >
                删除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty State -->
    <div v-else-if="!collectionStore.loading" class="rounded-lg border bg-card p-8 text-center">
      <p class="text-muted-foreground">暂无 Collection</p>
      <p class="text-sm text-muted-foreground mt-2">使用索引功能创建新的 Collection</p>
    </div>

    <!-- Delete Confirmation Modal -->
    <div
      v-if="showDeleteConfirm"
      class="fixed inset-0 z-50 flex items-center justify-center bg-background/80"
    >
      <div class="rounded-lg border bg-card p-6 shadow-lg">
        <h3 class="text-lg font-semibold">确认删除</h3>
        <p class="mt-2 text-muted-foreground">
          确定要删除 Collection "{{ selectedCollection?.name }}" 吗？此操作不可撤销。
        </p>
        <div class="mt-4 flex justify-end gap-2">
          <button
            @click="cancelDelete"
            class="rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted"
          >
            取消
          </button>
          <button
            @click="handleDelete"
            :disabled="deleting"
            class="rounded-md bg-destructive px-4 py-2 text-sm font-medium text-destructive-foreground hover:bg-destructive/90 disabled:opacity-50"
          >
            {{ deleting ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>