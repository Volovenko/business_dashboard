import { defineStore } from 'pinia'
import { ref } from 'vue'
import { clientsApi } from '../api/client.js'

export const useClientsStore = defineStore('clients', () => {
  const items = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetch() {
    loading.value = true
    error.value = null
    try {
      const res = await clientsApi.list()
      items.value = res.data
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  return { items, loading, error, fetch }
})
