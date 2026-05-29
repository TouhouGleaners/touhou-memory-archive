import { ref, computed, type Ref } from 'vue';

export interface SortableVideo {
  aid: number
  bvid: string
  title: string
  uploader_name: string
  created: number
  touhou_status: number
  parts: unknown[]
}

export function useSorting(videos: Ref<SortableVideo[]>) {
  const sortField = ref('');
  const sortOrder = ref<'asc' | 'desc' | ''>('');

  const sortedVideos = computed(() => {
    if (!sortField.value || !sortOrder.value) {
      return videos.value;
    }

    return [...videos.value].sort((a, b) => {
      let valueA: string | number, valueB: string | number

      switch (sortField.value) {
        case 'title':
          valueA = (a.title || '').toLowerCase()
          valueB = (b.title || '').toLowerCase()
          break
        case 'uploader_name':
          valueA = (a.uploader_name || '').toLowerCase()
          valueB = (b.uploader_name || '').toLowerCase()
          break
        case 'created':
          valueA = a.created || 0
          valueB = b.created || 0
          break
        case 'touhou_status':
          valueA = a.touhou_status || 0
          valueB = b.touhou_status || 0
          break
        case 'parts_count':
          valueA = (a.parts && a.parts.length) || 0
          valueB = (b.parts && b.parts.length) || 0
          break
        default:
          return 0
      }

      if (typeof valueA === 'string') {
        const result = valueA.localeCompare(valueB as string, 'zh-CN')
        return sortOrder.value === 'asc' ? result : -result
      }

      if (sortOrder.value === 'asc') {
        return (valueA as number) - (valueB as number)
      } else {
        return (valueB as number) - (valueA as number)
      }
    });
  });

  const handleSort = (field: string) => {
    if (sortField.value === field) {
      if (!sortOrder.value) {
        sortOrder.value = 'asc'
      } else if (sortOrder.value === 'asc') {
        sortOrder.value = 'desc'
      } else {
        sortField.value = ''
        sortOrder.value = ''
      }
    } else {
      sortField.value = field
      sortOrder.value = 'asc'
    }
  }

  const getSortClass = (field: string) => {
    if (sortField.value !== field) return ''
    return sortOrder.value === 'asc' ? 'sort-asc' : sortOrder.value === 'desc' ? 'sort-desc' : ''
  }

  return {
    sortField,
    sortOrder,
    sortedVideos,
    handleSort,
    getSortClass
  }
}
