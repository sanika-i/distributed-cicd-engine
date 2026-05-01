<template>
  <div>
    <!-- Loading -->
    <div v-if="loading" class="empty-state">
      <div class="spinner" style="width:28px;height:28px;border-width:3px;"></div>
    </div>

    <!-- Not found -->
    <div v-else-if="!pipeline" class="empty-state">
      <div class="empty-icon">⚠️</div>
      <div class="empty-title">Pipeline not found</div>
    </div>

    <!-- Content -->
    <div v-else class="page">

      <!-- Header: repo + branch + status -->
      <div class="page-header">
        <div class="page-repo">{{ meta.repo_name || pipeline_id }}</div>
        <div class="page-branch">
          <span>⎇</span>
          <span>{{ meta.branch_name || '—' }}</span>
        </div>
        <div class="page-commit" v-if="meta.commit_message">
          {{ meta.commit_message }}
        </div>
        <div class="page-meta">
          <span class="badge" :class="`badge-${pipeline.status}`">
            {{ statusIcon(pipeline.status) }} {{ pipeline.status }}
          </span>
          <span style="font-size:11px;color:var(--text-3);font-family:var(--font-mono);">
            {{ meta.created_at ? new Date(meta.created_at).toLocaleString() : '' }}
          </span>
          <span style="font-size:11px;font-family:var(--font-mono);color:var(--text-3);">
            ID: {{ pipeline_id.slice(0, 8) }}…
          </span>
        </div>
      </div>

      <!-- Stage strip -->
      <div class="stages-row" v-if="stages.length">
        <div v-for="(s, i) in stages" :key="s.name" class="stage-wrap">
          <div class="stage-bubble">
            <div class="stage-circle" :class="s.status">
              <span>{{ stageIcon(s.status) }}</span>
            </div>
            <div class="stage-label">{{ s.name }}</div>
          </div>
          <div
            v-if="i < stages.length - 1"
            class="stage-connector"
            :class="{ done: s.status === 'success' }"
          ></div>
        </div>
      </div>

      <!-- No stages yet -->
      <div v-else style="margin-bottom:24px;font-size:12px;color:var(--text-3);font-family:var(--font-mono);">
        Waiting for stages…
      </div>

      <!-- Logs -->
      <div class="log-header">
        <span class="log-title">Logs</span>
        <span style="font-size:11px;color:var(--text-3);">{{ logs.length }} line{{ logs.length !== 1 ? 's' : '' }}</span>
      </div>

      <div class="log-panel" ref="logEl">
        <div v-if="logs.length === 0" style="color:var(--text-3);">No logs yet.</div>
        <div v-for="(log, i) in logs" :key="i" class="log-line">
          <span class="log-time">{{ log.timestamp?.slice(11, 19) }}</span>
          <span class="log-stage-name">{{ log.stage }}</span>
          <span class="log-level" :class="log.level">{{ log.level }}</span>
          <span class="log-msg">{{ log.message }}</span>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { listPipelines, getPipeline } from '../services/api'

const route       = useRoute()
const pipeline    = ref(null)   // { status, stages{}, logs[] }
const meta        = ref({})     // { repo_name, branch_name, commit_message, created_at }
const loading     = ref(true)
const logEl       = ref(null)

const pipeline_id = computed(() => route.params.id)

const stages = computed(() =>
  Object.entries(pipeline.value?.stages || {}).map(([name, status]) => ({ name, status }))
)
const logs = computed(() => pipeline.value?.logs || [])

const statusIcon = (s) => ({ success: '✔', failed: '✖', running: '◉', pending: '○' }[s] || '○')
const stageIcon  = (s) => ({ success: '✔', failed: '✖', running: '◉', pending: '○' }[s] || '○')

const scrollLogs = () => nextTick(() => {
  if (logEl.value) logEl.value.scrollTop = logEl.value.scrollHeight
})

// Load the sidebar list entry for repo_name / branch_name / commit_message
const loadMeta = async () => {
  try {
    const { data } = await listPipelines()
    const found = data.find(p => p.pipeline_id === pipeline_id.value)
    if (found) meta.value = found
  } catch {}
}

const loadPipeline = async () => {
  loading.value = true
  try {
    const { data } = await getPipeline(pipeline_id.value)
    pipeline.value = data
    scrollLogs()
  } catch {
    pipeline.value = null
  } finally {
    loading.value = false
  }
}

// Poll while running
let pollTimer = null
const startPolling = () => {
  if (pollTimer) return
  pollTimer = setInterval(async () => {
    try {
      const { data } = await getPipeline(pipeline_id.value)
      pipeline.value = data
      scrollLogs()
      if (data.status !== 'running') stopPolling()
    } catch { stopPolling() }
  }, 3000)
}
const stopPolling = () => { clearInterval(pollTimer); pollTimer = null }

watch(() => pipeline.value?.status, (s) => {
  if (s === 'running') startPolling()
  else stopPolling()
})

// Re-load when route changes
watch(pipeline_id, async () => {
  stopPolling()
  pipeline.value = null
  await Promise.all([loadMeta(), loadPipeline()])
}, { immediate: true })

onUnmounted(stopPolling)
</script>
