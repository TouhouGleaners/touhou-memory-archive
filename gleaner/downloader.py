import yt_dlp
from pathlib import Path
from .config import PROXY_URL, FFMPEG_PATH 


def download_video(platform: str, origin_id: str, output_dir: Path, custom_title: str | None = None) -> str | None:
    """执行下载，返回保存的文件名 (静默模式)"""
    if not FFMPEG_PATH.exists():
        print(f"\n    [配置错误] 找不到 FFmpeg! 请确认文件位置: {FFMPEG_PATH}")
        return None
    
    # 构造 URL
    if platform == 'youtube': url = f"https://www.youtube.com/watch?v={origin_id}"
    elif platform == 'twitter': url = f"https://twitter.com/i/status/{origin_id}"
    elif platform == 'nico': url = f"https://www.nicovideo.jp/watch/{origin_id}"
    else: return None

    print(f"    -> 正在拉取: {url} ...", end="", flush=True)

    if custom_title:
        filename_tmpl = f"[{platform}] {origin_id} {custom_title}"
    else:
        filename_tmpl = f"[{platform}] {origin_id} %(title)s"
    
    save_tmpl = output_dir / filename_tmpl

    ydl_opts = {
        'outtmpl': str(save_tmpl) + ".%(ext)s",
        'format': 'bestvideo+bestaudio/best', # 最佳画质
        'ignoreerrors': True,
        'quiet': True,        # 不打印解析日志
        'no_warnings': True,  # 不打印警告
        'noprogress': False,  # 打印进度条
        
        'proxy': PROXY_URL,
        'ffmpeg_location': str(FFMPEG_PATH)
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info:
                filename = ydl.prepare_filename(info)
                
                final_path = Path(filename)
                if not final_path.exists():
                    mkv_path = final_path.with_suffix('.mkv')
                    if mkv_path.exists():
                        filename = str(mkv_path)
                
                print("    [成功]")
                return str(filename)
    except Exception as e:
        print(f"\n    [X] 下载出错: {e}")
        return None
    
    print("    [X] 未能获取文件")
    return None