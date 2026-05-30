<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <span class="sidebar-logo">🎵</span>
        <span class="sidebar-title">TMA 管理</span>
      </div>
      <nav class="sidebar-nav">
        <router-link :to="{ name: 'admin-home' }" class="nav-item" exact-active-class="active">
          <i class="pi pi-home" />
          <span>仪表盘</span>
        </router-link>
        <router-link :to="{ name: 'admin-videos' }" class="nav-item" active-class="active">
          <i class="pi pi-video" />
          <span>视频管理</span>
        </router-link>
      </nav>
    </aside>

    <div class="main">
      <header class="topbar">
        <div class="topbar-left" />
        <div class="topbar-right">
          <span v-if="state.user" class="user-label">
            <i class="pi pi-user" />
            {{ state.user.username }}
          </span>
          <Button label="登出" severity="secondary" text size="small" @click="handleLogout" />
        </div>
      </header>

      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import { useAuth } from '../../composables/useAuth'

const router = useRouter()
const { state, logout } = useAuth()

function handleLogout() {
  logout()
  router.push({ name: 'admin-login' })
}
</script>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
}

/* --- Sidebar --- */
.sidebar {
  width: 250px;
  background: var(--surface-card);
  border-right: 1px solid var(--surface-border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--surface-border);
}

.sidebar-logo {
  font-size: 1.5rem;
}

.sidebar-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-color);
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  padding: 0.75rem;
  gap: 0.25rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  color: var(--text-color-secondary);
  text-decoration: none;
  font-size: 0.9rem;
  transition: background 0.15s, color 0.15s;
}

.nav-item:hover {
  background: var(--surface-hover);
  color: var(--text-color);
}

.nav-item.active {
  background: var(--primary-color);
  color: var(--primary-contrast-color);
}

.nav-item.active:hover {
  background: var(--primary-hover-color);
}

.nav-item i {
  font-size: 1.1rem;
}

/* --- Main area --- */
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 2rem;
  background: var(--surface-card);
  border-bottom: 1px solid var(--surface-border);
  flex-shrink: 0;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--text-color-secondary);
}

.content {
  flex: 1;
  padding: 2rem;
  background: var(--surface-ground);
  overflow-y: auto;
}
</style>
