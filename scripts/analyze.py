import json
from datetime import datetime
from pathlib import Path

import numpy as np
from matplotlib import colormaps
from matplotlib import pyplot as plt


def load_weibo(filename: str) -> list[tuple[str, datetime]]:
    lines: list[str] = Path(filename).read_text(encoding="utf-8").splitlines()
    result = []
    for line in lines:
        data = json.loads(line)
        result.append((data["content"], datetime.fromisoformat(data["create_at"])))
    return result


def plot_polar_by_month() -> None:
    weibo_list = load_weibo("weibo.jsonl")

    # 12 months
    N = 12
    width = 2 * np.pi * 0.8 / N
    theta = np.linspace(0.0, 2 * np.pi, N, endpoint=False, dtype=np.float64)

    words_count = [0] * N
    for weibo in weibo_list:
        if weibo[1].year == 2024:
            words_count[weibo[1].month - 1] += len(weibo[0])

    radii = np.array(words_count, dtype=np.int32)

    colors = colormaps.get_cmap("viridis")(radii / max(radii))

    ax = plt.subplot(projection="polar")

    # direction
    ax.set_theta_direction(-1)  # type: ignore
    ax.set_theta_zero_location("N")  # type: ignore

    # xticks
    x_label = list(map(str, range(1, N + 1)))
    ax.set_xticks(np.linspace(0.0, 2 * np.pi, N, endpoint=False, dtype=np.float64))
    ax.set_xticklabels(x_label)

    ax.grid(axis="both", linestyle="--")
    ax.bar(theta, radii, width=width, bottom=0.0, color=colors, alpha=0.5)

    plt.title("按月分布的微博字数", fontname="Microsoft YaHei", y=1.08)

    plt.box(False)
    plt.show()


def plot_polar_by_hour() -> None:
    weibo_list = load_weibo("weibo.jsonl")

    # 24 Hours
    N = 24
    width = 2 * np.pi * 0.8 / N
    theta = np.linspace(0.0, 2 * np.pi, N, endpoint=False, dtype=np.float64)

    words_count = [0] * N
    for weibo in weibo_list:
        if weibo[1].year == 2024:
            words_count[weibo[1].hour - 1] += len(weibo[0])

    radii = np.array(words_count, dtype=np.int32)

    colors = colormaps.get_cmap("viridis")(radii / max(radii))

    ax = plt.subplot(projection="polar")

    # direction
    ax.set_theta_direction(-1)  # type: ignore
    ax.set_theta_zero_location("N")  # type: ignore

    # xticks
    x = np.linspace(0.0, 2 * np.pi, N, endpoint=False, dtype=np.float64)
    x_label = list(map(str, range(0, N)))
    ax.set_xticks(x)
    ax.set_xticklabels(x_label)

    y = list(range(0, max(radii) + 1, 4000))
    y_label = list(map(str, y))
    ax.set_yticks(y)
    ax.set_yticklabels(y_label)

    ax.grid(axis="both", linestyle="--")
    ax.bar(theta, radii, width=width, bottom=0.0, color=colors, alpha=0.5)

    plt.title("按时段分布的微博字数", fontname="Microsoft YaHei", y=1.08)

    plt.box(False)
    plt.show()
