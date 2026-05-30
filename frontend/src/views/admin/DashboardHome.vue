<template>
  <div class="dashboard-home">
    <h3>仪表盘</h3>
    <Message v-if="loadError" severity="error" :closable="false">{{ loadError }}</Message>
    <ProgressSpinner v-else-if="loading" style="width: 50px; height: 50px" />
    <div v-else class="cards">
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
import { ref, onMounted, watch } from 'vue'
import Card from 'primevue/card'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import { useVideos, isTouhou } from '../../composables/useVideos'

const { videos, loading, loadError, loadVideos } = useVideos()
const stats = ref({ total: 0, touhou: 0, uploaders: 0 })

function computeStats() {
  stats.value.total = videos.value.length
  stats.value.touhou = videos.value.filter(v => isTouhou(v.touhou_status)).length
  stats.value.uploaders = new Set(videos.value.map(v => v.uploader_name)).size
}

watch(videos, computeStats, { immediate: true })
onMounted(loadVideos)
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
