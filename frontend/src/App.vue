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
import AppHeader from './components/AppHeader.vue'
import VideoTable from './components/VideoTable.vue'
import AppFooter from './components/AppFooter.vue'
import ScrollButtons from './components/ScrollButtons.vue'
import { useFiltering } from './composables/useFiltering.js'

export default {
  name: 'App',
  components: {
    AppHeader,
    VideoTable,
    AppFooter,
    ScrollButtons
  },
  setup() {
    // 原始数据
    const allVideos = ref([])
    const uploaderList = ref([])
    const loading = ref(true)
    const error = ref('')
    const dataUpdateTime = ref('')
    
    // 筛选状态中心
    const currentFilterState = reactive({
      searchTerm: '',
      statusFilter: 'all',
      uploaderFilter: 'all',
      // 预留
    })

    // 过滤逻辑
    const { filteredVideos } = useFiltering(allVideos, currentFilterState)

    // 处理搜索
    const handleSearch = (searchTerm) => {
      currentFilterState.searchTerm = searchTerm
    }

    // 处理状态筛选
    const handleStatusFilter = (statusFilter) => {
      currentFilterState.statusFilter = statusFilter
    }

    // 处理UP主筛选
    const handleUploaderFilter = (uploaderFilter) => {
      currentFilterState.uploaderFilter = uploaderFilter
    }
    // 预留

    // 加载视频数据 (API / 静态双模式)
    const loadVideoData = async () => {
      try {
        loading.value = true
        error.value = ''

        // 读取环境变量
        const useApi = import.meta.env.VITE_USE_API === 'true'
        const apiBase = import.meta.env.VITE_API_BASE_URL || ''

        let data = []

        if (useApi) {
          // === 模式 A: 开发环境 (API) ===
          console.log(`[Dev] 正在从本地后端获取数据: ${apiBase}/videos`)
          
          const response = await fetch(`${apiBase}/videos`)
          if (!response.ok) {
            throw new Error(`API 请求失败: ${response.status} ${response.statusText}`)
          }
          data = await response.json()
          
          // API 模式下，直接显示当前时间为更新时间
          dataUpdateTime.value = new Date().toLocaleString('zh-CN', {
            year: 'numeric', month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit', hour12: false
          })

        } else {
          // === 模式 B: 生产环境 (静态 JSON) ===
          console.log('[Prod] 正在读取静态 videos.json...')
          
          const response = await fetch('videos.json')
          if (!response.ok) {
            throw new Error(`无法加载静态文件! 状态: ${response.status}`)
          }
          data = await response.json()

          // 静态模式下，尝试读取 Last-Modified 头
          const lastModified = response.headers.get('Last-Modified')
          if (lastModified) {
            const date = new Date(lastModified)
            dataUpdateTime.value = date.toLocaleString('zh-CN', {
              year: 'numeric', month: '2-digit', day: '2-digit',
              hour: '2-digit', minute: '2-digit', hour12: false
            })
          }
        }
        
        allVideos.value = data

        // 计算UP主列表
        const allUploaders = allVideos.value
          .map(v => v.uploader_name)
          .filter(name => name)
        const uniqueUploaders = [...new Set(allUploaders)].sort((a, b) => a.localeCompare(b, 'zh-CN'))
        uploaderList.value = ['所有UP主', ...uniqueUploaders]

      } catch (err) {
        console.error('加载视频失败:', err)
        error.value = err.message
      } finally {
        loading.value = false
      }
    }

    // 组件挂载时加载数据
    onMounted(() => {
      loadVideoData()
    })

    return {
      filteredVideos,
      currentFilterState,
      loading,
      error,
      dataUpdateTime,
      uploaderList,
      handleSearch,
      handleStatusFilter,
      loadVideoData,
      handleUploaderFilter,
      // 预留
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