<script setup lang="ts">
/**
 * Profile Presets Page
 *
 * Quick-switch interface for pipeline configuration presets.
 * Three profiles: fast, balanced, accurate
 *
 * Reference: Docs/21-UI-Design-Design-System.md Section 3.4
 */

import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Zap,
  Scale,
  Target,
  Check,
  Loader2,
  ChevronDown,
  ChevronUp,
  Settings,
  Clock,
  TrendingUp,
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

const { t } = useI18n()

// ============================================================================
// Profile State
// ============================================================================

interface ProfileSummary {
  name: string
  description: string
  icon: string
  is_default: boolean
  is_active: boolean
}

interface ProfileDetail {
  name: string
  description: string
  icon: string
  use_cases: string[]
  expected_latency: string
  expected_quality: string
  is_default: boolean
  is_active: boolean
  config: {
    retrieval: { top_k: number; hybrid_enabled: boolean; vector_weight: number }
    rerank: { enabled: boolean; provider: string; top_k: number; score_threshold: number; strategy: string }
    context: { enabled: boolean; max_tokens: number; deduplicate: boolean }
  }
}

const loading = ref(true)
const applying = ref<string | null>(null)
const profiles = ref<ProfileSummary[]>([])
const activeProfile = ref<string>('')
const expandedProfile = ref<string | null>(null)
const profileDetails = ref<Record<string, ProfileDetail>>({})

// ============================================================================
// Computed
// ============================================================================

const profileIcons = computed(() => ({
  fast: Zap,
  balanced: Scale,
  accurate: Target,
}))

const profileColors = computed(() => ({
  fast: 'text-yellow-500',
  balanced: 'text-blue-500',
  accurate: 'text-green-500',
}))

// ============================================================================
// Methods
// ============================================================================

async function loadProfiles() {
  loading.value = true
  try {
    const response = await fetch('/api/profiles')
    if (response.ok) {
      profiles.value = await response.json()
      const active = profiles.value.find((p) => p.is_active)
      if (active) {
        activeProfile.value = active.name
      }
    }
  } catch (e) {
    console.error('Failed to load profiles:', e)
  } finally {
    loading.value = false
  }
}

async function loadProfileDetail(name: string) {
  try {
    const response = await fetch(`/api/profiles/${name}`)
    if (response.ok) {
      profileDetails.value[name] = await response.json()
    }
  } catch (e) {
    console.error(`Failed to load profile ${name}:`, e)
  }
}

async function applyProfile(name: string) {
  applying.value = name
  try {
    const response = await fetch(`/api/profiles/${name}/apply`, {
      method: 'POST',
    })
    if (response.ok) {
      activeProfile.value = name
      // Update local state
      profiles.value = profiles.value.map((p) => ({
        ...p,
        is_active: p.name === name,
      }))
    }
  } catch (e) {
    console.error('Failed to apply profile:', e)
  } finally {
    applying.value = null
  }
}

function toggleExpand(name: string) {
  if (expandedProfile.value === name) {
    expandedProfile.value = null
  } else {
    expandedProfile.value = name
    // Load details if not already loaded
    if (!profileDetails.value[name]) {
      loadProfileDetail(name)
    }
  }
}

function getIcon(name: string) {
  return profileIcons.value[name as keyof typeof profileIcons.value] || Settings
}

