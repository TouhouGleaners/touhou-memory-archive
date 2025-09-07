CREATE TABLE users (
    mid BIGINT PRIMARY KEY,
    name TEXT NOT NULL
);


CREATE TABLE videos (
    aid BIGINT PRIMARY KEY,
    bvid TEXT NOT NULL UNIQUE,
    mid INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    pic TEXT,
    created TIMESTAMP,
    FOREIGN KEY (mid) REFERENCES users (mid)
); -- TODO: tags, is_touhou

CREATE TABLE video_parts (
    cid BIGINT PRIMARY KEY,
    aid BIGINT NOT NULL,
    page INTEGER NOT NULL,
    part TEXT NOT NULL,      -- 实际上是分P的标题
    duration INTEGER,
    ctime TIMESTAMP,
    FOREIGN KEY (aid) REFERENCES videos (aid)
);

