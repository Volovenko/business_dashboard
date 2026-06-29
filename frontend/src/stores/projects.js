import { defineStore } from 'pinia'
import { ref } from 'vue'
import { projectsApi } from '../api/client.js'

export const useProjectsStore = defineStore('projects', () => {
  const items = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetch(params = {}) {
    loading.value = true
    error.value = null
    try {
      const res = await projectsApi.list(params)
      items.value = res.data
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  return { items, loading, error, fetch }
})
