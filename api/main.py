from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from .models import Video
from shared.database import Database


app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:5173",  # Vite
    "http://localhost:8080",  # Vue CLI
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/videos", response_model=List[Video])
def read_videos():
    """
    提供视频列表的 JSON 数据给前端
    """
    videos_data = Database.get_all_videos_for_api()
    return videos_data

@app.get("/")
def read_root():
    return {"code": 200, "message": "Welcome to Touhou Memory Archive API"}
