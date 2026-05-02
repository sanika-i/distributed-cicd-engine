<template>
  <div class="detail-wrap" v-if="pipeline">

    <div class="detail-header">
      <div class="header-left">
        <div class="header-title">
          <span class="repo-name">{{ pipeline.repo_name || 'Unknown Repo' }}</span>
          <span class="sep">/</span>
          <span class="branch-name">{{ pipeline.branch_name || 'main' }}</span>
        </div>
        <div class="commit-line">
          <span class="commit-sha">{{ pipeline.commit_sha?.slice(0, 7) || '—' }}</span>
          <span class="commit-message">{{ pipeline.commit_message || 'Manual trigger' }}</span>
        </div>
      </div>
      <div class="header-right">
        <StatusBadge :status="pipeline.status" />
        <span class="created-at">{{ formatDate(pipeline.created_at) }}</span>
      </div>
    </div>

    <div class="stage-track-wrap">
      <div class="stage-track">
        <template v-for="(stage, i) in orderedStages" :key="stage.name">
          <div class="stage-node" :class="stage.status">
            <div class="stage-circle">
              <span v-if="stage.status === 'success'">✔</span>
              <span v-else-if="stage.status === 'failed'">✖</span>
              <span v-else-if="stage.status === 'running'" class="spin">◌</span>
              <span v-else>·</span>
            </div>
            <div class="stage-label">{{ stage.name }}</div>
          </div>
          <div v-if="i < orderedStages.length - 1" class="stage-connector" :class="{ lit: stage.status === 'success' }">
          </div>
        </template>
      </div>
    </div>

    <div class="log-section">
      <div class="log-toolbar">
        <span class="log-title">Execution Logs</span>
        <span class="log-count">{{ logs.length }} lines</span>
      </div>
      <div class="log-terminal" ref="logEl">
        <div v-if="logs.length === 0" class="log-empty">Waiting for logs…</div>
        <div v-for="(log, i) in logs" :key="i" class="log-line" :class="log.level.toLowerCase()">
          <span class="log-ts">{{ formatTime(log.timestamp) }}</span>
          <span class="log-stage">{{ log.stage }}</span>
          <span class="log-level" :class="log.level.toLowerCase()">{{ log.level }}</span>
          <span class="log-msg">{{ log.message }}</span>
        </div>
      </div>
    </div>

  </div>

  <div v-else-if="error" class="detail-loading" style="color: var(--red)">
    Error: {{ error }}
  </div>

  <div v-else class="detail-loading">
    <span>Loading pipeline…</span>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { getPipeline } from '../services/api'
import StatusBadge from './StatusBadge.vue'

const props = defineProps({ pipelineId: String })
console.log("PipelineDetails mounted with ID:", props.pipelineId)

const pipeline = ref(null)
const logs = ref([])
const logEl = ref(null)
const error = ref(null)
let interval = null

const orderedStages = computed(() => {
  if (!pipeline.value?.stages) return []
  return Object.entries(pipeline.value.stages).map(([name, status]) => ({ name, status }))
})

const fetchPipeline = async () => {
  try {
    const res = await getPipeline(props.pipelineId)
    const data = res.data

    const normalized = {
      stages: data.stages || {},
      logs: data.logs || [],
      status: data.status === "success" ? "success" : "running",

      repo_name: "Repo",
      branch_name: "main",
      commit_sha: "",
      commit_message: "",
      created_at: new Date().toISOString()
    }

    pipeline.value = normalized
    logs.value = normalized.logs

    if (normalized.status === "success" || normalized.status === "failed") {
      clearInterval(interval)
    }

  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || 'Failed to load pipeline'
    clearInterval(interval)
  }
}

const scrollToBottom = () => {
  if (logEl.value) logEl.value.scrollTop = logEl.value.scrollHeight
}

watch(logs, () => nextTick(scrollToBottom))

watch(
  () => props.pipelineId,
  (newId) => {
    if (!newId) return

    pipeline.value = null
    logs.value = []
    error.value = null

    if (interval) clearInterval(interval)

    fetchPipeline()

    interval = setInterval(fetchPipeline, 3000)
  },
  { immediate: true }
)

