<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="sidebar-header">
        <span class="logo-mark">⬡</span>
        <span class="logo-text">Jenkins Jr.</span>
      </div>

      <div class="sidebar-section-label">Recent Runs</div>

      <div v-if="loadingList" class="sidebar-empty">Loading…</div>
      <div v-else-if="pipelines.length === 0" class="sidebar-empty">No pipelines yet</div>

      <ul v-else class="pipeline-list">
        <li
          v-for="p in pipelines"
          :key="p.pipeline_id"
          class="pipeline-item"
          :class="{ active: selectedId === p.pipeline_id }"
          @click="selectPipeline(p.pipeline_id)"
        >
          <div class="item-top">
            <span class="commit-msg">{{ p.commit_message || p.commit_sha?.slice(0,7) || 'Manual run' }}</span>
            <span class="status-dot" :class="p.status" :title="p.status"></span>
          </div>
          <div class="item-meta">
            <span class="meta-chip repo">{{ p.repo_name || '—' }}</span>
            <span class="meta-chip branch">{{ p.branch_name || '—' }}</span>
          </div>
        </li>
      </ul>
    </aside>

    <main class="main-area">
      <div v-if="!selectedId" class="empty-state">
        <div class="empty-icon">⬡</div>
        <p>Select a pipeline run <br> from the sidebar.</p>
      </div>
      <PipelineDetail v-else :pipeline-id="selectedId" :key="selectedId" />
    </main>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getPipelines } from './services/api'
import PipelineDetail from './components/PipelineDetails.vue'

const pipelines   = ref([])
const selectedId  = ref(null)
const loadingList = ref(true)

let listInterval = null

const fetchList = async () => {
  try {
    const { data } = await getPipelines()
    pipelines.value = data
  } catch { /* silent */ }
  finally { loadingList.value = false }
}

const selectPipeline = (id) => { selectedId.value = id }

onMounted(() => {
  fetchList()
  listInterval = setInterval(fetchList, 4000)
})

onUnmounted(() => clearInterval(listInterval))
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=DM+Sans:wght@400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:       #0d0f14;
  --sidebar:  #111318;
  --panel:    #16181f;
  --border:   #23262f;
  --text:     #e4e6ed;
  --muted:    #6b7280;
  --accent:   #7c6aff;
  --green:    #22c55e;
  --red:      #f43f5e;
  --yellow:   #f59e0b;
  --blue:     #38bdf8;
  --mono:     'JetBrains Mono', monospace;
  --sans:     'DM Sans', sans-serif;
  --sidebar-w: 280px;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--sans);
  font-size: 14px;
  line-height: 1.5;
  height: 100dvh;
  overflow: hidden;
}

.app-shell {
  display: flex;
  height: 100dvh;
  overflow: hidden;
}

.sidebar {
  width: var(--sidebar-w);
  min-width: var(--sidebar-w);
  background: var(--sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 16px 14px;
  border-bottom: 1px solid var(--border);
}

.logo-mark {
  font-size: 20px;
  color: var(--accent);
  line-height: 1;
}

.logo-text {
  font-family: var(--mono);
  font-weight: 600;
  font-size: 15px;
  color: var(--text);
  letter-spacing: -0.3px;
}

.sidebar-section-label {
  padding: 6px 16px 4px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}

.sidebar-empty {
  padding: 12px 16px;
  color: var(--muted);
  font-size: 12px;
}

.pipeline-list {
  flex: 1;
  overflow-y: auto;
  list-style: none;
  padding: 4px 8px 12px;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}

.pipeline-item {
  padding: 10px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.12s;
  margin-bottom: 2px;
}
.pipeline-item:hover   { background: var(--panel); }
.pipeline-item.active  { background: #1e1f2e; border: 1px solid var(--accent)22; }

.item-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 6px;
  margin-bottom: 5px;
}

.commit-msg {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--text);
  line-height: 1.4;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  flex: 1;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 4px;
}
.status-dot.success { background: var(--green); box-shadow: 0 0 6px var(--green)88; }
.status-dot.failed  { background: var(--red); box-shadow: 0 0 6px var(--red)88; }
.status-dot.running { background: var(--yellow); animation: pulse 1.4s ease-in-out infinite; }
.status-dot.pending { background: var(--muted); }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.35; }
}

.item-meta { display: flex; gap: 5px; flex-wrap: wrap; }

.meta-chip {
  font-family: var(--mono);
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid var(--border);
  color: var(--muted);
}
.meta-chip.repo   { color: var(--blue); border-color: var(--blue)44; }
.meta-chip.branch { color: var(--accent); border-color: var(--accent)44; }

.main-area {
  flex: 1;
  overflow-y: auto;
  padding: 0;
  background: var(--bg);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 14px;
  color: var(--muted);
  text-align: center;
  line-height: 1.7;
}

.empty-icon {
  font-size: 48px;
  color: var(--border);
}
</style>
