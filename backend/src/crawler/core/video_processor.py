import logging
import asyncio

from crawler.api.models import VideoTag, VideoDetailData
from crawler.converters import pages_to_parts
from crawler.core.database import save_video
from crawler.core.video_fetcher import BiliClient
from shared.schemas import VideoSchema


logger = logging.getLogger(__name__)


class VideoService:
    """封装所有视频处理相关的业务逻辑"""
    def __init__(self, client: BiliClient):
        self.client = client
        self.touhou_keywords = {
            "东方Project", "东方project", "东方PROJECT",
            "東方Project", "東方project", "東方PROJECT",
            "Touhou", "東方", "车万", "ZUN", "Zun", "zun"
        }

    def _is_touhou(self, tags: list[str]) -> int:
        """自动检测是否为东方视频 是:1 否:2"""
        return 1 if any(keyword in tag for tag in tags for keyword in self.touhou_keywords) else 2

    async def process_video(self, video: VideoSchema, semaphore: asyncio.Semaphore):
        """
        处理单个视频的完整业务流程。

        输入的 video 是一个部分填充的 schema（来自空间搜索/合集列表），
        本方法会补充详情、标签、统计数据后保存到数据库。

        流程：
        1. 在 semaphore 限流下并发请求标签接口和详情接口
        2. 用详情数据填充 video 的 description、parts、分类、统计等字段
        3. 用标签数据填充 tags，同时过滤掉 bgm 类型的标签
        4. 根据标签关键词判断 touhou_status
        5. 保存到数据库
        """
        try:
            # semaphore 包住整个 gather，确保并发 I/O 真正受限
            async with semaphore:
                tags, detail = await asyncio.gather(
                    self.client.get_video_tags(video.bvid),
                    self.client.get_video_info(video.bvid),
                )

            # 用详情数据补全 video schema
            video.description = detail.desc
            video.category_id = detail.tid
            video.category_name = detail.tname
            video.copyright = detail.copyright
            video.state = detail.state

            video.view_count = detail.stat.view
            video.danmaku_count = detail.stat.danmaku
            video.reply_count = detail.stat.reply
            video.favorite_count = detail.stat.favorite
            video.coin_count = detail.stat.coin
            video.share_count = detail.stat.share
            video.like_count = detail.stat.like

            # 分P解析带防御性处理
            try:
                video.parts = pages_to_parts(detail.pages)
            except Exception as e:
                logger.warning(f"解析视频 {video.bvid} 分P失败: {e}", exc_info=True)
                video.parts = []

            # 标签处理：过滤 bgm 标签，然后判断是否为东方视频
            video.tags = [t.tag_name for t in tags if t.tag_type != "bgm"]
            video.touhou_status = self._is_touhou(video.tags)

            save_video(video)

            logger.info(f"视频 {video.bvid} 处理并保存成功。")

        except Exception as e:
            logger.error(f"处理视频 {video.bvid} 的业务逻辑时失败: {str(e)}")
            raise
