<template>
  <div class="container">
    <h1>Distributed CI/CD Dashboard</h1>
    <PipelineForm @pipeline-started="selectPipeline" />
    <PipelineDetail v-if="selectedPipelineId" :pipeline-id="selectedPipelineId" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import PipelineForm from './components/PipelineForm.vue'
import PipelineDetail from './components/PipelineDetails.vue'

const selectedPipelineId = ref(null)

const selectPipeline = (id) => {
  selectedPipelineId.value = id
}
</script>
