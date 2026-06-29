<template>
  <div>
    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:24px;">
      <h1 class="page-title" style="margin-bottom:0;">Сводка</h1>
      <button class="btn btn-primary" @click="showImport = true">Загрузить выписку</button>
    </div>

    <div v-if="store.loading" class="muted">Загружаю…</div>
    <div v-else-if="store.error" class="error">{{ store.error }}</div>
    <template v-else-if="store.data">
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="label">Общая сумма</div>
          <div class="value">{{ fmtAmount(store.data.total_amount) }}</div>
        </div>
        <div class="kpi-card">
          <div class="label">Закрытая сумма</div>
          <div class="value" style="color:#166534;">{{ fmtAmount(store.data.closed_amount) }}</div>
        </div>
        <div class="kpi-card">
          <div class="label">Открытая сумма</div>
          <div class="value" style="color:#1e40af;">{{ fmtAmount(store.data.open_amount) }}</div>
        </div>
        <div class="kpi-card">
          <div class="label">Проектов</div>
          <div class="value">{{ store.data.total_projects }}</div>
        </div>
        <div class="kpi-card">
          <div class="label">Платежей</div>
          <div class="value">{{ store.data.total_payments }}</div>
        </div>
        <div class="kpi-card">
          <div class="label">Актов не отправлено</div>
          <div class="value" :style="store.data.acts_not_sent ? 'color:#991b1b;' : ''">
            {{ store.data.acts_not_sent }}
          </div>
        </div>
        <div class="kpi-card">
          <div class="label">Ждут подписи</div>
          <div class="value" :style="store.data.acts_waiting_signature ? 'color:#1e40af;' : ''">
            {{ store.data.acts_waiting_signature }}
          </div>
        </div>
      </div>
    </template>

    <ImportModal v-if="showImport" @close="showImport = false" @imported="onImported" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useSummaryStore } from '../stores/summary.js'
import ImportModal from '../components/ImportModal.vue'

const store = useSummaryStore()
const showImport = ref(false)

onMounted(() => store.fetch())

function onImported() {
  store.fetch()
}

function fmtAmount(v) {
  return Number(v).toLocaleString('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 })
}
</script>
