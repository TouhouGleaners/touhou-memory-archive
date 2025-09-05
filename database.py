import sqlite3
import time
from typing import List, Dict, Optional


class VideoDatabase:
    """视频信息数据库操作类"""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建UP主信息表 ups
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ups (
                mid BIGINTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                record_created_at INTEGER DEFAULT (strftime('%s', 'now')),
                record_updated_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)

        # 创建视频信息表 videos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                aid BIGINTEGER UNIQUE NOT NULL,
                bvid TEXT UNIQUE NOT NULL,
                published_at INTEGER,
                play_count INTEGER DEFAULT 0,
                review_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                length TEXT,
                cover_url TEXT,
                description TEXT,
                up_mid BIGINTEGER NOT NULL,
                is_touhou INTEGER DEFAULT 0, -- 0:未标记 1:自动标记 2:人工确认
                is_alive BOOLEAN DEFAULT 1,
                tags TEXT,  -- 存储JSON格式的标签数组
                record_created_at INTEGER DEFAULT (strftime('%s', 'now')),
                record_updated_at INTEGER DEFAULT (strftime('%s', 'now')),
                UNIQUE(aid, bvid),
                FOREIGN KEY (up_mid) REFERENCES ups (mid)
                )
            """)
        
        # 创建视频分P信息表 video_parts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_parts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER,
                cid INTEGER NOT NULL,
                part_number INTEGER,
                part_name TEXT,
                part_duration INTEGER,
                UNIQUE(video_id, part_number),
                FOREIGN KEY (video_id) REFERENCES videos (id) ON DELETE CASCADE
                )    
            """)
                
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_up_mid ON videos(up_mid)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_published_at ON videos(published_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_parts_video_id ON video_parts(video_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_is_touhou ON videos(is_touhou)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_is_alive ON videos(is_alive)')

        conn.commit()
        conn.close()

    def save_up_info(self, mid: str, name: str) -> None:
        """保存或更新UP主信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        current_time = int(time.time())

        cursor.execute("""
            INSERT OR REPLACE INTO ups (mid, name, record_updated_at)
            VALUES (?, ?, ?)
        """, (mid, name, current_time))

        conn.commit()
        conn.close()

    def get_up_info(self, mid: str) -> Optional[Dict]:
        """获取UP主信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT mid, name FROM ups WHERE mid = ?", (mid,))
        result = cursor.fetchone()

        conn.close()
        return {'mid': result[0], 'name': result[1]} if result else None

    def save_videos(self, videos: List[Dict], up_mid: str) -> None:
        """保存视频信息至数据库(使用UPSERT优化)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('PRAGMA foreign_keys = ON')  # 启用外键约束

        current_time = int(time.time())

        # 预查询所有视频的id(用于分P处理)
        video_id_cache = {}
        for video in videos:
            video_id = self._get_video_id_by_aid(cursor, video['aid'])
            if video_id:
                video_id_cache[video['aid']] = video_id

        for video in videos:
            tags = video.get('tags', [])  
        
            # 过滤掉"发现《音乐名》"格式的标签
            filtered_tags = [tag for tag in tags if not (tag.startswith("发现《") and tag.endswith("》"))]
            
            # 检查是否为东方视频(仅针对新视频)(简易版)
            has_touhou_tag = any('东方' in tag for tag in filtered_tags) if filtered_tags else False
            
            # 获取视频id(如果存在)
            existing_video_id = video_id_cache.get(video['aid'])
            
            # 插入新视频
            cursor.execute('''
                INSERT INTO videos (
                    title, aid, bvid, published_at, play_count, review_count,
                    comment_count, length, cover_url, description, up_mid,
                    is_touhou, tags, record_created_at, record_updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (aid) DO UPDATE SET
                    title=excluded.title,
                    play_count=excluded.play_count,
                    review_count=excluded.review_count,
                    comment_count=excluded.comment_count,
                    length=excluded.length,
                    cover_url=excluded.cover_url,
                    description=excluded.description,
                    tags=excluded.tags,
                    record_updated_at=excluded.record_updated_at
            ''', (
                video.get('title', ''),
                video['aid'],
                video['bvid'],
                video.get('created', 0),
                video.get('play', 0),
                video.get('video_review', 0),
                video.get('comment', 0),
                video.get('length', ''),
                video.get('pic', ''),
                video.get('description', ''),
                up_mid,
                1 if has_touhou_tag else 0,  # 对于冲突更新，保留原有值；新视频则根据标签判断
                ','.join(filtered_tags),
                current_time if not existing_video_id else None,  # record_created_at
                current_time  # record_updated_at
            ))

            # 获取视频id（无论插入还是更新）
            if cursor.lastrowid:
                video_id = cursor.lastrowid
            else:
                video_id = self._get_video_id_by_aid(cursor, video['aid'])

            video_id_cache[video['aid']] = video_id  # 更新缓存
            self._update_video_parts(cursor, video_id, video['parts'])
            
        conn.commit()
        conn.close()

    def _get_video_id_by_aid(self, cursor, aid: int) -> Optional[int]:
        """根据AV号获取视频ID"""
        cursor.execute("SELECT id FROM videos WHERE aid = ?", (aid,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def _update_video_parts(self, cursor, video_id: int, parts: List[Dict]) -> None:
        """更新视频的分P信息"""
        # 获取现有分P信息 {cid: id}
        existing_parts = {}
        cursor.execute("SELECT cid, id FROM video_parts WHERE video_id = ?", (video_id,))
        for row in cursor.fetchall():
            existing_parts[row[0]] = row[1]

        # 准备批量操作的数据
        to_insert, to_update, to_delete = [], [], []

        # 处理新分P数据
        for part in parts:
            cid = part.get('cid')
            part_data = (
                video_id,
                cid,
                part.get('page', 1),
                part.get('part', ''),
                part.get('duration', 0)
            )

            if cid in existing_parts:
                # 更新现有分P
                to_update.append((
                    part.get('page', 1),  # 更新分P编号(如果变化)
                    part.get('part', ''),
                    part.get('duration', 0),
                    existing_parts[cid]  # 使用cid对应数据库id
                ))
                del existing_parts[cid]  # 标记为已处理
            else:
                # 插入新增分P
                to_insert.append(part_data)
        
        # 剩余未处理的分P需要删除
        to_delete = list(existing_parts.values())

        # 批量插入新分P
        if to_insert:
            cursor.executemany('''
                INSERT INTO video_parts (video_id, cid, part_number, part_name, part_duration)
                VALUES (?, ?, ?, ?, ?)
            ''', to_insert)

        # 批量更新现有分P
        if to_update:
            cursor.executemany('''
                UPDATE video_parts
                SET part_number = ?, part_name = ?, part_duration = ?
                WHERE id = ?
            ''', to_update)

        # 批量删除多余分P
        if to_delete:
            placeholders = ','.join(['?'] * len(to_delete))
            cursor.execute(f"DELETE FROM video_parts WHERE id IN ({placeholders})", to_delete)
    
    def get_videos_by_up(self, up_mid: str) -> List[Dict]:
        """获取指定UP主的视频信息"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = '''
            SELECT
                v.id, v.title, v.aid, v.bvid, v.published_at, v.play_count,
                v.review_count,v.comment_count, v.length, v.cover_url, v.description, 
                v.up_mid, v.record_created_at, v.record_updated_at,
                GROUP_CONCAT(vp.cid) AS cids,
                COUNT(vp.id) AS parts_count,
                datetime(v.published_at, 'unixepoch', 'localtime') AS published_time,
                datetime(v.record_created_at, 'unixepoch', 'localtime') AS record_created_time,
                datetime(v.record_updated_at, 'unixepoch', 'localtime') AS record_updated_time
            FROM videos AS v
            LEFT JOIN video_parts AS vp ON v.id = vp.video_id
            WHERE v.up_mid = ?
            GROUP BY v.id
            ORDER BY v.published_at DESC
            '''
        
        cursor.execute(query, (up_mid,))

        videos = [dict(row) for row in cursor.fetchall()]
        
        # 处理分P的cid列表
        for video in videos:
            if video['cids']:
                video['cids'] = [int(cid) for cid in video['cids'].split(',')]
            else:
                video['cids'] = []

        conn.close()
        return videos
    
    def get_video_by_bvid(self, bvid: str) -> Dict:
        """根据BVID获取视频信息"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                id, title, aid, bvid, published_at, play_count, review_count, comment_count,
                length, cover_url, description, up_mid, record_created_at, record_updated_at,
                datetime(published_at, 'unixepoch', 'localtime') AS published_time,
                datetime(v.record_created_at, 'unixepoch', 'localtime') AS record_created_time,
                datetime(v.record_updated_at, 'unixepoch', 'localtime') AS record_updated_time
            FROM videos
            WHERE bvid = ?
            ''', (bvid,))
        
        video = cursor.fetchone()
        conn.close()

        return dict(video) if video else None
    
    def get_video_parts(self, video_id: int) -> List[Dict]:
        """获取视频的所有分P信息"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, video_id, cid, part_number, part_name, part_duration
            FROM video_parts
            WHERE video_id = ?
            ORDER BY part_number ASC
            ''', (video_id,))
        
        parts = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return parts
    
    def get_video_count_by_up(self, up_mid: str) -> int:
        """获取指定UP主的视频数量"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM videos WHERE up_mid = ?", (up_mid,))
        count = cursor.fetchone()[0]
        conn.close()

        return count
    
    def delete_video(self, bvid: str) -> None:
        """删除视频信息及其分P信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('PRAGMA foreign_keys = ON')  # 启用外键约束 
        cursor.execute("DELETE FROM videos WHERE bvid = ?", (bvid,))  # 删除视频（级联删除）

        conn.commit()
        conn.close()
