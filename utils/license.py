"""ClipMind 许可证与功能开关模块。

当前 MVP 免费版开放核心剪贴板功能；Pro 功能（AI 总结、OCR 等）
由许可证开关控制。V2 接入激活码/许可证后，只需替换 _is_licensed 的实现。
"""

# 免费功能（MVP 永久开放）
FREE_FEATURES = {
    "clipboard_history": "剪贴板历史记录",
    "search": "全文搜索",
    "tags": "标签管理",
    "favorites": "收藏",
}

# Pro 功能（V2 收费版）
PRO_FEATURES = {
    "ai_summary": "AI 智能总结",
    "ocr": "OCR 图片文字识别",
    "ai_search": "AI 智能搜索",
    "cloud_sync": "云端同步",
}


def is_feature_enabled(feature: str) -> bool:
    """判断功能是否对当前版本开放。"""
    if feature in FREE_FEATURES:
        return True
    if feature in PRO_FEATURES:
        return _is_licensed()
    return False


def get_edition() -> str:
    """返回当前版本标识，用于界面展示。"""
    return "Pro" if _is_licensed() else "Free"


def _is_licensed() -> bool:
    """V2 接入激活码/许可证后，在此读取并验证本地许可证。"""
    return False
