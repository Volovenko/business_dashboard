<template>
  <span :class="['badge', cls]">{{ label }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ status: String })

const MAP = {
  closed:            ['badge-closed',   'Закрыт'],
  waiting_signature: ['badge-waiting',  'Ждёт подписи'],
  not_sent:          ['badge-not-sent', 'Не отправлен'],
  attention:         ['badge-attention','Внимание!'],
}

const entry = computed(() => MAP[props.status] ?? ['badge-not-sent', props.status])
const cls   = computed(() => entry.value[0])
const label = computed(() => entry.value[1])
</script>
