<template>
  <div class="card" v-if="pipeline">
    <h2>Pipeline {{ pipelineId }}</h2>
    <StatusBadge :status="pipeline.status" />

    <h3>Stages</h3>
    <div v-for="(status, stage) in pipeline.stages" :key="stage" class="stage-row">
      <span>{{ stage }}</span>
      <StatusBadge :status="status" />
    </div>

    <h3>Logs</h3>
    <div class="logs">
      <div v-for="(log, index) in pipeline.logs" :key="index">
        [{{ log.timestamp }}] {{ log.stage }} | {{ log.level }} | {{ log.message }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getPipeline } from '../services/api'
import StatusBadge from './StatusBadge.vue'

const props = defineProps({
  pipelineId: String
})

const pipeline = ref(null)
let interval = null

const fetchPipeline = async () => {
  const { data } = await getPipeline(props.pipelineId)
  pipeline.value = data
}

onMounted(() => {
  fetchPipeline()
  interval = setInterval(fetchPipeline, 3000)
})

onUnmounted(() => clearInterval(interval))
</script>
