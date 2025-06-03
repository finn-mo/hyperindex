from datetime import datetime, timezone
from typing import Iterable

from pywebcopy import save_webpage
from waybackpy import WaybackMachineSaveAPI

from client.core.config import Config


def archive_with_pywebcopy(url: str) -> dict[str, str]:
    """Save a local snapshot of the webpage using pywebcopy"""
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    folder = f"{timestamp}_{url.replace('https://', '').replace('http://', '').replace('/', '_')}"
    save_path = Config.SNAPSHOT_DIR / folder
    save_path.mkdir(parents=True, exist_ok=True)
    try:
        save_webpage(
            url=url,
            project_folder=str(save_path),
            open_in_browser=False,
            delay=1,
            threaded=True
        )
    except Exception as e:
        raise RuntimeError(f"pywebcopy failed: {e}")

    return {"snapshot_dir": str(save_path)}


def archive_with_wayback(url: str) -> dict[str, str]:
    """Save a remote archive using the Wayback Machine"""
    try:
        archive = WaybackMachineSaveAPI(url).save()
        return {"archived_url": archive.archive_url}
    except Exception as e:
        raise RuntimeError(f"waybackpy failed: {e}")


def archive_none(url: str) -> dict[str, str]:
    """No-op fallback archiver"""
    return {"archived_url": "", "snapshot_dir": ""}


def archive_url(url: str, strategies: Iterable[str]) -> dict[str, str]:
    """Archive a URL using one or more given strategies"""
    strategies = {s.strip().lower() for s in strategies}
    if not strategies:
        raise RuntimeError("No archiving strategy provided.")
    if not strategies.issubset(Config.ALLOWED_STRATEGIES):
        invalid = strategies - Config.ALLOWED_STRATEGIES
        raise RuntimeError(
            f"Invalid archiving strategies: {', '.join(invalid)}. "
            f"Allowed: {', '.join(Config.ALLOWED_STRATEGIES)}"
        )
    if "none" in strategies and len(strategies) > 1:
        raise RuntimeError("'none' cannot be combined with other archiving strategies.")
    if "none" in strategies:
        return archive_none(url)

    result = {}
    if "pywebcopy" in strategies:
        result.update(archive_with_pywebcopy(url))
    if "wayback" in strategies:
        result.update(archive_with_wayback(url))
    return result