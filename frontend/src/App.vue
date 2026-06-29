<template>
  <div class="layout">
    <aside :class="['sidebar', { open: menuOpen }]">
      <div class="sidebar-header">
        <h1>Dashboard</h1>
        <button class="burger" @click="menuOpen = !menuOpen" aria-label="Меню">☰</button>
      </div>
      <nav @click="menuOpen = false">
        <RouterLink to="/">Сводка</RouterLink>
        <RouterLink to="/payments">Платежи</RouterLink>
        <RouterLink to="/projects">Проекты</RouterLink>
        <RouterLink to="/clients">Клиенты</RouterLink>
      </nav>
    </aside>
    <main class="main">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const menuOpen = ref(false)
</script>
