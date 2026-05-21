import sqlite3

from shared.models.video import Video, VideoPart


def get_videos(db: sqlite3.Connection, is_touhou: bool = False) -> list[Video]:
    """获取视频列表"""
    sql = """
    SELECT 
        v.aid, v.bvid, v.mid, v.title, v.description, 
        v.pic, v.created, v.tags, v.touhou_status, v.season_id,
        u.name as uploader_name 
    FROM videos v
    LEFT JOIN users u ON v.mid = u.mid
    """
    # 查询视频主表
    if is_touhou:
        # 只查东方视频 (状态 1=自动检测, 3=人工确认)
        query = f"{sql} WHERE v.touhou_status IN (1, 3) ORDER BY v.created DESC"
    else:
        # 查所有视频
        query = f"{sql} ORDER BY v.created DESC"

    cursor = db.execute(query)
    
    video_rows = cursor.fetchall()
    if not video_rows:
        return []

    videos_data = [dict(row) for row in video_rows]
    
    # 收集所有的 aid，一次性查出所有分P
    aids = [v['aid'] for v in videos_data]
    
    if aids:
        placeholders = ','.join('?' for _ in aids)  # 生成 SQL 占位符 (例如: ?,?,?)
        query = f"SELECT * FROM video_parts WHERE aid IN ({placeholders})"
        parts_cursor = db.execute(query, aids)
        all_parts = [dict(row) for row in parts_cursor.fetchall()]

        # 创建分P字典映射: { aid: [part1, part2...] }
        parts_map = {}
        for part in all_parts:
            pid = part['aid']
            if pid not in parts_map:
                parts_map[pid] = []
            parts_map[pid].append(part)

        # 组装最终数据
        for video in videos_data:
            video_parts_data = parts_map.get(video['aid'], [])  # 填入分P数据，如果没找到则为空列表
            video['parts'] = [VideoPart.model_validate(p) for p in video_parts_data]  # 转换为 Pydantic 模型
            tags_str = video.get('tags')
            video['tags'] = [t.strip() for t in tags_str.split(',')] if tags_str else []

    # 转换为 Pydantic Video 模型返回
    return [Video.model_validate(v) for v in videos_data]