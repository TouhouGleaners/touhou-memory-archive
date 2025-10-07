from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1 import videos

app = FastAPI(
    title="Touhou Memory Archive API",
    description="API for accessing Touhou Memory video archive data.",
    version="1.0.0",
)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(videos.router, prefix="/api/v1/videos", tags=["videos"])


@app.get("/")
def read_root():
    return {"message": "Welcome to Touhou Memory Archive API"}