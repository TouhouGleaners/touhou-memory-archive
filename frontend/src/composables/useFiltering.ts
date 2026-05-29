import { computed, type Ref } from "vue";

interface FilterableVideo {
  title: string
  uploader_name: string
  touhou_status: number
  tags: string[]
  aid: number
  bvid: string
}

interface Filters {
  searchTerm: string
  statusFilter: string
  uploaderFilter: string
}

export function useFiltering(allVideos: Ref<FilterableVideo[]>, filters: Filters) {
  const filteredVideos = computed(() => {
    const { searchTerm, statusFilter, uploaderFilter } = filters;
    let videos = [...allVideos.value]

    if (statusFilter !== 'all') {
      if (statusFilter === '5') {
        videos = videos.filter(v => v.touhou_status === 1 || v.touhou_status === 3)
      } else {
        const statusNum = parseInt(statusFilter, 10)
        videos = videos.filter(v => v.touhou_status === statusNum)
      }
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase().trim()

      videos = videos.filter(v => {
        const titleMatch = v.title &&
          v.title.toLowerCase().includes(term)

        const uploaderMatch = v.uploader_name &&
          v.uploader_name.toLowerCase().includes(term)

        const tagsMatch = v.tags &&
          v.tags.some(tag => tag.toLowerCase().includes(term))

        const aidMatch = v.aid &&
          v.aid.toString().includes(term)

        const bvidMatch = v.bvid &&
          v.bvid.toLowerCase().includes(term)

        return titleMatch || uploaderMatch || tagsMatch || bvidMatch || aidMatch
      })
    }

    if (uploaderFilter && uploaderFilter !== 'all') {
      videos = videos.filter(v => v.uploader_name === uploaderFilter)
    }

    return videos
  })
  return { filteredVideos }
}
