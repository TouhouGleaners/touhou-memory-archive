// 状态描述映射
export const statusMap = {
  0: "未检查",
  1: "自动检测为东方",
  2: "自动检测为非东方",
  3: "人工检测为东方",
  4: "人工检测为非东方",
  5: "自动+人工检测为东方"
};

// 东方状态选项（管理后台用）
// 后端对应定义在 backend/src/app/api/admin.py 的 TouhouStatus IntEnum，修改时需同步
export const touhouStatusOptions = [
  { value: 0, label: "未检测" },
  { value: 1, label: "自动东方" },
  { value: 2, label: "自动非东方" },
  { value: 3, label: "人工东方" },
  { value: 4, label: "人工非东方" },
];

// 格式化日期 (YYYY/MM/DD)
export const formatDate = (timestamp, locale = "zh-CN") => {
  if (!timestamp) return '未知日期'
  const date = new Date(timestamp * 1000)
  return date.toLocaleDateString(locale, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
};

// 格式化时长 (HH:MM:SS)
export const formatTime = (totalSeconds) => {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = Math.floor(totalSeconds % 60); // 确保是整数

  const parts = [];
  if (hours > 0) {
    parts.push(hours.toString().padStart(2, '0'));
  }
  parts.push(minutes.toString().padStart(2, '0'));
  parts.push(seconds.toString().padStart(2, '0'));

  return parts.join(':');
};

// 获取状态文本
export const getStatusText = (status) => {
  return statusMap[status] || '未知状态';
};

// 生成视频URL
export const getVideoUrl = (aid, bvid) => {
  // 优先使用BV号，如果没有则使用AV号
  if (bvid) {
    return `https://www.bilibili.com/video/${bvid}`;
  } else if (aid) {
    return `https://www.bilibili.com/video/av${aid}`;
  }
  return '#'; // 如果都没有，返回占位符
};

/**
 * 健壮的环境变量布尔值解析
 */
export const parseEnvBoolean = (value) => {
  if (typeof value === 'boolean') return value
  if (!value) return false
  
  const normalized = String(value).toLowerCase().trim()
  const truthy = ['true', '1', 'yes', 'on']
  return truthy.includes(normalized)
}

/**
 * 计算去重后的 UP 主列表
 */
export const computeUploaderList = (videos) => {
  if (!Array.isArray(videos)) return []
  
  const names = videos
    .map(v => v.uploader_name)
    .filter(name => name)
  
  return ['所有UP主', ...[...new Set(names)].sort((a, b) => a.localeCompare(b, 'zh-CN'))]
}

/**
 * 格式化详细时间 (YYYY/MM/DD HH:mm)
 * 用于页面底部的“数据更新于...”
 */
export const formatDateTime = (dateObj) => {
  if (!dateObj || isNaN(dateObj.getTime())) return '未知时间'
  
  return dateObj.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hour12: false
  })
}