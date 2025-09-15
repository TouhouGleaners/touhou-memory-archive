import asyncio
import aiohttp
import logging
from typing import Callable, TypeVar, Dict, Any

from config import HEADERS, DELAY_SECONDS
from video import Video, VideoPart
from wbi_signer import WbiSigner


logger = logging.getLogger(__name__)

T = TypeVar('T')

async def make_api_request(
    url: str,
    params: Dict[str, Any],
    *,
    need_wbi: bool = False,
    retry_times: int = 3,
    retry_delay: int = 5,
    process_data: Callable[[Dict[str, Any]], T],
    session: aiohttp.ClientSession,
    delay_seconds: Callable[[], float] = DELAY_SECONDS,
) -> T:
    """
    公共 API 请求函数
    
    Args:
        url: API 地址
        params: 请求参数
        need_wbi: 是否需要 WBI 签名
        retry_times: 最大重试次数
        retry_delay: 重试延迟基础时间（秒）
        process_data: 处理返回数据的函数
        delay_seconds: 请求延迟函数
    
    Returns:
        经过 process_data 处理后的数据
    
    Raises:
        Exception: API 请求失败或数据处理出错
    """
    if need_wbi:
        img_key, sub_key = WbiSigner.get_wbi_keys()
        params = WbiSigner.enc_wbi(params, img_key, sub_key)
    
    for attempt in range(retry_times):
        try:
            async with session.get(url=url, params=params, headers=HEADERS) as response:
                # 处理风控
                if response.status == 412:
                    logger.warning(f"请求过快触发风控，等待 {retry_delay * (attempt + 1)} 秒后重试")
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                
                response.raise_for_status()  # 处理其他HTTP错误
                
                data = await response.json()
                if data.get('code') != 0:
                    raise Exception(f"API返回错误: {data.get('message', '未知错误')}")
                
                return process_data(data)
            
        except (aiohttp.ClientError, aiohttp.ClientResponseError) as e:
            if attempt < retry_times - 1:
                logger.warning(f"请求失败，等待 {retry_delay * (attempt + 1)} 秒后重试: {str(e)}")
                await asyncio.sleep(retry_delay * (attempt + 1))
                continue
            raise Exception(f"API请求失败: {str(e)}")
        
        except Exception as e:
            if attempt < retry_times - 1:
                logger.warning(f"数据处理失败，等待 {retry_delay * (attempt + 1)} 秒后重试: {str(e)}")
                await asyncio.sleep(retry_delay * (attempt + 1))
                continue
            raise
        finally:
            await asyncio.sleep(delay_seconds())


async def fetch_video_page(mid: int, session: aiohttp.ClientSession, page_number: int, page_size: int, delay_seconds: Callable[[], float] = DELAY_SECONDS) -> dict:
    """获取单页视频"""
    params = {'mid': mid, 'pn': page_number, 'ps': page_size}

    def process_video_page(data: Dict[str, Any]) -> dict:
        vlist = data['data']['list']['vlist']
        total_videos = data['data']['page']['count']

        page_videos = []
        for item in vlist:
            try:
                page_videos.append(Video(item))
            except Exception as e:
                logger.warning(f"视频 {item.get('bvid')} 数据解析错误: {e}")
        return {'page': page_number, 'total': total_videos, 'videos': page_videos}

    return await make_api_request(
        url="https://api.bilibili.com/x/space/wbi/arc/search",
        params=params,
        need_wbi=True,
        process_data=process_video_page,
        session=session,
        delay_seconds=delay_seconds,
    )

