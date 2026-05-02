import axios from 'axios'

const api = axios.create({
  baseURL: "YOUR_BACKEND_URL"
})

export const getPipelines    = ()     => api.get('/pipelines')
export const getPipeline     = (id)   => api.get(`/pipelines/${id}`)
export const getPipelineLogs = (id)   => api.get(`/pipelines/${id}/logs`)
export const runPipeline     = (data) => api.post('/run_pipeline', data)

export default api
