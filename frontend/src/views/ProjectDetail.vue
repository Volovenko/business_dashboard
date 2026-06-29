<template>
  <div>
    <button class="btn btn-ghost" style="margin-bottom:16px;" @click="$router.back()">← Назад</button>

    <div v-if="loading" class="muted">Загружаю…</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <template v-else-if="project">
      <div style="display:flex; align-items:center; gap:12px; margin-bottom:6px;">
        <h1 class="page-title" style="margin-bottom:0;">{{ project.name }}</h1>
        <ProjectStatusBadge :status="project.status" />
      </div>
      <p class="muted" style="margin-bottom:20px;">
        Клиент:
        <RouterLink :to="`/clients/${project.client_id}`" style="color:#3b82f6;">
          {{ clientName }}
        </RouterLink>
        &nbsp;·&nbsp; Создан: {{ fmtDate(project.created_at) }}
      </p>

      <h2 style="font-size:16px; font-weight:600; margin-bottom:12px;">
        Платежи ({{ payments.length }})
      </h2>

      <div v-if="paymentsLoading" class="muted">Загружаю платежи…</div>
      <div v-else-if="!payments.length" class="empty">Нет платежей по проекту.</div>
      <div v-else class="card" style="padding:0; overflow:hidden;">
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Дата</th>
                <th>Услуга</th>
                <th style="text-align:right;">Сумма</th>
                <th>Назначение</th>
                <th>Акт</th>
                <th>Действие</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in payments" :key="p.id">
                <td class="muted" style="white-space:nowrap;">{{ fmtDate(p.payment_date) }}</td>
                <td class="muted">{{ p.service_type }}</td>
                <td class="amount" style="text-align:right;">{{ fmtAmount(p.amount) }}</td>
                <td style="max-width:220px; word-break:break-word; font-size:12px; color:#475569;">
                  {{ p.payment_purpose }}
                </td>
                <td>
                  <ActBadge v-if="p.act" :status="p.act.status" />
                  <span v-if="p.act?.status === 'attention'" class="attention-reason">
                    {{ daysOverdue(p.payment_date) }} дн. без акта
                  </span>
                  <span v-else-if="!p.act" class="muted">—</span>
                </td>
                <td>
                  <ActActions v-if="p.act" :act="p.act" @updated="onActUpdated(p, $event)" />
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="project-totals">
          <span>Итого: <strong>{{ fmtAmount(totalAmount) }}</strong></span>
          <span>Закрыто: <strong style="color:#166534;">{{ fmtAmount(closedAmount) }}</strong></span>
          <span>Открыто: <strong style="color:#1e40af;">{{ fmtAmount(openAmount) }}</strong></span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { projectsApi, paymentsApi } from '../api/client.js'
import ProjectStatusBadge from '../components/ProjectStatusBadge.vue'
import ActBadge from '../components/ActBadge.vue'
import ActActions from '../components/ActActions.vue'

const route = useRoute()
const project = ref(null)
const payments = ref([])
const clientName = ref('')
const loading = ref(false)
const paymentsLoading = ref(false)
const error = ref(null)

onMounted(async () => {
  loading.value = true
  try {
    const res = await projectsApi.get(route.params.id)
    project.value = res.data
    fetchPayments()
  } catch (e) {
    error.value = e.response?.data?.detail ?? e.message
  } finally {
    loading.value = false
  }
})

async function fetchPayments() {
  paymentsLoading.value = true
  try {
    const res = await paymentsApi.list({ project_id: route.params.id })
    payments.value = res.data
    if (res.data.length) clientName.value = res.data[0].client.name
  } finally {
    paymentsLoading.value = false
  }
}

function onActUpdated(payment, updatedAct) {
  payment.act = updatedAct
  const statuses = payments.value.map(p => p.act?.status).filter(Boolean)
  if (statuses.every(s => s === 'closed')) project.value.status = 'completed'
  else if (statuses.some(s => s === 'attention')) project.value.status = 'attention'
  else project.value.status = 'active'
}

const totalAmount = computed(() =>
  payments.value.reduce((s, p) => s + Number(p.amount), 0)
)
const closedAmount = computed(() =>
  payments.value.filter(p => p.act?.status === 'closed').reduce((s, p) => s + Number(p.amount), 0)
)
const openAmount = computed(() => totalAmount.value - closedAmount.value)

function daysOverdue(paymentDate) {
  const diff = Date.now() - new Date(paymentDate).getTime()
  return Math.floor(diff / 86_400_000)
}

function fmtDate(d) {
  return new Date(d).toLocaleDateString('ru-RU')
}
function fmtAmount(v) {
  return Number(v).toLocaleString('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 })
}
</script>