async def fetch_video_list(mid: int, session: aiohttp.ClientSession, page_size: int = 50, delay_seconds: Callable[[], float] = DELAY_SECONDS) -> list[Video]:
    """获取用户所有视频列表（使用循环代替递归）"""
    # 获取第一页以确认页数
    try:
        first_page = await fetch_video_page(mid, session, 1, page_size, delay_seconds)
        total_videos = first_page['total']
        total_pages = (total_videos + page_size - 1 ) // page_size
    except Exception as e:
        logger.error(f"获取用户 {mid} 视频列表失败: {str(e)}")
        return []
    
    # 创建所有页面的请求任务
    tasks = []
    for page in range(1, total_pages + 1):
        tasks.append(fetch_video_page(mid, session, page, page_size, delay_seconds))

    # 并发执行所有页面请求
    try:
        pages = await asyncio.gather(*tasks, return_exceptions=False)
    except Exception as e:
        logger.error(f"并发获取用户 {mid} 视频分页失败: {str(e)}")
        return []
    
    # 合并所有视频
    all_videos = []
    for page in pages:
        if isinstance(page, Exception):
            logger.error(f"获取页面失败: {str(page)}")
        else:
            all_videos.extend(page['videos'])
    
    return all_videos


async def fetch_video_parts(bvid: str, session: aiohttp.ClientSession, delay_seconds: Callable[[], float] = DELAY_SECONDS) -> list[VideoPart]:
    """获取单个视频的分P信息"""
    params = {
        'bvid': bvid
    }
    
    def process_video_parts(data: Dict[str, Any]) -> list[VideoPart]:
        try:
            return list(map(VideoPart, data['data']))
        except Exception as e:
            raise Exception(f"分P数据解析错误: {e}")
    
    return await make_api_request(
        url="https://api.bilibili.com/x/player/pagelist",
        params=params,
        need_wbi=False,
        process_data=process_video_parts,
        session=session,
        delay_seconds=delay_seconds,
    )

