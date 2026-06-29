<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <h2>Загрузка банковской выписки</h2>

      <template v-if="store.step === 'idle'">
        <input type="file" accept="application/pdf" @change="onFile" style="margin-bottom:14px;" />
        <div v-if="store.error" class="error">{{ store.error }}</div>
        <div style="display:flex; gap:10px; margin-top:10px;">
          <button class="btn btn-primary" :disabled="!file || store.loading" @click="preview">
            {{ store.loading ? 'Разбираю…' : 'Разобрать' }}
          </button>
          <button class="btn btn-ghost" @click="$emit('close')">Отмена</button>
        </div>
      </template>

      <template v-else-if="store.step === 'preview'">
        <p style="margin-bottom:12px; color:#64748b;">
          Найдено <strong>{{ store.preview.length }}</strong> платежей. Проверьте и подтвердите импорт.
        </p>
        <div class="table-wrap" style="max-height:420px; overflow-y:auto; margin-bottom:16px;">
          <table>
            <thead>
              <tr>
                <th>Дата</th>
                <th>Клиент</th>
                <th>Услуга</th>
                <th>Проект</th>
                <th style="text-align:right;">Сумма</th>
                <th>Счёт</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in store.preview" :key="p.doc_number">
                <td class="muted">{{ p.payment_date }}</td>
                <td>{{ p.client_name }}</td>
                <td>{{ p.service_type }}</td>
                <td class="muted" style="max-width:200px; word-break:break-word;">{{ p.project_name }}</td>
                <td class="amount" style="text-align:right;">{{ fmtAmount(p.amount) }}</td>
                <td class="muted">{{ p.invoice_number ?? '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="store.error" class="error">{{ store.error }}</div>
        <div style="display:flex; gap:10px;">
          <button class="btn btn-success" :disabled="store.loading" @click="commit">
            {{ store.loading ? 'Сохраняю…' : 'Сохранить в БД' }}
          </button>
          <button class="btn btn-ghost" @click="store.reset()">Назад</button>
          <button class="btn btn-ghost" @click="$emit('close')">Отмена</button>
        </div>
      </template>

      <template v-else>
        <div style="margin-bottom:16px;">
          <p style="color:#166534; font-weight:600; margin-bottom:10px;">Импорт завершён!</p>
          <ul style="line-height:2; padding-left:18px;">
            <li>Клиентов создано: <strong>{{ store.summary.created_clients }}</strong></li>
            <li>Проектов создано: <strong>{{ store.summary.created_projects }}</strong></li>
            <li>Платежей создано: <strong>{{ store.summary.created_payments }}</strong></li>
            <li>Актов создано: <strong>{{ store.summary.created_acts }}</strong></li>
          </ul>
        </div>
        <button class="btn btn-primary" @click="finish">Готово</button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useImportStore } from '../stores/importStatement.js'

const emit = defineEmits(['close', 'imported'])
const store = useImportStore()
const file = ref(null)

function onFile(e) {
  file.value = e.target.files[0] ?? null
}

async function preview() {
  if (file.value) await store.runPreview(file.value)
}

async function commit() {
  await store.commit()
}

function finish() {
  store.reset()
  emit('imported')
  emit('close')
}

function fmtAmount(v) {
  return Number(v).toLocaleString('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 })
}
</script>
