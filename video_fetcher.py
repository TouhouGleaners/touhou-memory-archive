import time
import csv
import asyncio
import aiohttp
import logging
from wbi_signer import WbiSigner


logger = logging.getLogger(__name__)

class AsyncBiliUPVideoInfoFetcher:
    """B站指定UP主视频信息获取类(异步版)"""
    def __init__(self, mid: str, sessdata: str, db, max_concurrent: int = 5):
        if not sessdata or not sessdata.strip():
            logger.error("SESSDATA是必需的参数，不能为空")
            raise ValueError("SESSDATA是必需的参数，不能为空")
        
        self.mid = mid
        self.sessdata = sessdata
        self.db = db
        self.max_concurrent = max_concurrent
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
            'Cookie': f"SESSDATA={sessdata}",
            'Referer': 'https://www.bilibili.com',
            'Origin': 'https://www.bilibili.com',
            'Accept': 'application/json, text/plain, */*',
            'Connection': 'keep-alive',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }

    async def get_video_tags(self, session: aiohttp.ClientSession, bvid: str) -> list[str]:
        """获取视频标签信息"""
        # 为特定视频设置 Referer
        headers = {
            **self.headers,
            'Referer': f'https://www.bilibili.com/video/{bvid}'
        }
        
        max_retries = 3
        retry_delay = 1  # 初始重试延迟（秒）
        
        for attempt in range(max_retries):
            try:
                async with session.get(
                    url=f"https://api.bilibili.com/x/web-interface/view/detail/tag",
                    params={'bvid': bvid},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 412:
                        if attempt < max_retries - 1:
                            logger.warning(f"视频 {bvid} 获取标签触发风控，等待 {retry_delay * (attempt + 1)} 秒后重试")
                            await asyncio.sleep(retry_delay * (attempt + 1))
                            continue
                    
                    response.raise_for_status()
                    data = await response.json()
                    
                    if data.get('code') != 0:
                        logger.warning(f"获取视频 {bvid} 标签失败: {data.get('code')}, {data.get('message')}")
                        return []
                    
                    return [tag['tag_name'] for tag in data.get('data', [])]
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"视频 {bvid} 获取标签失败，等待 {retry_delay * (attempt + 1)} 秒后重试: {e}")
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                logger.error(f"获取视频 {bvid} 标签失败，已达最大重试次数: {e}")
                return []
            
        return []  # 所有重试都失败后返回空列表

    async def get_cid_by_bvid(self, session: aiohttp.ClientSession, bvid: str) -> list[dict]:
        """通过bvid获取视频所有分P的cid信息(异步版)"""
        # 为特定视频设置 Referer
        headers = {
            **self.headers,
            'Referer': f'https://www.bilibili.com/video/{bvid}'
        }
        
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                async with session.get(
                    url="https://api.bilibili.com/x/player/pagelist",
                    params={'bvid': bvid},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 412:
                        if attempt < max_retries - 1:
                            logger.warning(f"视频 {bvid} 获取分P信息触发风控，等待 {retry_delay * (attempt + 1)} 秒后重试")
                            await asyncio.sleep(retry_delay * (attempt + 1))
                            continue

                    response.raise_for_status()
                    data = await response.json()

                    if data.get('code') != 0:
                        logger.warning(f"获取视频 {bvid} 分P信息失败: {data.get('code')}, {data.get('message')}")
                        return []

                    return data.get('data', [])
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"获取视频 {bvid} 分P信息失败，等待 {retry_delay * (attempt + 1)} 秒后重试: {e}")
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                logger.error(f"获取视频 {bvid} 分P信息失败，已达最大重试次数: {e}")
                return []

        return []

    async def fetch_all_videos(self) -> list[dict]:
        """获取目标UP主的所有视频信息(异步版)"""
        img_key, sub_key = WbiSigner.get_wbi_keys()  # 获取 WBI 签名秘钥

        all_videos = []
        page = 1
        page_size = 50  # 每页视频数量

        # 创建aiohttp会话
        async with aiohttp.ClientSession(headers=self.headers) as session:
            while True:
                params = {
                    'mid': self.mid,
                    'pn': page,
                    'ps': page_size
                }

                # 添加 WBI 签名
                signed_params = WbiSigner.enc_wbi(params, img_key, sub_key)

                try:
                    async with session.get(
                        url="https://api.bilibili.com/x/space/wbi/arc/search",
                        params=signed_params,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        response.raise_for_status()
                        data = await response.json()

                        # 检查返回状态
                        if data.get('code') != 0:
                            logger.error(f"API错误: {data.get('code')}, 错误信息: {data.get('message')}")
                            break

                        # 检查数据结构
                        if 'data' not in data or 'list' not in data['data'] or 'vlist' not in data['data']['list']:
                            break  
                        
                        # 获取分页信息 计算总页数
                        page_info = data['data']['page']
                        total_pages = (page_info['count'] + page_size - 1) // page_size  

                        videos = data['data']['list']['vlist']
                        if not videos:
                            break  

                        # 从第一个视频获取UP主信息并保存（因为每个视频都包含相同的author信息）
                        if videos and page == 1:
                            first_video = videos[0]
                            up_name = first_video.get('author', '')
                            self.db.save_up_info(self.mid, up_name)
                        
                        # 使用信号量控制并发数
                        semaphore = asyncio.Semaphore(self.max_concurrent)

                        async def get_video_info_with_parts_and_tags(video):
                            async with semaphore:
                                # 获取分P信息
                                parts = await self.get_cid_by_bvid(session, video['bvid'])
                                video['parts'] = parts
                                # 获取标签信息
                                tags = await self.get_video_tags(session, video['bvid'])
                                video['tags'] = tags
                                await asyncio.sleep(0.1)  # 避免请求过快
                                return video

                        # 并发获取所有视频的分P信息和标签信息
                        tasks = [get_video_info_with_parts_and_tags(video) for video in videos]
                        videos = await asyncio.gather(*tasks)

                        all_videos.extend(videos)
                        
                        # 分页控制
                        if page >= total_pages:
                            break  # 如果已经是最后一页，则退出循环

                        page += 1  # 翻页
                        await asyncio.sleep(0.3)  # 翻页延迟

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    logger.error(f"请求失败: {e}")
                    break

        return all_videos
    
    def save_to_csv(self, videos: list[dict], filename: str):
        """将视频信息保存到 CSV 文件"""
        if not videos:
            logger.warning("没有视频数据可保存")
            return
        
        # 需要保存的字段
        fields = ['title', 'aid', 'bvid', 'cid', 'parts_count', 'created', 'play', 
                  'video_review', 'comment', 'length', 'pic', 'description']

        try:
            with open(filename, mode='w', newline='', encoding='utf-8-sig') as file:
                writer = csv.DictWriter(file, fieldnames=fields)
                writer.writeheader()
                
                for video in videos:
                    # 时间戳转换
                    created_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(video['created']))

                    # 获取分P信息与其对应的CID
                    parts = video.get('parts', [])
                    parts_count = len(parts)
                    all_cids = [str(part['cid']) for part in parts]

                    row = {
                        'title': video.get('title', ''),
                        'aid': video.get('aid', ''),
                        'bvid': video.get('bvid', ''),
                        'cid': '; '.join(all_cids),  # 分P的CID合并为字符串
                        'parts_count': parts_count,
                        'created': created_time,
                        'play': video.get('play', ''),
                        'video_review': video.get('video_review', ''),
                        'comment': video.get('comment', ''),
                        'length': video.get('length', ''),
                        'pic': video.get('pic', ''),
                        'description': video.get('description', '')
                    }
                    writer.writerow(row)
            logger.info(f"成功保存 {len(videos)} 条视频信息到 {filename}")
        except IOError as e:
            logger.error(f"保存到CSV失败: {e}")