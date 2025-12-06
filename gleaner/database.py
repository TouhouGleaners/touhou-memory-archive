import sqlite3
from pathlib import Path
from datetime import datetime
from .utils import extract_origin_id


class DatabaseManager:
    def __init__(self, main_db_path: Path, history_db_path: Path):
        self.main_db_path = main_db_path
        self.history_db_path = history_db_path
        self._init_history_table()

    def _init_history_table(self):
        """初始化本地历史库"""
        with sqlite3.connect(self.history_db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS downloads (
                    platform TEXT,
                    origin_id TEXT,
                    bv_source TEXT,
                    saved_filename TEXT,
                    download_date TEXT,
                    PRIMARY KEY (platform, origin_id)
                )
            ''')

    def build_whitelist(self) -> dict[tuple[str, str], str]:
        """
        构建查重字典。
        Returns: {(platform, origin_id): "来源说明"}
        """
        whitelist = {}
        
        # 读取主库 (只读)
        if self.main_db_path.exists():
            print(f"正在索引主数据库: {self.main_db_path.name} ...")

            conn = None
            try:
                # 尝试 URI 只读模式
                conn_str = f"file:{self.main_db_path}?mode=ro"
                try:
                    conn = sqlite3.connect(conn_str, uri=True)
                except sqlite3.OperationalError:
                    conn = sqlite3.connect(self.main_db_path)
            
                cursor = conn.cursor()
                cursor.execute("SELECT description FROM videos WHERE description IS NOT NULL AND description != ''")
                while True:
                    rows = cursor.fetchmany(2000)
                    if not rows:
                        break
                    for row in rows:
                        res = extract_origin_id(row[0])
                        if res: 
                            whitelist[res] = "主数据库(已收录)"
            except Exception as e:
                print(f"[错误] 读取主库失败: {e}")
            finally:
                if conn:
                    conn.close()
        
        # 读取历史库
        with sqlite3.connect(self.history_db_path) as conn:
            cursor = conn.execute("SELECT platform, origin_id FROM downloads")
            for row in cursor.fetchall():
                key = (row[0], row[1])
                whitelist[key] = "本地历史(已补档)"
                
        print(f"索引构建完成，有效记录数: {len(whitelist)}")
        return whitelist

    def record_download(self, platform: str, origin_id: str, bvid: str, filepath: str):
        """记录下载成功"""
        with sqlite3.connect(self.history_db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO downloads (
                    platform, origin_id, bv_source, saved_filename, download_date
                ) VALUES (?, ?, ?, ?, ?)
            ''', (platform, origin_id, str(bvid), str(filepath), datetime.now().isoformat()))