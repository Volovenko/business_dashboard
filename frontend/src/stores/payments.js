import { defineStore } from 'pinia'
import { ref } from 'vue'
import { paymentsApi } from '../api/client.js'

export const usePaymentsStore = defineStore('payments', () => {
  const items = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetch(filters = {}) {
    loading.value = true
    error.value = null
    const params = Object.fromEntries(
      Object.entries(filters).filter(([, v]) => v !== null && v !== '' && v !== undefined),
    )
    try {
      const res = await paymentsApi.list(params)
      items.value = res.data
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function updateAct(actId, payload) {
    const { actsApi } = await import('../api/client.js')
    const res = await actsApi.update(actId, payload)
    const act = res.data
    const payment = items.value.find((p) => p.act?.id === actId)
    if (payment) payment.act = act
    return act
  }

  return { items, loading, error, fetch, updateAct }
})
