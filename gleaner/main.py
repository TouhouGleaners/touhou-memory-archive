import time
import requests
import pandas as pd
from pathlib import Path

from .config import COL_IDX_BV, COL_IDX_TITLE, COL_IDX_DESC, FFMPEG_PATH
from .database import DatabaseManager
from .utils import check_bilibili_alive, extract_origin_id, sanitize_filename
from .downloader import download_video


class GleanerApp:
    def __init__(self, excel_path: Path, main_db_path: Path, download_dir: Path):
        self.excel_path = Path(excel_path)
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        history_db = Path(__file__).parent / "download_history.db"
        self.db_mgr = DatabaseManager(main_db_path, history_db)
        
        self.whitelist: dict[tuple[str, str], str] = self.db_mgr.build_whitelist()
        self.session = requests.Session()

    def run(self):
        print("=== Touhou Memory Achive: Gleaner Started ===")
        
        if not self.excel_path.exists():
            print(f"错误: Excel文件未找到 {self.excel_path}")
            return
        
        if not FFMPEG_PATH.exists():
            print(f"错误: 找不到 FFmpeg! 请将 ffmpeg.exe 放置于: {FFMPEG_PATH}")
            return

        df = pd.read_excel(self.excel_path)
        total = len(df)
        print(f"任务加载: {total} 条数据\n")

        for index, row in df.iterrows():
            bvid = row.iloc[COL_IDX_BV] if COL_IDX_BV < len(row) else None
            desc = row.iloc[COL_IDX_DESC] if COL_IDX_DESC < len(row) else ""

            raw_title = row.iloc[COL_IDX_TITLE] if COL_IDX_TITLE < len(row) else ""
            clean_title = sanitize_filename(str(raw_title)) if not pd.isna(raw_title) else None
            
            if pd.isna(bvid): continue

            # 提取
            origin_info = extract_origin_id(str(desc))
            if not origin_info:
                # 只有BV号无外链的情况，静默跳过或根据需求打印
                continue
            
            platform, origin_id = origin_info

            # 查重
            if (platform, origin_id) in self.whitelist:
                source = self.whitelist[(platform, origin_id)]
                # 打印格式：[进度] BV号: [-] 跳过原因
                print(f"[{index+1}/{total}] {bvid}: [-] 跳过 ({source})")
                continue

            # 查活
            print(f"[{index+1}/{total}] {bvid}: [?] 检测B站状态...", end="", flush=True)

            if check_bilibili_alive(bvid, self.session):
                print(" -> 存活 (无需补档)")
                time.sleep(0.2)
                continue
            else:
                print(" -> [失效]!")

            # 下载
            print(f"    [+] 触发补档: {platform}/{origin_id}")
            print(f"        标题: {clean_title}")

            saved_file = download_video(platform, origin_id, self.download_dir, custom_title=clean_title)
            
            if saved_file:
                self.db_mgr.record_download(platform, origin_id, bvid, saved_file)
                self.whitelist[(platform, origin_id)] = "本次下载"
            
            time.sleep(2)


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = BASE_DIR.parent
    
    excel_file = Path(r"C:\Users\16122\Desktop\鵺.xlsx")
    main_db = Path(r"E:\Code\TouhouGleaners\touhou-memory-archive\bili_videos.db")
    download_folder = BASE_DIR / "downloads"

    app = GleanerApp(excel_file, main_db, download_folder)
    app.run()