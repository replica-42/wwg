"""Configure the external model and cache locations used by segmentation."""

import os
from pathlib import Path

DATA_DIR = Path.cwd() / "data"


def configure_data_paths(data_dir: Path | None = None) -> None:
    """Set homes before importing backends, which cache paths at import time."""
    global DATA_DIR
    if data_dir is not None:
        DATA_DIR = data_dir.resolve()
    os.environ["HANLP_HOME"] = str(DATA_DIR / "hanlp")
    os.environ["PKUSEG_HOME"] = str(DATA_DIR / "pkuseg")
