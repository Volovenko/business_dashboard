<template>
  <div>
    <button class="btn btn-ghost" style="margin-bottom:16px;" @click="$router.back()">← Назад</button>

    <div v-if="loading" class="muted">Загружаю…</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <template v-else-if="client">
      <h1 class="page-title">{{ client.name }}</h1>

      <div class="card" style="margin-bottom:20px;">
        <div class="detail-grid">
          <div class="detail-row">
            <span class="detail-label">ИНН</span>
            <span>{{ client.inn }}</span>
          </div>
          <div class="detail-row" v-if="client.ogrn">
            <span class="detail-label">ОГРН</span>
            <span>{{ client.ogrn }}</span>
          </div>
          <div class="detail-row" v-if="client.bank_account">
            <span class="detail-label">Счёт</span>
            <span>{{ client.bank_account }}</span>
          </div>
          <div class="detail-row" v-if="client.contact_person">
            <span class="detail-label">Контакт</span>
            <span>{{ client.contact_person }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Добавлен</span>
            <span class="muted">{{ fmtDate(client.created_at) }}</span>
          </div>
        </div>
      </div>

      <h2 style="font-size:16px; font-weight:600; margin-bottom:12px;">
        Проекты ({{ client.projects.length }})
      </h2>

      <div v-if="!client.projects.length" class="empty">Нет проектов.</div>
      <div v-else class="card" style="padding:0; overflow:hidden;">
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Проект</th>
                <th>Статус</th>
                <th>Создан</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="p in client.projects"
                :key="p.id"
                class="clickable-row"
                @click="$router.push(`/projects/${p.id}`)"
              >
                <td>{{ p.name }}</td>
                <td><ProjectStatusBadge :status="p.status" /></td>
                <td class="muted">{{ fmtDate(p.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { clientsApi } from '../api/client.js'
import ProjectStatusBadge from '../components/ProjectStatusBadge.vue'

const route = useRoute()
const client = ref(null)
const loading = ref(false)
const error = ref(null)

onMounted(async () => {
  loading.value = true
  try {
    const res = await clientsApi.get(route.params.id)
    client.value = res.data
  } catch (e) {
    error.value = e.response?.data?.detail ?? e.message
  } finally {
    loading.value = false
  }
})

function fmtDate(d) {
  return new Date(d).toLocaleDateString('ru-RU')
}
</script>
