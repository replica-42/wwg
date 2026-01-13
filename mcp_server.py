import json
from datetime import datetime
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("tools")


@mcp.tool
def query_weibo_by_time(start: str, end: str) -> list[dict[str, str]]:
    """
    查询指定 ISO 8601 时间范围内的微博内容。

    Args:
        start (str): 起始时间，ISO 8601 格式（如 "2025-01-01T00:00:00"）
        end (str): 结束时间，ISO 8601 格式（如 "2025-01-31T23:59:59"）

    Returns:
        list[dict]: 包含 create_at 和 content 的字典列表
    """
    try:
        start_time = datetime.fromisoformat(start)
        end_time = datetime.fromisoformat(end)
    except ValueError as e:
        raise ValueError(f"Invalid ISO format datetime: {e}")

    file_path = Path("weibo.jsonl")
    if not file_path.exists():
        return []  # 或抛出 FileNotFoundError，视需求而定

    result = []
    for line in file_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            content = json.loads(line)
            # 假设 create_at 格式为 "2025-01-10T12:34:56"
            create_at_dt = datetime.strptime(content["create_at"], "%Y-%m-%dT%H:%M:%S")
        except (json.JSONDecodeError, KeyError, ValueError):
            continue  # 跳过无效行

        if start_time <= create_at_dt <= end_time:
            result.append(
                {"create_at": content["create_at"], "content": content["content"]}
            )

    return result


if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8000)
