<template>
  <div class="video-manage">
    <h3>视频管理</h3>
    <Toast />
    <Message v-if="loadError" severity="error" :closable="false" style="margin-bottom: 1rem">
      {{ loadError }}
    </Message>
    <DataTable
      v-else
      :value="videos"
      :loading="loading"
      dataKey="bvid"
      paginator
      :rows="20"
      :rowsPerPageOptions="[10, 20, 50, 100]"
      stripedRows
      sortMode="multiple"
      removableSort
      responsiveLayout="scroll"
      emptyMessage="暂无视频数据"
    >
      <Column field="title" header="标题" sortable style="min-width: 300px">
        <template #body="{ data }">
          <a :href="getVideoUrl(data.bvid)" target="_blank" rel="noopener" class="video-link">
            {{ data.title }}
          </a>
        </template>
      </Column>
      <Column field="uploader_name" header="UP主" sortable style="width: 140px" />
      <Column field="touhou_status" header="东方状态" sortable style="width: 120px">
        <template #body="{ data }">
          <Tag :value="statusLabelMap[data.touhou_status] || '未知'" :severity="statusSeverity(data.touhou_status)" />
        </template>
      </Column>
      <Column header="操作" style="width: 160px">
        <template #body="{ data }">
          <Select
            :modelValue="data.touhou_status"
            :options="touhouStatusOptions"
            optionLabel="label"
            optionValue="value"
            :disabled="savingBvid === data.bvid"
            @update:modelValue="(val) => handleStatusChange(data, val)"
            size="small"
            style="width: 100%"
          />
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Select from 'primevue/select'
import Toast from 'primevue/toast'
import Message from 'primevue/message'
import { apiGet, apiPatch } from '../../api/client'
import { touhouStatusOptions } from '../../utils/index'

interface VideoItem {
  bvid: string
  title: string
  uploader_name: string
  touhou_status: number
}

const toast = useToast()

const videos = ref<VideoItem[]>([])
const loading = ref(true)
const loadError = ref('')
const savingBvid = ref<string | null>(null)

const statusLabelMap = Object.fromEntries(touhouStatusOptions.map(o => [o.value, o.label]))
const statusSeverityMap = Object.fromEntries(touhouStatusOptions.map(o => [
  o.value,
  o.touhou === true ? 'success' : o.touhou === false ? 'danger' : 'secondary',
]))

function statusSeverity(s: number) {
  return statusSeverityMap[s] || 'secondary'
}

function getVideoUrl(bvid: string) {
  return `https://www.bilibili.com/video/${bvid}`
}

async function loadVideos() {
  loading.value = true
  loadError.value = ''
  try {
    videos.value = await apiGet<VideoItem[]>('/videos')
  } catch (e) {
    loadError.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function handleStatusChange(video: VideoItem, newVal: number) {
  if (newVal === video.touhou_status) return
  savingBvid.value = video.bvid
  try {
    await apiPatch(`/admin/videos/${video.bvid}/touhou-status`, { touhou_status: newVal })
    video.touhou_status = newVal
    toast.add({ severity: 'success', summary: '修改成功', detail: `${video.bvid} → ${statusLabelMap[newVal] || newVal}`, life: 3000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: '修改失败', detail: e instanceof Error ? e.message : '未知错误', life: 5000 })
  } finally {
    savingBvid.value = null
  }
}

onMounted(loadVideos)
</script>

<style scoped>
.video-manage h3 {
  margin: 0 0 1rem;
  color: var(--text-color);
}

.video-link {
  color: var(--primary-color);
  text-decoration: none;
}

.video-link:hover {
  text-decoration: underline;
}
</style>
