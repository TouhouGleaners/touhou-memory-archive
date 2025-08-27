import os
import time
from dotenv import load_dotenv
from video_fetcher import BiliUPVideoInfoFetcher
from database import VideoDatabase


def main():
    # 加载环境变量
    load_dotenv(".env")

    # 获取配置
    up_mid_srt = os.getenv("UP_UID")
    up_mids = [mid.strip() for mid in up_mid_srt.split(",")]
    sessdata = os.getenv("SESSDATA")

    db_path = "bili_videos.db"

    try:
        # 创建数据库实例
        db = VideoDatabase(db_path)

        # 遍历所有UP主
        for up_mid in up_mids:
            print(f"正在处理UP主: {up_mid}")

            # 创建视频获取器实例
            fetcher = BiliUPVideoInfoFetcher(mid=up_mid, sessdata=sessdata)

            # 获取视频信息
            videos = fetcher.fetch_all_videos()
            print(f"获取到 {len(videos)} 个视频")

            if videos:
                # 保存到数据库
                db.save_videos(videos, up_mid)
                print(f"已保存视频信息到数据库: {db_path}")
            else:
                print(f"没有获取到视频信息，跳过保存。")

            if up_mid != up_mids[-1]:
                print("等待10秒后处理下一个UP主...")
                time.sleep(10)

        # 查询并显示数据库中的视频总数
        total_count = 0
        for up_mid in up_mids:
            count = db.get_video_count_by_up(up_mid)
            print(f"UP主 {up_mid} 的视频数量: {count}")
            total_count += count
        print(f"数据库中视频总数量: {total_count}")


    except ValueError as e:
        print(f"初始化错误: {e}")
    except Exception as e:
        print(f"程序执行错误: {e}")

    finally:
        print("程序结束")


if __name__ == "__main__":
    main()