<template>
  <div>
    <h1 class="page-title">Клиенты</h1>

    <div v-if="store.loading" class="muted">Загружаю…</div>
    <div v-else-if="store.error" class="error">{{ store.error }}</div>
    <div v-else-if="!store.items.length" class="empty">Нет клиентов. Загрузите выписку на странице «Сводка».</div>
    <div v-else class="card" style="padding:0; overflow:hidden;">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Клиент</th>
              <th>ИНН</th>
              <th style="text-align:center;">Проектов</th>
              <th style="text-align:center;">Платежей</th>
              <th style="text-align:right;">Сумма</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="c in store.items"
              :key="c.id"
              class="clickable-row"
              @click="$router.push(`/clients/${c.id}`)"
            >
              <td>{{ c.name }}</td>
              <td class="muted">{{ c.inn }}</td>
              <td style="text-align:center;">{{ c.project_count }}</td>
              <td style="text-align:center;">{{ c.payment_count }}</td>
              <td class="amount" style="text-align:right;">{{ fmtAmount(c.total_amount) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useClientsStore } from '../stores/clients.js'

const store = useClientsStore()
onMounted(() => store.fetch())

function fmtAmount(v) {
  return Number(v).toLocaleString('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 })
}
</script>
