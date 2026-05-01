<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <div class="sidebar-logo-icon">⚙</div>
      <span class="sidebar-logo-text">Jenkins Jr.</span>
    </div>

    <div class="sidebar-section-label">Pipeline Runs</div>

    <div class="sidebar-list">
      <div v-if="loading" style="display:flex;justify-content:center;padding:28px;">
        <div class="spinner"></div>
      </div>

      <div v-else-if="pipelines.length === 0" style="padding:20px 10px;text-align:center;">
        <div style="font-size:22px;opacity:0.25;margin-bottom:8px;">📭</div>
        <div style="font-size:11px;color:var(--text-3);line-height:1.6;">No pipeline runs yet.</div>
      </div>

      <RouterLink
        v-for="p in pipelines"
        :key="p.pipeline_id"
        :to="`/pipelines/${p.pipeline_id}`"
        class="sidebar-item"
        :class="{ active: currentId === p.pipeline_id }"
      >
        <div class="sidebar-dot" :class="p.status"></div>
        <div class="sidebar-item-body">
          <div class="sidebar-item-top">
            <span class="sidebar-item-repo">{{ p.repo_name || 'unknown' }}</span>
            <span class="sidebar-item-time">{{ relativeTime(p.created_at) }}</span>
          </div>
          <div class="sidebar-item-branch">⎇ {{ p.branch_name || 'main' }}</div>
          <div class="sidebar-item-commit">{{ p.commit_message || '—' }}</div>
        </div>
      </RouterLink>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { listPipelines } from '../services/api'

const route     = useRoute()
const pipelines = ref([])
const loading   = ref(true)

const currentId = computed(() => route.params.id || null)

const relativeTime = (ts) => {
  if (!ts) return ''
  const diff = Date.now() - new Date(ts).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 1)  return 'just now'
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}

const fetchPipelines = async () => {
  try {
    const { data } = await listPipelines()
    pipelines.value = data
  } catch (e) {
    console.error('sidebar fetch failed', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchPipelines()
  const t = setInterval(fetchPipelines, 5000)
  onUnmounted(() => clearInterval(t))
})
</script>
