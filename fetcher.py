import sys
import time
import requests
import logging
from typing import Callable, TypeVar, Dict, Any

from config import HEADERS, DELAY_SECONDS
from Video import Video, VideoPart
from wbi_signer import WbiSigner


logger = logging.getLogger(__name__)

T = TypeVar('T')

def make_api_request(
    url: str,
    params: Dict[str, Any],
    *,
    need_wbi: bool = False,
    retry_times: int = 3,
    retry_delay: int = 5,
    process_data: Callable[[Dict[str, Any]], T],
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
            response = requests.get(url=url, params=params, headers=HEADERS)
            time.sleep(delay_seconds())
            
            # 处理风控
            if response.status_code == 412:
                logger.warning(f"请求过快触发风控，等待 {retry_delay * (attempt + 1)} 秒后重试")
                time.sleep(retry_delay * (attempt + 1))
                continue
            
            response.raise_for_status()  # 处理其他HTTP错误
            
            data = response.json()
            if data.get('code') != 0:
                raise Exception(f"API返回错误: {data.get('message', '未知错误')}")
            
            return process_data(data)
            
        except requests.exceptions.RequestException as e:
            if attempt < retry_times - 1:
                logger.warning(f"请求失败，等待 {retry_delay * (attempt + 1)} 秒后重试: {str(e)}")
                time.sleep(retry_delay * (attempt + 1))
                continue
            raise Exception(f"API请求失败: {str(e)}")
        
        except Exception as e:
            if attempt < retry_times - 1:
                logger.warning(f"数据处理失败，等待 {retry_delay * (attempt + 1)} 秒后重试: {str(e)}")
                time.sleep(retry_delay * (attempt + 1))
                continue
            raise

def fetch_video_list(mid: int, page_number: int = 1, page_size: int = 50, delay_seconds: Callable[[], float] = DELAY_SECONDS) -> list[Video]:
    params = {
        'mid': mid,
        'pn': page_number,
        'ps': page_size
    }
    
    def process_video_list(data: Dict[str, Any]) -> list[Video]:
        vlist = data['data']['list']['vlist']
        total_videos = data['data']['page']['count']
        total_pages = (total_videos + page_size - 1) // page_size
        
        if page_number == 1 and total_videos > 1000:
            sys.setrecursionlimit(page_size * 2)
        
        if page_number < total_pages:  # 递归获取下一页
            vlist += fetch_video_list(mid, page_number + 1, page_size)
        
        try:
            return list(map(Video, vlist))
        except Exception as e:
            raise Exception(f"视频数据解析错误: {e}")
    
    return make_api_request(
        url="https://api.bilibili.com/x/space/wbi/arc/search",
        params=params,
        need_wbi=True,
        process_data=process_video_list,
        delay_seconds=delay_seconds,
    )


def fetch_video_parts(bvid: str, delay_seconds: Callable[[], float] = DELAY_SECONDS) -> list[VideoPart]:
    params = {
        'bvid': bvid
    }
    
    def process_video_parts(data: Dict[str, Any]) -> list[VideoPart]:
        try:
            return list(map(VideoPart, data['data']))
        except Exception as e:
            raise Exception(f"分P数据解析错误: {e}")
    
    return make_api_request(
        url="https://api.bilibili.com/x/player/pagelist",
        params=params,
        need_wbi=False,
        process_data=process_video_parts,
        delay_seconds=delay_seconds,
    )


def fetch_video_tags(bvid: str, delay_seconds: Callable[[], float] = DELAY_SECONDS) -> list[str]:
    params = {
        'bvid': bvid
    }
    
    def process_video_tags(data: Dict[str, Any]) -> list[str]:
        return list(map(lambda tag: tag['tag_name'], data.get('data', [])))
    
    return make_api_request(
        url="https://api.bilibili.com/x/web-interface/view/detail/tag",
        params=params,
        need_wbi=False,
        process_data=process_video_tags,
        delay_seconds=delay_seconds,
    )

if __name__ == "__main__":
    if False: # test fetch_video_list
        mid = 66508
        video_list = fetch_video_list(mid)
        print(f"Total videos fetched: {len(video_list)}")


    if False: # test fetch_video_parts
        bvid = "BV1Gx411w7wU"
        plist = fetch_video_parts(bvid)
        print(f"Total parts fetched: {len(plist)}")

    if True: # test fetch_video_tags
        bvid = "BV1Gx411w7wU"
        tags = fetch_video_tags(bvid)
        print(f"Tags: {tags}")