async def fetch_video_parts_batch(
    videos: list[Video],
    session: aiohttp.ClientSession,
    max_concurrent: int = 5,
    delay_seconds: Callable[[], float] = DELAY_SECONDS,
    batch_retry_times: int = 2,
    batch_retry_delay: int = 10
) -> Dict[str, list[VideoPart]]:
    """
    批量获取多个视频的分P信息
    
    Args:
        videos: 要获取分P信息的视频列表
        session: aiohttp会话
        max_concurrent: 最大并发请求数
        delay_seconds: 请求延迟函数
        batch_retry_times: 批次重试次数
        batch_retry_delay: 批次重试延迟（秒）
    
    Returns:
        Dict[str, list[VideoPart]]: 以视频bvid为键的分P信息字典
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    results_dict = {}
    failed_videos = videos
    
    for attempt in range(batch_retry_times + 1):
        if not failed_videos:
            break
            
        if attempt > 0:
            logger.warning(f"第 {attempt} 次重试获取 {len(failed_videos)} 个视频的分P信息")
            await asyncio.sleep(batch_retry_delay * attempt)
        
        async def fetch_with_semaphore(video: Video) -> tuple[str, list[VideoPart], bool]:
            async with semaphore:
                try:
                    parts = await fetch_video_parts(video.bvid, session, delay_seconds)
                    return video.bvid, parts, True
                except Exception as e:
                    logger.error(f"获取视频 {video.bvid} 分P信息失败: {str(e)}")
                    return video.bvid, [], False
        
        # 创建当前批次的请求任务
        tasks = [fetch_with_semaphore(video) for video in failed_videos]
        
        # 并发执行请求
        try:
            current_results = await asyncio.gather(*tasks, return_exceptions=False)
            
            # 更新结果并收集失败的视频
            next_failed_videos = []
            for bvid, parts, success in current_results:
                if success:
                    results_dict[bvid] = parts
                else:
                    next_video = next(v for v in failed_videos if v.bvid == bvid)
                    next_failed_videos.append(next_video)
            
            failed_videos = next_failed_videos
            
            if failed_videos:
                logger.warning(f"本批次仍有 {len(failed_videos)} 个视频获取分P信息失败")
            
        except Exception as e:
            logger.error(f"批量获取分P信息时发生错误: {str(e)}")
            continue
    
    if failed_videos:
        logger.error(f"最终仍有 {len(failed_videos)} 个视频的分P信息获取失败")
        # 为失败的视频添加空分P列表
        for video in failed_videos:
            results_dict[video.bvid] = []
    
    return results_dict


async def fetch_video_tags(bvid: str, session: aiohttp.ClientSession, delay_seconds: Callable[[], float] = DELAY_SECONDS) -> list[str]:
    """获取单个视频的标签"""
    params = {
        'bvid': bvid
    }
    
    def process_video_tags(data: Dict[str, Any]) -> list[str]:
        return list(map(lambda tag: tag['tag_name'], data.get('data', [])))
    
    return await make_api_request(
        url="https://api.bilibili.com/x/web-interface/view/detail/tag",
        params=params,
        need_wbi=False,
        process_data=process_video_tags,
        session=session,
        delay_seconds=delay_seconds,
    )

async def fetch_video_tags_batch(
    videos: list[Video],
    session: aiohttp.ClientSession,
    max_concurrent: int = 5,
    delay_seconds: Callable[[], float] = DELAY_SECONDS,
    batch_retry_times: int = 2,
    batch_retry_delay: int = 10
) -> Dict[str, list[str]]:
    """
    批量获取多个视频的标签，支持批次级别的重试
    
    Args:
        videos: 要获取标签的视频列表
        session: aiohttp会话
        max_concurrent: 最大并发请求数
        delay_seconds: 请求延迟函数
        batch_retry_times: 批次重试次数
        batch_retry_delay: 批次重试延迟（秒）
    
    Returns:
        Dict[str, list[str]]: 以视频bvid为键的标签字典
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    results_dict = {}
    failed_videos = videos
    
    for attempt in range(batch_retry_times + 1):
        if not failed_videos:
            break
            
        if attempt > 0:
            logger.warning(f"第 {attempt} 次重试获取 {len(failed_videos)} 个视频的标签")
            await asyncio.sleep(batch_retry_delay * attempt)
        
        async def fetch_with_semaphore(video: Video) -> tuple[str, list[str], bool]:
            async with semaphore:
                try:
                    tags = await fetch_video_tags(video.bvid, session, delay_seconds)
                    return video.bvid, tags, True
                except Exception as e:
                    logger.error(f"获取视频 {video.bvid} 标签失败: {str(e)}")
                    return video.bvid, [], False
        
        # 创建当前批次的请求任务
        tasks = [fetch_with_semaphore(video) for video in failed_videos]
        
        # 并发执行请求
        try:
            current_results = await asyncio.gather(*tasks, return_exceptions=False)
            
            # 更新结果并收集失败的视频
            next_failed_videos = []
            for bvid, tags, success in current_results:
                if success:
                    results_dict[bvid] = tags
                else:
                    next_video = next(v for v in failed_videos if v.bvid == bvid)
                    next_failed_videos.append(next_video)
            
            failed_videos = next_failed_videos
            
            if failed_videos:
                logger.warning(f"本批次仍有 {len(failed_videos)} 个视频获取标签失败")
            
        except Exception as e:
            logger.error(f"批量获取标签时发生错误: {str(e)}")
            continue
    
    if failed_videos:
        logger.error(f"最终仍有 {len(failed_videos)} 个视频的标签获取失败")
        # 为失败的视频添加空标签列表
        for video in failed_videos:
            results_dict[video.bvid] = []
    
    return results_dict

if __name__ == "__main__":
    if True: # test fetch_video_list
        mid = 66508
        video_list = fetch_video_list(mid)
        print(f"Total videos fetched: {len(video_list)}")


    if True: # test fetch_video_parts
        bvid = "BV1Gx411w7wU"
        plist = fetch_video_parts(bvid)
        print(f"Total parts fetched: {len(plist)}")

    if True: # test fetch_video_tags
        bvid = "BV1Gx411w7wU"
        tags = fetch_video_tags(bvid)
        print(f"Tags: {tags}")