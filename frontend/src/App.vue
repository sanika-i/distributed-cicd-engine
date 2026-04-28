<template>
  <div class="container">
    <h1>Jenkins Jr.</h1>
    <PipelineForm @pipeline-started="selectPipeline" />
    <PipelineDetail v-if="selectedPipelineId" :pipeline-id="selectedPipelineId" />
    <PipelineVisualizer v-if="pipeline" :stages="pipeline.stages" />
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