const formatDate = (ts) => {
  if (!ts) return ''
  return new Date(ts).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const formatTime = (ts) => {
  if (!ts) return ''
  return new Date(ts).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

// onMounted(() => {
//   fetchPipeline()
//   interval = setInterval(fetchPipeline, 3000)
// })

onUnmounted(() => clearInterval(interval))
</script>

<style scoped>
.detail-wrap {
  display: flex;
  flex-direction: column;
  min-height: 100%;
}

.detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 22px 28px 18px;
  border-bottom: 1px solid var(--border);
  background: var(--panel);
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 17px;
  font-weight: 600;
}

.repo-name {
  color: var(--text);
}

.sep {
  color: var(--muted);
}

.branch-name {
  color: var(--accent);
  font-family: var(--mono);
  font-size: 15px;
}

.commit-line {
  display: flex;
  align-items: center;
  gap: 10px;
}

.commit-sha {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--muted);
  background: var(--border);
  padding: 2px 7px;
  border-radius: 4px;
}

.commit-message {
  font-size: 13px;
  color: var(--muted);
  font-style: italic;
}

.header-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.created-at {
  font-size: 11px;
  color: var(--muted);
  font-family: var(--mono);
}

/* ── Stage track ── */
.stage-track-wrap {
  padding: 24px 28px;
  border-bottom: 1px solid var(--border);
  overflow-x: auto;
}

.stage-track {
  display: flex;
  align-items: center;
  gap: 0;
  width: max-content;
}

.stage-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.stage-circle {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: 2px solid var(--border);
  display: grid;
  place-items: center;
  font-size: 13px;
  background: var(--bg);
  transition: border-color 0.2s, color 0.2s;
}

.stage-node.success .stage-circle {
  border-color: var(--green);
  color: var(--green);
}

.stage-node.failed .stage-circle {
  border-color: var(--red);
  color: var(--red);
}

.stage-node.running .stage-circle {
  border-color: var(--yellow);
  color: var(--yellow);
}

.stage-node.pending .stage-circle {
  border-color: var(--border);
  color: var(--muted);
}

.spin {
  display: inline-block;
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  to {
    transform: rotate(360deg);
  }
}

.stage-label {
  font-size: 11px;
  font-family: var(--mono);
  color: var(--muted);
  text-transform: lowercase;
}

.stage-connector {
  width: 60px;
  height: 2px;
  background: var(--border);
  margin-bottom: 20px;
  transition: background 0.3s;
}

.stage-connector.lit {
  background: var(--green)66;
}

.log-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin: 0 28px 28px;
}

.log-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-bottom: none;
  border-radius: 8px 8px 0 0;
}

.log-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.07em;
}

.log-count {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--muted);
}

.log-terminal {
  background: #0a0c10;
  border: 1px solid var(--border);
  border-radius: 0 0 8px 8px;
  padding: 12px 14px;
  max-height: calc(100dvh - 380px);
  overflow-y: auto;
  font-family: var(--mono);
  font-size: 12px;
  line-height: 1.8;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}

.log-empty {
  color: var(--muted);
  font-style: italic;
}

.log-line {
  display: flex;
  gap: 10px;
  align-items: baseline;
}

.log-ts {
  color: #3d4252;
  flex-shrink: 0;
  font-size: 10px;
}

.log-stage {
  color: var(--accent);
  min-width: 60px;
  flex-shrink: 0;
  font-size: 11px;
}

.log-level {
  min-width: 48px;
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 600;
}

.log-msg {
  color: #c9d1e0;
  white-space: pre-wrap;
  word-break: break-all;
}

.log-level.info {
  color: var(--blue);
}

.log-level.stdout {
  color: var(--green);
}

.log-level.stderr {
  color: var(--red);
}

.log-level.error {
  color: var(--red);
}

.log-line.stderr .log-msg {
  color: var(--red);
}

.log-line.error .log-msg {
  color: #f87171;
}

.detail-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--muted);
  font-family: var(--mono);
}
</style>
