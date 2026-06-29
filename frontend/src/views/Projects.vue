<template>
  <div>
    <h1 class="page-title">Проекты</h1>

    <div v-if="store.loading" class="muted">Загружаю…</div>
    <div v-else-if="store.error" class="error">{{ store.error }}</div>
    <div v-else-if="!store.items.length" class="empty">Нет проектов.</div>
    <div v-else class="card" style="padding:0; overflow:hidden;">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Проект</th>
              <th>Юрлицо</th>
              <th>Статус</th>
              <th style="text-align:center;">Оплат</th>
              <th style="text-align:center;">Актов закрыто</th>
              <th style="text-align:center;">Актов открыто</th>
              <th style="text-align:right;">Сумма</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="p in store.items"
              :key="p.id"
              class="clickable-row"
              @click="$router.push(`/projects/${p.id}`)"
            >
              <td>{{ p.name }}</td>
              <td class="muted">{{ p.client.name }}</td>
              <td><ProjectStatusBadge :status="p.status" /></td>
              <td style="text-align:center;">{{ p.payment_count }}</td>
              <td style="text-align:center;">
                <span style="color:#166534; font-weight:600;">{{ p.acts_closed }}</span>
              </td>
              <td style="text-align:center;">
                <span :style="p.acts_open ? 'color:#991b1b; font-weight:600;' : 'color:#94a3b8;'">
                  {{ p.acts_open }}
                </span>
              </td>
              <td class="amount" style="text-align:right;">{{ fmtAmount(p.total_amount) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useProjectsStore } from '../stores/projects.js'
import ProjectStatusBadge from '../components/ProjectStatusBadge.vue'

const store = useProjectsStore()
onMounted(() => store.fetch())

function fmtAmount(v) {
  return Number(v).toLocaleString('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 })
}
</script>
