CREATE TABLE users (
    mid BIGINT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE videos (
    aid BIGINT PRIMARY KEY,
    bvid TEXT NOT NULL UNIQUE,
    mid BIGINT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    pic TEXT,
    created TIMESTAMP,
    tags TEXT,
    touhou_status INTEGER NOT NULL DEFAULT 0,  -- 0:未检测 1:自动检测为东方 2:自动检测为非东方 3:人工确认为东方 4:人工确认为非东方
    season_id INT,
    FOREIGN KEY (mid) REFERENCES users (mid)
);

CREATE TABLE video_parts (
    cid BIGINT PRIMARY KEY,
    aid BIGINT NOT NULL,
    page INTEGER NOT NULL,
    part TEXT NOT NULL,      -- 实际上是分P的标题
    duration INTEGER,
    ctime TIMESTAMP,
    FOREIGN KEY (aid) REFERENCES videos (aid)
);

