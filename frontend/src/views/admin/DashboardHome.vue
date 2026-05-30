<template>
  <div class="dashboard-home">
    <h3>仪表盘</h3>
    <div class="cards">
      <Card>
        <template #title>
          <div class="card-title"><i class="pi pi-video" /> 视频总数</div>
        </template>
        <template #content>
          <div class="card-value">{{ stats.total }}</div>
        </template>
      </Card>
      <Card>
        <template #title>
          <div class="card-title"><i class="pi pi-star" /> 东方视频</div>
        </template>
        <template #content>
          <div class="card-value">{{ stats.touhou }}</div>
        </template>
      </Card>
      <Card>
        <template #title>
          <div class="card-title"><i class="pi pi-users" /> UP主数量</div>
        </template>
        <template #content>
          <div class="card-value">{{ stats.uploaders }}</div>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Card from 'primevue/card'
import { useVideos, isTouhou } from '../../composables/useVideos'

const { videos, loadVideos } = useVideos()
const stats = ref({ total: 0, touhou: 0, uploaders: 0 })

onMounted(async () => {
  await loadVideos()
  stats.value.total = videos.value.length
  stats.value.touhou = videos.value.filter(v => isTouhou(v.touhou_status)).length
  stats.value.uploaders = new Set(videos.value.map(v => v.uploader_name)).size
})
</script>

<style scoped>
.dashboard-home h3 {
  margin: 0 0 1.5rem;
  color: var(--text-color);
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: var(--text-color-secondary);
}

.card-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-color);
}
</style>
