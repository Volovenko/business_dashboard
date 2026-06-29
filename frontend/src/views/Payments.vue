<template>
  <div>
    <h1 class="page-title">Платежи</h1>

    <div class="card">
      <div class="filters">
        <label>
          Поиск
          <input v-model="filters.search" placeholder="клиент или назначение" @input="debouncedFetch" />
        </label>
        <label>
          Юрлицо
          <select v-model="filters.client_id" @change="onClientChange">
            <option value="">Все</option>
            <option v-for="c in clients" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </label>
        <label>
          Проект
          <select v-model="filters.project_id" @change="load">
            <option value="">Все</option>
            <option v-for="p in filteredProjects" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </label>
        <label>
          Статус акта
          <select v-model="filters.act_status" @change="load">
            <option value="">Все</option>
            <option value="not_sent">Не отправлен</option>
            <option value="waiting_signature">Ждёт подписи</option>
            <option value="closed">Закрыт</option>
            <option value="attention">Внимание!</option>
          </select>
        </label>
        <label>
          Тип / этап
          <input v-model="filters.service_type" placeholder="SEO, разработка…" @input="debouncedFetch" />
        </label>
        <label>
          Дата с
          <input type="date" v-model="filters.date_from" @change="load" />
        </label>
        <label>
          Дата по
          <input type="date" v-model="filters.date_to" @change="load" />
        </label>
        <button class="btn btn-ghost" style="align-self:flex-end;" @click="resetFilters">Сбросить</button>
      </div>
    </div>

    <div v-if="store.loading" class="muted">Загружаю…</div>
    <div v-else-if="store.error" class="error">{{ store.error }}</div>
    <div v-else-if="!store.items.length" class="empty">Нет платежей по заданным фильтрам.</div>
    <div v-else class="card" style="padding:0; overflow:hidden;">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Дата</th>
              <th>Юрлицо</th>
              <th>Проект</th>
              <th>Тип / этап</th>
              <th style="text-align:right;">Сумма</th>
              <th>Назначение платежа</th>
              <th>Отправлен</th>
              <th>Подписан</th>
              <th>Статус</th>
              <th>Комментарий</th>
              <th>Действие</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in store.items" :key="p.id">
              <td class="muted" style="white-space:nowrap;">{{ fmtDate(p.payment_date) }}</td>
              <td>{{ p.client.name }}</td>
              <td class="muted" style="max-width:160px; word-break:break-word;">{{ p.project.name }}</td>
              <td class="muted">{{ p.service_type }}</td>
              <td class="amount" style="text-align:right;">{{ fmtAmount(p.amount) }}</td>
              <td style="max-width:200px; word-break:break-word; font-size:12px; color:#475569;">
                {{ p.payment_purpose }}
              </td>
              <td style="text-align:center;">
                <span v-if="p.act?.is_sent" class="bool-yes" title="Отправлен">✓</span>
                <span v-else class="bool-no" title="Не отправлен">—</span>
              </td>
              <td style="text-align:center;">
                <span v-if="p.act?.is_signed" class="bool-yes" title="Подписан">✓</span>
                <span v-else class="bool-no" title="Не подписан">—</span>
              </td>
              <td>
                <ActBadge v-if="p.act" :status="p.act.status" />
                <span v-else class="muted">—</span>
              </td>
              <td style="min-width:140px;">
                <CommentCell v-if="p.act" :act="p.act" @updated="onActUpdated(p, $event)" />
              </td>
              <td>
                <ActActions v-if="p.act" :act="p.act" @updated="onActUpdated(p, $event)" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { usePaymentsStore } from '../stores/payments.js'
import { clientsApi, projectsApi } from '../api/client.js'
import ActBadge from '../components/ActBadge.vue'
import ActActions from '../components/ActActions.vue'
import CommentCell from '../components/CommentCell.vue'

const store = usePaymentsStore()

const clients = ref([])
const projects = ref([])

const filters = reactive({
  search: '',
  client_id: '',
  project_id: '',
  act_status: '',
  service_type: '',
  date_from: '',
  date_to: '',
})

function onClientChange() {
  filters.project_id = ''
  load()
}

const filteredProjects = computed(() =>
  filters.client_id
    ? projects.value.filter(p => p.client_id === filters.client_id)
    : projects.value
)

let debounceTimer = null
function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(load, 350)
}

function load() {
  store.fetch(filters)
}

function resetFilters() {
  Object.assign(filters, {
    search: '', client_id: '', project_id: '',
    act_status: '', service_type: '', date_from: '', date_to: '',
  })
  load()
}

function onActUpdated(payment, updatedAct) {
  payment.act = updatedAct
}

onMounted(async () => {
  const [c, p] = await Promise.all([clientsApi.list(), projectsApi.list()])
  clients.value = c.data
  projects.value = p.data
  load()
})

function fmtDate(d) {
  return new Date(d).toLocaleDateString('ru-RU')
}
function fmtAmount(v) {
  return Number(v).toLocaleString('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 })
}
</script>
