<template>
  <div class="comment-cell">
    <template v-if="!editing">
      <span class="comment-text" :class="{ muted: !act.manager_comment }">
        {{ act.manager_comment || '—' }}
      </span>
      <button class="comment-edit-btn" title="Редактировать" @click="startEdit">✏</button>
    </template>
    <template v-else>
      <textarea
        ref="inputRef"
        v-model="draft"
        rows="2"
        class="comment-input"
        @keydown.enter.ctrl="save"
        @keydown.esc="cancel"
      />
      <div class="comment-actions">
        <button class="btn btn-primary" style="padding:3px 10px; font-size:12px;" :disabled="saving" @click="save">
          {{ saving ? '…' : 'Сохранить' }}
        </button>
        <button class="btn btn-ghost" style="padding:3px 8px; font-size:12px;" @click="cancel">✕</button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { actsApi } from '../api/client.js'

const props = defineProps({ act: Object })
const emit = defineEmits(['updated'])

const editing = ref(false)
const draft = ref('')
const saving = ref(false)
const inputRef = ref(null)

function startEdit() {
  draft.value = props.act.manager_comment ?? ''
  editing.value = true
  nextTick(() => inputRef.value?.focus())
}

function cancel() {
  editing.value = false
}

async function save() {
  saving.value = true
  try {
    const res = await actsApi.update(props.act.id, { manager_comment: draft.value || null })
    emit('updated', res.data)
    editing.value = false
  } finally {
    saving.value = false
  }
}
</script>
