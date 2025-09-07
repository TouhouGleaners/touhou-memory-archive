import sys
import time
import json
import requests
from typing import Callable

from config import HEADERS, DELAY_SECONDS
from Video import Video, VideoPart
from wbi_signer import WbiSigner


def fetch_video_list(mid: int, page_number: int = 1, page_size: int = 50, delay_seconds: Callable[[], float] = DELAY_SECONDS) -> list[Video]:
    params = {
        'mid': mid,
        'pn': page_number,
        'ps': page_size
    }

    img_key, sub_key = WbiSigner.get_wbi_keys() # 带缓存, 放心调用
    signed_params = WbiSigner.enc_wbi(params, img_key, sub_key)
    
    response = requests.get(
        url="https://api.bilibili.com/x/space/wbi/arc/search",
        params=signed_params,
        headers=HEADERS,
    ) # TODO: 错误处理
    time.sleep(delay_seconds())
    
    if response.status_code == 412:
        raise Exception("请求过快触发风控") # TODO: 重试机制

    data = json.loads(response.content.decode()) # TODO: 错误处理
    if data.get('code') != 0:
        raise Exception(f"API返回错误: {data.get('message', '未知错误')}")

    vlist = data['data']['list']['vlist']

    total_videos = data['data']['page']['count']
    total_pages = (total_videos + page_size - 1) // page_size  
    
    if page_number == 1 and total_videos > 1000:
        sys.setrecursionlimit(page_size * 2)

    if page_number < total_pages: # 递归获取下一页
        vlist += fetch_video_list(mid, page_number + 1, page_size)

    try:
        video_list = list(map(Video, vlist))
    except Exception as e:
        raise Exception(f"视频数据解析错误: {e}") # TODO: 具体错误处理

    return video_list


def fetch_video_parts(bvid: str, delay_seconds: Callable[[], float] = DELAY_SECONDS) -> list[VideoPart]:
    params = {
        'bvid': bvid
    }

    response = requests.get(
        url="https://api.bilibili.com/x/player/pagelist",
        params=params,
        headers=HEADERS,
    )
    time.sleep(delay_seconds())

    if response.status_code == 412:
        raise Exception("请求过快触发风控") # TODO: 重试机制
    
    data = json.loads(response.content.decode()) # TODO: 错误处理
    if data.get('code') != 0:
        raise Exception(f"API 返回错误: {data.get('message', '未知错误')}")
    

    plist = data['data']
    try:
        part_list = list(map(VideoPart, plist))
    except Exception as e:
        raise Exception(f"分P数据解析错误: {e}") # TODO: 具体错误处理
    
    return part_list


def fetch_video_tags(bvid: str, delay_seconds: Callable[[], float] = DELAY_SECONDS) -> list[str]:
    params = {
        'bvid': bvid
    }
    
    response = requests.get(
        url="https://api.bilibili.com/x/web-interface/view/detail/tag",
        params=params,
        headers=HEADERS,
    )
    time.sleep(delay_seconds())
    
    if response.status_code == 412:
        raise Exception("请求过快触发风控") # TODO: 重试机制
    
    data = json.loads(response.content.decode()) # TODO: 错误处理
    if data.get('code') != 0:
        raise Exception(f"API 返回错误: {data.get('message', '未知错误')}")
    
    return list(map(lambda tag: tag['tag_name'], data.get('data', [])))

    # TODO(重构): 提取公共请求逻辑

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