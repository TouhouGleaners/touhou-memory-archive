CREATE TABLE IF NOT EXISTS users (
    mid BIGINT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS videos (
    aid BIGINT PRIMARY KEY,
    bvid TEXT NOT NULL UNIQUE,
    mid BIGINT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    cover_url TEXT,
    duration INTEGER,
    published_at INTEGER,
    created_at INTEGER,
    category_id INTEGER,
    category_name TEXT,
    copyright INTEGER,
    state INTEGER,
    view_count INTEGER,
    danmaku_count INTEGER,
    reply_count INTEGER,
    favorite_count INTEGER,
    coin_count INTEGER,
    share_count INTEGER,
    like_count INTEGER,
    tags TEXT,
    touhou_status INTEGER NOT NULL DEFAULT 0,
    season_id INTEGER,
    FOREIGN KEY (mid) REFERENCES users (mid)
);

CREATE TABLE IF NOT EXISTS video_parts (
    cid BIGINT PRIMARY KEY,
    aid BIGINT NOT NULL,
    idx INTEGER NOT NULL,
    title TEXT NOT NULL,
    duration INTEGER,
    FOREIGN KEY (aid) REFERENCES videos (aid)
);
