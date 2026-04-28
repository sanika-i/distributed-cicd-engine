<template>
  <div class="card" v-if="pipeline">
    <div class="header">
      <h2>Pipeline <span class="muted">{{ pipelineId }}</span></h2>
      <StatusBadge :status="pipeline.status" />
    </div>

    <div class="pipeline">
      <div
        v-for="(stage, index) in orderedStages"
        :key="stage.name"
        class="stage"
        :class="stage.status"
      >
        <div class="circle">
          <span v-if="stage.status === 'success'">✔</span>
          <span v-else-if="stage.status === 'failed'">✖</span>
          <span v-else>⏳</span>
        </div>

        <div class="label">{{ stage.name }}</div>

        <div v-if="index !== orderedStages.length - 1" class="line" />
      </div>
    </div>

    <h3>Logs</h3>
    <div class="logs">
      <div v-for="log in logs" :key="log.timestamp + log.message" class="log-line">
        [{{ log.timestamp }}] {{ log.stage }} | {{ log.level }} | {{ log.message }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getPipeline } from '../services/api'
import StatusBadge from './StatusBadge.vue'

const props = defineProps({
  pipelineId: String
})

const pipeline = ref(null)
const logs = ref([])

const PIPELINE_ORDER = ["clone", "build", "test", "deploy"]

const normalizeStages = (stages) => {
  return PIPELINE_ORDER.map((name) => {
    return {
      name,
      status: stages?.[name] || "pending"
    }
  })
}

const orderedStages = computed(() => {
  if (!pipeline.value) return []
  return normalizeStages(pipeline.value.stages)
})

let interval = null

const fetchPipeline = async () => {
  const { data } = await getPipeline(props.pipelineId)
  pipeline.value = data
  logs.value = data.logs || []
}

onMounted(() => {
  fetchPipeline()
  interval = setInterval(fetchPipeline, 3000)
})

onUnmounted(() => clearInterval(interval))
</script>

<style scoped>
.card {
  background: var(--panel);
  padding: 20px;
  border-radius: 10px;
}

.header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 18px;
}

.muted {
  color: var(--muted);
}

.pipeline {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 16px 0 24px;
  overflow-x: auto;
}

.stage {
  display: flex;
  align-items: center;
  gap: 8px;
}

.circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: #0b0f19;
  border: 1px solid var(--border);
  font-size: 12px;
}

.stage.success .circle {
  border-color: var(--green);
  color: var(--green);
}

.stage.failed .circle {
  border-color: var(--red);
  color: var(--red);
}

.stage.pending .circle {
  border-color: var(--muted);
  color: var(--muted);
}

.stage.running .circle {
  border-color: var(--yellow);
  color: var(--yellow);
}

.label {
  font-size: 13px;
  color: var(--muted);
}

.line {
  width: 40px;
  height: 2px;
  background: var(--border);
}

.logs {
  margin-top: 10px;
  background: #0b0f19;
  border: 1px solid var(--border);
  padding: 12px;
  border-radius: 8px;
  max-height: 300px;
  overflow-y: auto;
  font-family: monospace;
  font-size: 12px;
}

.log-line {
  padding: 2px 0;
  color: var(--muted);
}
</style>
