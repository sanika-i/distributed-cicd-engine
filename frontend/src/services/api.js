import axios from 'axios'

const api = axios.create({ baseURL: 'http://localhost:8000' })

export const listPipelines = ()   => api.get('/pipelines')
export const getPipeline   = (id) => api.get(`/pipelines/${id}`)
export const runPipeline   = (data) => api.post('/run_pipeline', data)

export default api
