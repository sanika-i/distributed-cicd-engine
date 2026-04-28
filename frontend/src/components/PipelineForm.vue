<template>
  <form @submit.prevent="submitPipeline" class="card form">
    <h3>Run New Pipeline</h3>

    <input
      v-model="repo_url"
      placeholder="GitHub Repository URL"
      required
    />

    <input
      v-model="branch"
      placeholder="Branch"
    />

    <button :disabled="loading">
      {{ loading ? "Running..." : "Run Pipeline" }}
    </button>
  </form>
</template>

<script setup>
import { ref } from 'vue'
import { runPipeline } from '../services/api'

const emit = defineEmits(['pipeline-started'])

const repo_url = ref('')
const branch = ref('main')
const loading = ref(false)

const submitPipeline = async () => {
  if (!repo_url.value) return

  loading.value = true

  try {
    const { data } = await runPipeline({
      repo_url: repo_url.value,
      branch: branch.value
    })

    emit('pipeline-started', data.pipeline_id)

    repo_url.value = ''
    branch.value = 'main'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

input {
  background: #0b0f19;
  border: 1px solid var(--border);
  color: var(--text);
  padding: 10px;
  border-radius: 6px;
  outline: none;
}

input:focus {
  border-color: var(--muted);
}

button {
  background: var(--green);
  color: black;
  padding: 10px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
