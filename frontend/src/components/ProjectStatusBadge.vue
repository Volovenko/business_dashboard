<template>
  <span :class="['badge', cls]">{{ label }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ status: String })

const MAP = {
  active:    ['badge-active',    'Активный'],
  completed: ['badge-completed', 'Завершён'],
  on_hold:   ['badge-on-hold',   'На паузе'],
  attention: ['badge-attention', 'Внимание!'],
}

const entry = computed(() => MAP[props.status] ?? ['badge-not-sent', props.status])
const cls   = computed(() => entry.value[0])
const label = computed(() => entry.value[1])
</script>
