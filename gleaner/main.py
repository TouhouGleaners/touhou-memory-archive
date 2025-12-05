import pandas as pd
import sqlite3
import re
import requests
import time
import yt_dlp
from pathlib import Path
from datetime import datetime


class BiliSalvage:
    def __init__(self, excel_path: Path, main_db_path: Path, download_dir: Path):
        self.excel_path = Path(excel_path)
        self.main_db_path = Path(main_db_path)
        self.download_dir = Path(download_dir)
        self.history_db_path = Path(__file__).parent / "download_history.db"
        self.proxy_url = "http://127.0.0.1:7890" 
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://www.bilibili.com/"
        }
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.whitelist_ids = set()

        # 初始化流程
        self.init_history_db()
        self.load_readonly_data()
        self.load_history_data()

    def init_history_db(self):
        """初始化用于记录下载历史的独立数据库"""
        conn = sqlite3.connect(self.history_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS downloads (
                platform TEXT,
                origin_id TEXT,
                bv_source TEXT,
                saved_filename TEXT,
                download_date TEXT,
                PRIMARY KEY (platform, origin_id)
            )
        ''')
        conn.commit()
        conn.close()

    def load_readonly_data(self):
        """
        扫描主数据库 videos 表，提取简介里的原链接，加入白名单，避免重复下载已有的视频
        """
        if not self.main_db_path.exists():
            print(f"[警告] 主数据库未找到: {self.main_db_path}")
            return

        print(f"正在读取主数据库 (只读模式): {self.main_db_path.name} ...")
        try:
            conn = sqlite3.connect(f"file:{self.main_db_path}?mode=ro", uri=True)
        except sqlite3.OperationalError:
            conn = sqlite3.connect(self.main_db_path)
            
        cursor = conn.cursor()
        
        count = 0
        try:
            cursor.execute("SELECT description FROM videos WHERE description IS NOT NULL AND description != ''")
            while True:
                rows = cursor.fetchmany(1000)
                if not rows:
                    break
                for row in rows:
                    origin_info = self.extract_first_origin_id(row[0])
                    if origin_info:
                        self.whitelist_ids.add(origin_info)
                        count += 1
        except Exception as e:
            print(f"[错误] 读取主数据库失败: {e}")
        finally:
            conn.close()
            
        print(f"  - 从主库提取到原视频记录: {count} 条")

    def load_history_data(self):
        """读取自己的下载记录"""
        conn = sqlite3.connect(self.history_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT platform, origin_id FROM downloads")
        rows = cursor.fetchall()
        for row in rows:
            self.whitelist_ids.add((row[0], row[1]))
        conn.close()
        print(f"  - 当前总白名单 (主库+历史): {len(self.whitelist_ids)} 条")

    def is_bilibili_alive(self, bvid):
        """API 检测 B站视频状态 (修复版)"""
        if pd.isna(bvid) or not bvid:
            return False  # 认为原BV已不存在 执行下载
            
        api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        try:
            resp = requests.get(api_url, headers=self.headers, timeout=5)
            
            if resp.status_code != 200:
                print(f"  [API警告] HTTP {resp.status_code} - 暂停检测")
                return True  # 假装它活着，防止因服务器错误导致误下载
                
            data = resp.json()
            
            if data['code'] == 0:
                return True
                
            return False
            
        except Exception as e:
            print(f"  [网络波动] 检测失败，跳过: {e}")
            return True

    def extract_first_origin_id(self, text):
        """正则提取逻辑"""
        if not text or not isinstance(text, str):
            return None
        
        patterns = [
            ('youtube', r'(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be|m\.youtube\.com)/(?:shorts/|watch\?v=|v/|embed/|watch\?.+?v=)?([a-zA-Z0-9_-]{11})'),
            ('twitter', r'(?:twitter\.com|x\.com)/(?:[a-zA-Z0-9_-]+/status/|i/videos/)(\d+)'),
            ('nico', r'(?:nicovideo\.jp|sp\.nicovideo\.jp|nico\.ms|nico\.jp)/watch/(sm\d+)')
        ]

        matches = []
        for platform, pattern in patterns:
            for m in re.finditer(pattern, text):
                matches.append({'pos': m.start(), 'platform': platform, 'id': m.group(1)})

        if not matches: return None
        return (sorted(matches, key=lambda x: x['pos'])[0]['platform'], 
                sorted(matches, key=lambda x: x['pos'])[0]['id'])

    def download_origin(self, platform, origin_id):
        """yt-dlp 下载"""
        if platform == 'youtube': url = f"https://www.youtube.com/watch?v={origin_id}"
        elif platform == 'twitter': url = f"https://twitter.com/i/status/{origin_id}"
        elif platform == 'nico': url = f"https://www.nicovideo.jp/watch/{origin_id}"
        else: return None

        print(f"  [下载中] {url}")
        
        # 路径处理
        save_path = self.download_dir / f"[{platform}] {origin_id} %(title)s.%(ext)s"

        ydl_opts = {
            'outtmpl': str(save_path),
            'ignoreerrors': True,
            'proxy': self.proxy_url,
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info:
                    return ydl.prepare_filename(info)
        except Exception:
            return None
        return None

    def record_history(self, platform, origin_id, bvid, filepath):
        """写入 download_history.db"""
        self.whitelist_ids.add((platform, origin_id))
        
        conn = sqlite3.connect(self.history_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO downloads (platform, origin_id, bv_source, saved_filename, download_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (platform, origin_id, str(bvid), str(filepath), datetime.now().isoformat()))
        conn.commit()
        conn.close()
        print(f"  [记录] 已写入历史记录 (不影响原库)")

    def run(self):
        print("=== BiliSalvage (只读原库版) ===")
        if not self.excel_path.exists():
            print("Excel 文件不存在")
            return

        df = pd.read_excel(self.excel_path)
        total = len(df)
        
        # 目前硬编码: BV在第2列(1), 简介在第23列(22)
        COL_BV = 1
        COL_DESC = 22

        for index, row in df.iterrows():
            bvid = row.iloc[COL_BV] if COL_BV < len(row) else None
            desc = row.iloc[COL_DESC] if COL_DESC < len(row) else ""
            
            if pd.isna(bvid): continue
            
            print(f"\n[{index+1}/{total}] {bvid}")

            # 1. 提取 ID
            origin_info = self.extract_first_origin_id(str(desc))
            if not origin_info:
                print("  [跳过] 无外链")
                continue
            
            platform, origin_id = origin_info

            # 2. 查重
            if (platform, origin_id) in self.whitelist_ids:
                print(f"  [跳过] 已存在 (在原库或历史记录中)")
                continue

            # 3. 查活
            if self.is_bilibili_alive(bvid):
                print("  [跳过] B站视频存活")
                time.sleep(0.5)
                continue

            # 4. 下载
            print("  [补档] 开始下载...")
            saved_file = self.download_origin(platform, origin_id)
            if saved_file:
                self.record_history(platform, origin_id, bvid, saved_file)
            else:
                print("  [失败] 下载未完成")
            
            time.sleep(2)

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent
    
    excel_file = Path(r"C:\Users\16122\Desktop\鵺.xlsx")
    main_db = Path(r"E:\Code\TouhouGleaners\touhou-memory-archive\bili_videos.db")
    
    download_folder = BASE_DIR / "downloads"

    bot = BiliSalvage(excel_file, main_db, download_folder)
    bot.run()