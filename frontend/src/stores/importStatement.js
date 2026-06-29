import { defineStore } from 'pinia'
import { ref } from 'vue'
import { importApi } from '../api/client.js'

export const useImportStore = defineStore('import', () => {
  const preview = ref([])
  const summary = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const step = ref('idle')

  async function runPreview(file) {
    loading.value = true
    error.value = null
    try {
      const res = await importApi.preview(file)
      preview.value = res.data.payments
      step.value = 'preview'
    } catch (e) {
      error.value = e.response?.data?.detail ?? e.message
    } finally {
      loading.value = false
    }
  }

  async function commit() {
    loading.value = true
    error.value = null
    try {
      const res = await importApi.commit(preview.value)
      summary.value = res.data
      step.value = 'done'
    } catch (e) {
      error.value = e.response?.data?.detail ?? e.message
    } finally {
      loading.value = false
    }
  }

  function reset() {
    preview.value = []
    summary.value = null
    error.value = null
    step.value = 'idle'
  }

  return { preview, summary, loading, error, step, runPreview, commit, reset }
})
