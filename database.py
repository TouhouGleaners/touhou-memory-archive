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
        """保存视频信息至数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 启用外键约束
        cursor.execute('PRAGMA foreign_keys = ON')

        current_time = int(time.time())

        for video in videos:
            # 检查视频是否已经存在
            cursor.execute("SELECT id, is_touhou FROM videos WHERE aid = ?", (video['aid'],))
            existing_video = cursor.fetchone()

            tags = video.get('tags', [])  
        
            # 过滤掉"发现《音乐名》"格式的标签
            filtered_tags = []
            for tag in tags:
                if tag.startswith("发现《") and tag.endswith("》"):
                    continue
                filtered_tags.append(tag)
            
            # 检查是否为东方相关视频
            if existing_video:
                # 视频已存在，保留原有的is_touhou值
                is_touhou = existing_video[1]
            else:
                # 新视频，根据标签自动判断
                # 检查过滤后的标签中是否包含"东方"
                has_touhou_tag = any('东方' in tag for tag in filtered_tags) if filtered_tags else False
                is_touhou = 1 if has_touhou_tag else 0
            
            if existing_video:
                # 更新现有视频信息
                video_id = existing_video[0]
                cursor.execute("""
                    UPDATE videos
                    SET title = ?, play_count = ?, review_count = ?, comment_count = ?,
                        length = ?, cover_url = ?, description = ?, is_touhou = ?,
                        tags = ?, record_updated_at = ?
                    WHERE aid = ?
                """, (
                    video.get('title', ''),
                    video.get('play', 0),
                    video.get('video_review', 0),
                    video.get('comment', 0),
                    video.get('length', ''),
                    video.get('pic', ''),
                    video.get('description', ''),
                    is_touhou,
                    ','.join(tags),
                    current_time,
                    video['aid']
                ))
            else:
                # 插入新视频
                cursor.execute('''
                    INSERT INTO videos
                        (title, aid, bvid, published_at, play_count, review_count, comment_count,
                        length, cover_url, description, up_mid, is_touhou, tags, record_created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
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
                        is_touhou,
                        ','.join(tags),
                        current_time
                    ))
                video_id = cursor.lastrowid

            # 处理分P信息
            if 'parts' in video:
                # 删除旧的分P信息
                cursor.execute("DELETE FROM video_parts WHERE video_id = ?", (video_id,))

                # 插入新的分P信息
                for part in video['parts']:
                    cursor.execute('''
                        INSERT OR REPLACE INTO video_parts
                            (video_id, cid, part_number, part_name, part_duration)
                        VALUES (?, ?, ?, ?, ?)
                        ''',(
                            video_id,
                            part.get('cid', 0),
                            part.get('page', 1),
                            part.get('part', ''),
                            part.get('duration', 0)
                        ))
        conn.commit()
        conn.close()

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

        videos = []
        for row in cursor.fetchall():
            video = dict(row)

            # 处理分P的cid列表
            if video['cids']:
                video['cids'] = [int(cid) for cid in video['cids'].split(',')]
            else:
                video['cids'] = []

            videos.append(video)

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

        # 启用外键约束 
        cursor.execute('PRAGMA foreign_keys = ON')

        # 删除视频 （级联删除）
        cursor.execute("DELETE FROM videos WHERE bvid = ?", (bvid,))

        conn.commit()
        conn.close()
