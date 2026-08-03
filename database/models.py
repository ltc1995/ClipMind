# 数据模型

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ClipboardItem:
    """剪贴板记录数据模型"""
    id: Optional[int] = None
    content: str = ''
    content_type: str = 'text'  # text, code, image
    language: str = ''           # 代码语言
    tags: str = ''               # 逗号分隔
    is_favorite: int = 0         # 0=否, 1=是
    image_path: str = ''         # 图片保存路径
    created_time: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    updated_time: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def preview(self, max_length: int = 100) -> str:
        """获取内容预览"""
        text = self.content.replace('\r\n', ' ').replace('\n', ' ')
        if len(text) > max_length:
            return text[:max_length] + '...'
        return text

    def tag_list(self) -> list:
        """获取标签列表"""
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]
