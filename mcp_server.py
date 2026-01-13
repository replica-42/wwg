import json
import re
from datetime import datetime
from pathlib import Path

import yaml
from fastmcp import FastMCP

# Global blog index - will be populated at module level
BLOG_INDEX = []


def _parse_blog_file(file_path: Path) -> list[dict]:
    """Parse a blog markdown file and extract paragraphs with metadata."""
    content = file_path.read_text(encoding="utf-8")

    # Split frontmatter and body
    if not content.startswith("---"):
        return []

    parts = content.split("---", 2)
    if len(parts) < 3:
        return []

    frontmatter = parts[1]
    body = parts[2]

    # Parse frontmatter
    meta = {}
    if yaml is not None:
        try:
            meta = yaml.safe_load(frontmatter)
            if meta is None:
                meta = {}
        except Exception:
            pass

    title = meta.get("title", "")
    date: datetime = meta.get("date")  # type: ignore
    date_str = date.strftime("%Y-%m-%dT%H:%M:%S")
    categories = meta.get("categories", [])

    if not date_str:
        return []

    # Remove code blocks from body but preserve inline code
    lines = body.split("\n")
    processed_lines = []
    in_code_block = False

    for line in lines:
        stripped_line = line.rstrip()
        # Check for code block start/end (``` or ~~~)
        if stripped_line.startswith("```") or stripped_line.startswith("~~~"):
            in_code_block = not in_code_block
            continue

        if not in_code_block:
            processed_lines.append(line)

    body = "\n".join(processed_lines)

    # Process body - split into paragraphs
    paragraphs: list[dict[str, str]] = []
    current_para: list[str] = []

    for line in body.split("\n"):
        line = line.strip()

        # Skip blockquotes (lines starting with >)
        if line.startswith(">"):
            continue

        # Skip headings (lines starting with #)
        if line.startswith("#"):
            continue

        if line.startswith("!"):
            continue

        # Handle empty lines as paragraph separators
        if not line:
            if current_para:
                para_text = ";".join(current_para)
                # Remove markdown links - keep only link text
                para_text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", para_text)
                # Inline code (text between single backticks) is preserved automatically
                paragraphs.append(
                    {
                        "content": para_text,
                        "create_at": date_str,
                        "title": title,
                        "categories": categories,
                        "type": "blog",
                    }
                )
                current_para = []
            continue

        # Handle list items - treat as part of current paragraph
        if line.startswith("- ") or line.startswith("* "):
            line = line[2:].strip()

        current_para.append(line)

    # Handle last paragraph
    if current_para:
        para_text = ";".join(current_para)
        para_text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", para_text)
        paragraphs.append(
            {
                "content": para_text,
                "create_at": date_str,
                "title": title,
                "categories": categories,
                "type": "blog",
            }
        )

    return paragraphs


def _build_blog_index():
    """Build index of all blog posts at startup."""
    global BLOG_INDEX
    BLOG_INDEX = []

    blogs_dir = Path("blogs")
    if not blogs_dir.exists():
        return

    for blog_file in blogs_dir.rglob("*.md"):
        try:
            paragraphs = _parse_blog_file(blog_file)
            BLOG_INDEX.extend(paragraphs)
        except Exception:
            continue


mcp = FastMCP("tools")


@mcp.tool
def query_weibo_by_time(start: str, end: str) -> list[dict]:
    """
    查询指定 ISO 8601 时间范围内的微博内容和博客内容。

    Args:
        start (str): 起始时间，ISO 8601 格式（如 "2025-01-01T00:00:00"）
        end (str): 结束时间，ISO 8601 格式（如 "2025-01-31T23:59:59"）

    Returns:
        list[dict]: 包含微博和博客内容的字典列表。微博条目包含 create_at 和 content 字段，
                   博客条目额外包含 title、categories 和 type="blog" 字段。
    """
    try:
        start_time = datetime.fromisoformat(start)
        end_time = datetime.fromisoformat(end)
    except ValueError as e:
        raise ValueError(f"Invalid ISO format datetime: {e}")

    result = []

    # Add weibo content
    file_path = Path("weibo.jsonl")
    if file_path.exists():
        for line in file_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                content = json.loads(line)
                # 假设 create_at 格式为 "2025-01-10T12:34:56"
                create_at_dt = datetime.strptime(
                    content["create_at"], "%Y-%m-%dT%H:%M:%S"
                )
            except (json.JSONDecodeError, KeyError, ValueError):
                continue  # 跳过无效行

            if start_time <= create_at_dt <= end_time:
                result.append(
                    {
                        "create_at": content["create_at"],
                        "content": content["content"],
                        "type": "weibo",
                    }
                )

    # Add blog content from the same time range
    for blog_entry in BLOG_INDEX:
        try:
            blog_create_at_dt = datetime.strptime(
                blog_entry["create_at"], "%Y-%m-%dT%H:%M:%S"
            )
            if start_time <= blog_create_at_dt <= end_time:
                result.append(blog_entry)
        except (ValueError, KeyError):
            continue

    # Sort all results by create_at
    result.sort(key=lambda x: datetime.strptime(x["create_at"], "%Y-%m-%dT%H:%M:%S"))

    return result


@mcp.tool
def get_historical_profiles(start_month: str, offset: int) -> str:
    """
    获取历史用户画像数据。

    Args:
        start_month (str): 起始月份，格式为 "YYYY-MM"（如 "2024-11"）
        offset (int): 偏移量，表示要获取从 T-offset 月到 T-1 月的数据

    Returns:
        str: 包含按时间顺序排列的用户画像JSON数组的字符串
    """
    try:
        # 解析起始月份
        start_year, start_month_num = map(int, start_month.split("-"))

        # 计算目标月份范围：从 T-offset 到 T-1
        profiles = []

        for i in range(offset, 0, -1):
            # 计算年月
            year = start_year
            month = start_month_num - i

            # 处理跨年情况
            while month <= 0:
                month += 12
                year -= 1

            # 格式化为 YYYY-MM
            target_month = f"{year:04d}-{month:02d}"

            # 构建文件路径
            file_path = Path("preferences") / f"{target_month}.json"

            # 检查文件是否存在
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        profile_data = json.load(f)
                        profiles.append(profile_data)
                except (json.JSONDecodeError, IOError):
                    # 如果文件存在但无法读取或解析，跳过该文件
                    continue

        # 返回序列化的JSON数组字符串
        return json.dumps(profiles, ensure_ascii=False)

    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid input parameters: {e}")


if __name__ == "__main__":
    _build_blog_index()
    mcp.run(transport="http", host="127.0.0.1", port=8000)
