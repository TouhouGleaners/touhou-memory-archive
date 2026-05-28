<template>
  <div class="dashboard">
    <header class="dashboard-header">
      <h2>管理后台</h2>
      <div class="user-info">
        <span v-if="state.user">{{ state.user.username }} ({{ state.user.role }})</span>
        <button @click="handleLogout">登出</button>
      </div>
    </header>
    <main class="dashboard-content">
      <p>欢迎使用 Touhou Memory Archive 管理后台。</p>
      <p>后续功能开发中...</p>
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuth } from '../../composables/useAuth.js'

const router = useRouter()
const { state, logout } = useAuth()

function handleLogout() {
  logout()
  router.push('/admin/login')
}
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: #f5f5f5;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.dashboard-header h2 {
  margin: 0;
  color: #333;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 0.875rem;
  color: #555;
}

.user-info button {
  padding: 0.4rem 0.8rem;
  background: none;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.user-info button:hover {
  border-color: #fb7299;
  color: #fb7299;
}

.dashboard-content {
  padding: 2rem;
  color: #666;
}
</style>
