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
      <h3>视频管理</h3>
      <p v-if="loading" class="status">加载中...</p>
      <p v-else-if="error" class="status error">{{ error }}</p>
      <p v-else-if="!videos.length" class="status">暂无视频数据</p>
      <table v-else class="video-table">
        <thead>
          <tr>
            <th class="col-title">标题</th>
            <th class="col-uploader">UP主</th>
            <th class="col-status">东方状态</th>
            <th class="col-action">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="v in videos" :key="v.bvid">
            <td class="col-title">
              <a :href="getVideoUrl(v.bvid)" target="_blank" rel="noopener">{{ v.title }}</a>
            </td>
            <td class="col-uploader">{{ v.uploader_name }}</td>
            <td class="col-status">
              <span :class="['status-tag', statusClass(v.touhou_status)]">
                {{ statusLabelMap[v.touhou_status] }}
              </span>
            </td>
            <td class="col-action">
              <select
                :value="v.touhou_status"
                :disabled="savingBvid === v.bvid"
                @change="handleStatusChange(v, $event.target.value)"
              >
                <option v-for="opt in touhouStatusOptions" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
            </td>
          </tr>
        </tbody>
      </table>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../../composables/useAuth.js'
import { apiGet, apiPatch } from '../../api/client.js'
import { touhouStatusOptions } from '../../utils/index.js'

const router = useRouter()
const { state, isLoggedIn, logout } = useAuth()

const videos = ref([])
const loading = ref(true)
const error = ref('')
const savingBvid = ref(null)

const statusLabelMap = Object.fromEntries(touhouStatusOptions.map(o => [o.value, o.label]))
const statusClassMap = Object.fromEntries(touhouStatusOptions.map(o => [o.value, o.cssClass]))

function statusClass(s) {
  return statusClassMap[s] || 'status-unknown'
}

function getVideoUrl(bvid) {
  return `https://www.bilibili.com/video/${bvid}`
}

async function loadVideos() {
  loading.value = true
  error.value = ''
  try {
    videos.value = await apiGet('/videos')
  } catch (e) {
    error.value = e?.message || String(e) || '加载失败'
  } finally {
    loading.value = false
  }
}

async function handleStatusChange(video, newStatus) {
  const val = parseInt(newStatus, 10)
  if (isNaN(val)) return
  savingBvid.value = video.bvid
  try {
    await apiPatch(`/admin/videos/${video.bvid}/touhou-status`, { touhou_status: val })
    video.touhou_status = val
  } catch (e) {
    alert(`修改失败: ${e.message || '未知错误'}`)
  } finally {
    savingBvid.value = null
  }
}

function handleLogout() {
  logout()
  router.push({ name: 'admin-login' })
}

watch(isLoggedIn, (val) => {
  if (!val) router.push({ name: 'admin-login' })
})

onMounted(loadVideos)
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
}

.dashboard-content h3 {
  margin: 0 0 1rem;
  color: #333;
}

.status {
  color: #666;
  text-align: center;
  padding: 2rem;
}

.status.error {
  color: #e74c3c;
}

.video-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.video-table th,
.video-table td {
  padding: 0.6rem 1rem;
  text-align: left;
  border-bottom: 1px solid #eee;
  font-size: 0.875rem;
}

.video-table th {
  background: #fafafa;
  color: #555;
  font-weight: 600;
}

.video-table a {
  color: #fb7299;
  text-decoration: none;
}

.video-table a:hover {
  text-decoration: underline;
}

.col-title {
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.col-uploader {
  width: 120px;
}

.col-status {
  width: 100px;
}

.col-action {
  width: 140px;
}

.col-action select {
  padding: 0.3rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.8rem;
  cursor: pointer;
}

.status-tag {
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

.status-touhou {
  background: #e8f5e9;
  color: #2e7d32;
}

.status-non-touhou {
  background: #fce4ec;
  color: #c62828;
}

.status-unknown {
  background: #f5f5f5;
  color: #999;
}
</style>
