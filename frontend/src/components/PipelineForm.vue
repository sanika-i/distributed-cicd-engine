<template>
  <form @submit.prevent="submitPipeline" class="card">
    <input v-model="repo_url" placeholder="GitHub Repository URL" required />
    <input v-model="branch" placeholder="Branch" />
    <button type="submit">Run Pipeline</button>
  </form>
</template>

<script setup>
import { ref } from 'vue'
import { runPipeline } from '../services/api'

const emit = defineEmits(['pipeline-started'])

const repo_url = ref('')
const branch = ref('main')

const submitPipeline = async () => {
  const { data } = await runPipeline({
    repo_url: repo_url.value,
    branch: branch.value
  })

  emit('pipeline-started', data.pipeline_id)
  repo_url.value = ''
  branch.value = 'main'
}
</script>
