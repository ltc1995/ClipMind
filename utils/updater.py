"""ClipMind 更新检查模块。

更新清单支持两种格式：
1. 自定义 JSON：{"version": "1.0.1", "url": "https://...", "notes": "更新说明"}
2. GitHub Releases API：https://api.github.com/repos/{owner}/{repo}/releases/latest
"""

import json
import urllib.request

from utils.config import APP_VERSION, UPDATE_CHECK_URL

REQUEST_TIMEOUT = 10
USER_AGENT = f"ClipMind/{APP_VERSION}"


def parse_version(version: str) -> tuple:
    """将 'v1.2.3' 解析为可比较的整数元组 (1, 2, 3)。"""
    parts = []
    for part in str(version).strip().lstrip("vV").split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def is_newer(candidate: str, current: str) -> bool:
    """判断 candidate 是否比 current 版本更新。"""
    return parse_version(candidate) > parse_version(current)


def normalize_update_info(data: dict) -> dict:
    """兼容自定义 JSON 与 GitHub Releases API 两种响应结构。"""
    version = data.get("version") or data.get("tag_name") or ""
    download_url = data.get("url") or data.get("html_url") or ""
    for asset in data.get("assets") or []:
        if isinstance(asset, dict) and asset.get("browser_download_url"):
            download_url = asset["browser_download_url"]
            break
    return {
        "version": str(version).lstrip("vV"),
        "url": download_url,
        "notes": data.get("notes") or data.get("body") or "",
    }


def fetch_latest_info(update_url: str) -> dict:
    """请求更新清单并返回规范化后的字典。"""
    if not update_url:
        return {}
    req = urllib.request.Request(update_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return normalize_update_info(data)


def check_for_update(current_version: str = APP_VERSION, update_url: str = None):
    """检查是否有新版本。

    返回 (has_update, latest_version, download_url, notes, error)。
    """
    url = update_url if update_url is not None else UPDATE_CHECK_URL
    try:
        info = fetch_latest_info(url)
    except Exception as exc:
        return False, current_version, "", "", f"无法连接更新服务器：{exc}"
    if not info.get("version"):
        return False, current_version, "", "", ""
    if is_newer(info["version"], current_version):
        return True, info["version"], info["url"], info["notes"], ""
    return False, current_version, "", "", ""
