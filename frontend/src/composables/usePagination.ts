import { ref, computed, watch, type Ref } from 'vue';

export function usePagination<T>(data: Ref<T[]>) {
  const currentPage = ref(1)
  const pageSize = ref(50)

  const totalPages = computed(() => {
    if (pageSize.value === Infinity) return 1
    return Math.max(1, Math.ceil(data.value.length / pageSize.value))
  })

  const pagedVideos = computed(() => {
    if (pageSize.value === Infinity) return data.value
    const start = (currentPage.value - 1) * pageSize.value
    return data.value.slice(start, start + pageSize.value)
  })

  const startIndex = computed(() => {
    if (pageSize.value === Infinity || data.value.length === 0) return 0
    return (currentPage.value - 1) * pageSize.value + 1
  })

  const endIndex = computed(() => {
    if (pageSize.value === Infinity) return data.value.length
    const end = currentPage.value * pageSize.value
    return Math.min(end, data.value.length)
  })

  const prevPage = () => {
    if (currentPage.value > 1) currentPage.value--
  }

  const nextPage = () => {
    if (currentPage.value < totalPages.value) currentPage.value++
  }

  const goToPage = (page: number) => {
    if (page >= 1 && page <= totalPages.value) {
      currentPage.value = page
    }
  }

  const pageNumbers = computed(() => {
    if (pageSize.value === Infinity) return []

    const pages: number[] = []
    const total = totalPages.value
    const cur = currentPage.value
    let start = Math.max(2, cur - 2)
    let end = Math.min(total - 1, cur + 2)
    if (cur <= 4) {
      start = 2
      end = Math.min(5, total - 1)
    }
    if (cur >= total - 3) {
      start = Math.max(2, total - 4)
      end = total - 1
    }
    for (let i = start; i <= end; i++) {
      pages.push(i)
    }
    return pages
  })

  const showFirst = computed(() => totalPages.value > 1 && pageSize.value !== Infinity)
  const showLast = computed(() => totalPages.value > 1 && pageSize.value !== Infinity)
  const showLeftEllipsis = computed(() => currentPage.value > 4 && totalPages.value > 6 && pageSize.value !== Infinity)
  const showRightEllipsis = computed(() => currentPage.value < totalPages.value - 3 && totalPages.value > 6 && pageSize.value !== Infinity)

  watch(pageSize, () => {
    currentPage.value = 1
  })

  watch(() => data.value.length, () => {
    if (currentPage.value > totalPages.value) {
      currentPage.value = Math.max(1, totalPages.value)
    }
  })

  return {
    currentPage,
    pageSize,
    totalPages,
    pagedVideos,
    startIndex,
    endIndex,
    prevPage,
    nextPage,
    goToPage,
    pageNumbers,
    showFirst,
    showLast,
    showLeftEllipsis,
    showRightEllipsis
  }
}
