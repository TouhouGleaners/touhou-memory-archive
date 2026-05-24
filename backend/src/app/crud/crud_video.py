import sqlite3

from shared.models.video import Video, VideoPart


def get_videos(db: sqlite3.Connection, is_touhou: bool = False) -> list[Video]:
    """获取视频列表"""
    sql = """
    SELECT
        v.aid, v.bvid, v.mid, v.title, v.description,
        v.cover_url, v.duration, v.published_at, v.created_at,
        v.category_id, v.category_name, v.copyright, v.state,
        v.view_count, v.danmaku_count, v.reply_count, v.favorite_count,
        v.coin_count, v.share_count, v.like_count,
        v.tags, v.touhou_status, v.season_id,
        u.name as uploader_name
    FROM videos v
    LEFT JOIN users u ON v.mid = u.mid
    """
    if is_touhou:
        query = f"{sql} WHERE v.touhou_status IN (1, 3) ORDER BY v.published_at DESC"
    else:
        query = f"{sql} ORDER BY v.published_at DESC"

    cursor = db.execute(query)

    video_rows = cursor.fetchall()
    if not video_rows:
        return []

    videos_data = [dict(row) for row in video_rows]

    aids = [v['aid'] for v in videos_data]

    if aids:
        placeholders = ','.join('?' for _ in aids)
        query = f"SELECT * FROM video_parts WHERE aid IN ({placeholders})"
        parts_cursor = db.execute(query, aids)
        all_parts = [dict(row) for row in parts_cursor.fetchall()]

        parts_map: dict[int, list] = {}
        for part in all_parts:
            pid = part['aid']
            if pid not in parts_map:
                parts_map[pid] = []
            parts_map[pid].append(part)

        for video in videos_data:
            video_parts_data = parts_map.get(video['aid'], [])
            video['parts'] = [
                VideoPart(cid=p['cid'], index=p['idx'], title=p['title'], duration=p['duration'])
                for p in video_parts_data
            ]
            tags_str = video.get('tags')
            video['tags'] = [t.strip() for t in tags_str.split(',')] if tags_str else []

    return [Video.model_validate(v) for v in videos_data]