import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def split_by_month(input_file: str, output_dir: str) -> None:
    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 用于存储按月分组的数据
    monthly_data = defaultdict(list)

    # 读取输入文件
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            # 解析日期并提取年月
            date = datetime.fromisoformat(data["create_at"])
            month_key = f"{date.year}-{date.month:02d}"
            monthly_data[month_key].append(data)

    # 写入分组后的文件
    for month, entries in monthly_data.items():
        output_file = Path(output_dir) / f"{month}.jsonl"
        with open(output_file, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# 使用示例
if __name__ == "__main__":
    split_by_month("../weibo.jsonl", "output")
