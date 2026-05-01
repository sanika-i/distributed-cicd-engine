import { createRouter, createWebHistory } from 'vue-router'
import PipelineView from '../components/PipelineView.vue'
import WelcomeView  from '../components/WelcomeView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/',                    component: WelcomeView  },
    { path: '/pipelines/:id',       component: PipelineView },
  ]
})
