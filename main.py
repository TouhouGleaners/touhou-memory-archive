import os
import time
import logging
from dotenv import load_dotenv
from video_fetcher import BiliUPVideoInfoFetcher
from database import VideoDatabase


def setup_logging():
    logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s][%(levelname)s]%(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler()]
)

def main():
    setup_logging()
    logger = logging.getLogger(__name__)

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
            logger.info(f"正在处理UP主: {up_mid}")

            # 创建视频获取器实例
            fetcher = BiliUPVideoInfoFetcher(mid=up_mid, sessdata=sessdata)

            # 获取视频信息
            videos = fetcher.fetch_all_videos()
            logger.info(f"获取到 {len(videos)} 个视频")

            if videos:
                # 保存到数据库
                db.save_videos(videos, up_mid)
                logger.info(f"已保存视频信息到数据库: {db_path}")
            else:
                logger.warning(f"没有获取到视频信息，跳过保存。")

            if up_mid != up_mids[-1]:
                logger.info("等待10秒后处理下一个UP主...")
                time.sleep(10)

        # 查询并显示数据库中的视频总数
        total_count = 0
        for up_mid in up_mids:
            count = db.get_video_count_by_up(up_mid)
            logger.info(f"UP主 {up_mid} 的视频数量: {count}")
            total_count += count
        logger.info(f"数据库中视频总数量: {total_count}")


    except ValueError as e:
        logger.error(f"初始化错误: {e}")
    except Exception as e:
        logger.error(f"程序执行错误: {e}")

    finally:
        logger.info("程序结束")


if __name__ == "__main__":
    main()