import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000'
})

export const getPipeline = (id) => api.get(`/pipelines/${id}`)
export const getPipelineLogs = (id) => api.get(`/pipelines/${id}/logs`)
export const runPipeline = (data) => api.post('/run_pipeline', data)

export default api