function getColor(name: string) {
  return profileColors.value[name as keyof typeof profileColors.value] || 'text-gray-500'
}

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(() => {
  loadProfiles()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold tracking-tight">{{ t('profile.title') }}</h1>
      <p class="text-muted-foreground">{{ t('profile.select_profile') }}</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-12">
      <Loader2 class="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
      <p class="mt-2 text-muted-foreground">{{ t('common.loading') }}</p>
    </div>

    <!-- Profile Cards -->
    <div v-else class="grid gap-4 md:grid-cols-3">
      <Card
        v-for="profile in profiles"
        :key="profile.name"
        :class="[
          'cursor-pointer transition-all hover:shadow-lg',
          profile.is_active ? 'ring-2 ring-primary' : '',
        ]"
      >
        <!-- Header -->
        <CardHeader @click="toggleExpand(profile.name)">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <component
                :is="getIcon(profile.name)"
                :class="['h-8 w-8', getColor(profile.name)]"
              />
              <div>
                <CardTitle class="text-lg">{{ profile.name }}</CardTitle>
                <CardDescription>{{ profile.description }}</CardDescription>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <Badge v-if="profile.is_default" variant="secondary">
                {{ t('common.default') }}
              </Badge>
              <Badge v-if="profile.is_active" variant="default">
                <Check class="h-3 w-3 mr-1" />
                {{ t('profile.active') }}
              </Badge>
            </div>
          </div>
        </CardHeader>

        <CardContent class="space-y-4">
          <!-- Quick Stats -->
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div class="flex items-center gap-2 text-muted-foreground">
              <Clock class="h-4 w-4" />
              <span v-if="profileDetails[profile.name]">
                {{ profileDetails[profile.name].expected_latency }}
              </span>
            </div>
            <div class="flex items-center gap-2 text-muted-foreground">
              <TrendingUp class="h-4 w-4" />
              <span v-if="profileDetails[profile.name]">
                {{ profileDetails[profile.name].expected_quality }}
              </span>
            </div>
          </div>

          <!-- Expand Button -->
          <button
            @click="toggleExpand(profile.name)"
            class="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            {{ expandedProfile === profile.name ? t('profile.hide_details') : t('profile.show_details') }}
            <ChevronDown v-if="expandedProfile !== profile.name" class="h-4 w-4" />
            <ChevronUp v-else class="h-4 w-4" />
          </button>

          <!-- Expanded Details -->
          <div v-if="expandedProfile === profile.name && profileDetails[profile.name]" class="border-t pt-4 space-y-3 text-sm">
            <!-- Use Cases -->
            <div>
              <span class="font-medium">{{ t('profile.use_cases') }}:</span>
              <div class="mt-1 flex flex-wrap gap-1">
                <Badge
                  v-for="useCase in profileDetails[profile.name].use_cases"
                  :key="useCase"
                  variant="outline"
                  class="text-xs"
                >
                  {{ useCase }}
                </Badge>
              </div>
            </div>

            <!-- Config Summary -->
            <div class="space-y-2 text-muted-foreground">
              <div class="flex items-center justify-between">
                <span>{{ t('pipeline.retrieval_stage') }}:</span>
                <span class="font-mono text-foreground">
                  top_k={{ profileDetails[profile.name].config.retrieval.top_k }}
                  <span v-if="profileDetails[profile.name].config.retrieval.hybrid_enabled">
                    | hybrid
                  </span>
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span>{{ t('pipeline.rerank_stage') }}:</span>
                <span class="font-mono text-foreground">
                  {{ profileDetails[profile.name].config.rerank.provider }}
                  | threshold={{ profileDetails[profile.name].config.rerank.score_threshold }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span>{{ t('pipeline.context_stage') }}:</span>
                <span class="font-mono text-foreground">
                  max_tokens={{ profileDetails[profile.name].config.context.max_tokens }}
                </span>
              </div>
            </div>
          </div>

          <!-- Apply Button -->
          <Button
            v-if="!profile.is_active"
            class="w-full"
            :disabled="applying === profile.name"
            @click="applyProfile(profile.name)"
          >
            <Loader2 v-if="applying === profile.name" class="mr-2 h-4 w-4 animate-spin" />
            <Check v-else class="mr-2 h-4 w-4" />
            {{ t('profile.apply') }}
          </Button>
          <Button
            v-else
            class="w-full"
            variant="outline"
            disabled
          >
            <Check class="mr-2 h-4 w-4" />
            {{ t('profile.currently_active') }}
          </Button>
        </CardContent>
      </Card>
    </div>
  </div>
</template>