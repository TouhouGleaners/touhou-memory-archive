import { ref } from 'vue'
import { apiGet } from '../api/client'
import { touhouStatusOptions } from '../utils/index'

export interface VideoItem {
  bvid: string
  title: string
  uploader_name: string
  touhou_status: number
}

const TOUHOU_VALUES = new Set(
  touhouStatusOptions.filter(o => o.touhou === true).map(o => o.value)
)

export function isTouhou(status: number): boolean {
  return TOUHOU_VALUES.has(status)
}

export function useVideos() {
  const videos = ref<VideoItem[]>([])
  const loading = ref(true)
  const loadError = ref('')

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

  return { videos, loading, loadError, loadVideos }
}
