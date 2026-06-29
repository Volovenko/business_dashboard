<template>
  <div style="display:flex; gap:6px; flex-wrap:wrap;">
    <button
      v-if="!act.is_sent"
      class="btn btn-primary"
      style="padding:4px 10px; font-size:12px;"
      :disabled="saving"
      @click="markSent"
    >Отправить акт</button>

    <button
      v-if="act.is_sent && !act.is_signed"
      class="btn btn-success"
      style="padding:4px 10px; font-size:12px;"
      :disabled="saving"
      @click="markSigned"
    >Подписан</button>

    <template v-if="act.status === 'closed'">
      <span class="muted" style="font-size:12px;">✓ Закрыт</span>
    </template>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { actsApi } from '../api/client.js'

const props = defineProps({ act: Object })
const emit = defineEmits(['updated'])
const saving = ref(false)

async function markSent() {
  saving.value = true
  try {
    const res = await actsApi.update(props.act.id, { is_sent: true })
    emit('updated', res.data)
  } finally {
    saving.value = false
  }
}

async function markSigned() {
  saving.value = true
  try {
    const res = await actsApi.update(props.act.id, { is_sent: true, is_signed: true })
    emit('updated', res.data)
  } finally {
    saving.value = false
  }
}
</script>
