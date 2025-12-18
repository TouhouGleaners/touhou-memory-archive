import json
from pathlib import Path

from backend.app.database import get_db
from backend.app.crud.crud_video import get_videos


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def export_data():
    print(">>> 正在初始化导出任务...")
    
    # 输出路径
    public_dir = PROJECT_ROOT / "frontend" / "public"
    public_dir.mkdir(parents=True, exist_ok=True)
    target_file = public_dir / "videos.json"

    # 获取数据库连接
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        print(">>> 正在从数据库读取数据...")
        
        videos_models = get_videos(db, is_touhou=False)

        print(f">>> 格式化 {len(videos_models)} 条数据...")
        data_list = [v.model_dump() for v in videos_models]

        # 写入文件
        print(f">>> 写入文件: {target_file}")
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(data_list, f, ensure_ascii=False, indent=None, separators=(',', ':'))

        print(">>> 导出完成.")

    except Exception as e:
        print(f"!!! 导出出错: {e}")
        raise
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


if __name__ == "__main__":
    export_data()