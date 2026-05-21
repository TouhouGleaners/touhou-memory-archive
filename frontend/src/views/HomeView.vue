<template>
  <div class="container">
    <!-- 页面头部 -->
    <AppHeader 
      :videoCount="filteredVideos.length"
      :uploaderList="uploaderList"
      @search="handleSearch"
      @filter="handleStatusFilter" 
      @filter-uploader="handleUploaderFilter"
    />
    
    <!-- 视频表格 -->
    <VideoTable 
      :videos="filteredVideos"
      :searchTerm="currentFilterState.searchTerm"
      :loading="loading"
      :error="error"
      @retry="loadVideoData"
    />
    
    <!-- 页脚 -->
    <AppFooter :dataUpdateTime="dataUpdateTime" />
    
    <!-- 滚动按钮 -->
    <ScrollButtons />
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import AppHeader from '../components/AppHeader.vue'
import VideoTable from '../components/VideoTable.vue'
import AppFooter from '../components/AppFooter.vue'
import ScrollButtons from '../components/ScrollButtons.vue'
import { useFiltering } from '../composables/useFiltering.js'

import { 
  parseEnvBoolean, 
  computeUploaderList, 
  formatDateTime 
} from '../utils/index.js' 

export default {
  name: 'App',
  components: { AppHeader, VideoTable, AppFooter, ScrollButtons },
  setup() {
    // --- 状态定义 ---
    const allVideos = ref([])
    const uploaderList = ref([])
    const loading = ref(true)
    const error = ref('')
    const dataUpdateTime = ref('')
    
    // 筛选状态
    const currentFilterState = reactive({
      searchTerm: '',
      statusFilter: 'all',
      uploaderFilter: 'all',
    })

    const { filteredVideos } = useFiltering(allVideos, currentFilterState)

    // --- 具体的获取策略 ---

    // 策略 A: 从 API 获取
    const fetchFromApi = async (apiBase) => {
      console.log(`[Dev] 正在从本地后端获取数据: ${apiBase}/videos`)
      const response = await fetch(`${apiBase}/videos`)
      if (!response.ok) throw new Error(`API 请求失败: ${response.status}`)
      
      const data = await response.json()
      // API 模式直接返回当前时间
      return { data, time: new Date() }
    }

    // 策略 B: 从静态文件获取
    const fetchFromStatic = async () => {
      console.log('[Prod] 正在读取静态 videos.json...')
      const response = await fetch('videos.json')
      if (!response.ok) throw new Error(`无法加载静态文件: ${response.status}`)
      
      const data = await response.json()
      // 尝试读取 Last-Modified，读不到则返回 null
      const lastModified = response.headers.get('Last-Modified')
      const time = lastModified ? new Date(lastModified) : null
      return { data, time }
    }

    // --- 主加载函数 ---
    const loadVideoData = async () => {
      try {
        loading.value = true
        error.value = ''
        dataUpdateTime.value = '更新中...'

        // 解析配置
        const useApi = parseEnvBoolean(import.meta.env.VITE_USE_API)
        const apiBase = import.meta.env.VITE_API_BASE_URL || ''

        // 选择并执行策略
        let result
        if (useApi) {
          if (!apiBase) throw new Error('配置错误: 启用 API 模式但缺少 Base URL')
          result = await fetchFromApi(apiBase)
        } else {
          result = await fetchFromStatic()
        }

        // 更新数据状态
        allVideos.value = result.data
        uploaderList.value = computeUploaderList(result.data)

        // 更新时间状态
        dataUpdateTime.value = result.time
          ? formatDateTime(result.time)
          : '未知时间 (本地文件)'

      } catch (err) {
        console.error('加载失败:', err)
        error.value = err.message || '未知错误'
        dataUpdateTime.value = '更新失败'
      } finally {
        loading.value = false
      }
    }

    // 事件处理
    const handleSearch = (term) => currentFilterState.searchTerm = term
    const handleStatusFilter = (status) => currentFilterState.statusFilter = status
    const handleUploaderFilter = (uploader) => currentFilterState.uploaderFilter = uploader

    onMounted(loadVideoData)

    return {
      filteredVideos,
      currentFilterState,
      loading,
      error,
      dataUpdateTime,
      uploaderList,
      handleSearch,
      handleStatusFilter,
      handleUploaderFilter,
      loadVideoData,
    }
  }
}
</script>

<style scoped>
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}
</style>