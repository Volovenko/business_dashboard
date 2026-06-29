import { defineStore } from 'pinia'
import { ref } from 'vue'
import { summaryApi } from '../api/client.js'

export const useSummaryStore = defineStore('summary', () => {
  const data = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetch() {
    loading.value = true
    error.value = null
    try {
      const res = await summaryApi.get()
      data.value = res.data
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, fetch }
})
