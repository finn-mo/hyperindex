import os
from pathlib import Path


class Config:
    APP_NAME = "hyperindex"
    BASE_DIR = Path(os.getenv("HYPERINDEX_HOME", Path.home() / f".{APP_NAME}"))
    DB_PATH = BASE_DIR / "rolodex.db"
    SNAPSHOT_DIR = BASE_DIR / "snapshots"
    EXPORT_DIR = BASE_DIR / "exports"

    ALLOWED_STRATEGIES = {"none", "pywebcopy", "wayback"}

    @classmethod
    def init_paths(cls):
        cls.BASE_DIR.mkdir(parents=True, exist_ok=True)
        cls.SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        cls.EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def set_test_config(cls, test_base_dir: Path):
        cls.BASE_DIR = test_base_dir
        cls.DB_PATH = cls.BASE_DIR / "rolodex-test.db"
        cls.SNAPSHOT_DIR = cls.BASE_DIR / "snapshots"
        cls.EXPORT_DIR = cls.BASE_DIR / "exports"
        cls.init_paths()