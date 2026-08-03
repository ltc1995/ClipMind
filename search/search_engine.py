# 搜索引擎模块

from typing import List
from database.db import Database
from database.models import ClipboardItem


class SearchEngine:
    """搜索功能封装"""

    def __init__(self, db: Database):
        self.db = db

    def search(self, keyword: str) -> List[ClipboardItem]:
        """搜索历史记录"""
        if not keyword or not keyword.strip():
            return self.db.get_recent(50)
        return self.db.search(keyword.strip())
