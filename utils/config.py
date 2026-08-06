# ClipMind 配置模块

import os
import sys
from pathlib import Path


# 应用信息
APP_NAME = 'ClipMind'
APP_VERSION = '1.0.3'
APP_DESCRIPTION = '\u667a\u80fd\u526a\u8d34\u677f\u52a9\u624b'
APP_AUTHOR = 'ClipMind'

# 更新检查地址：自定义 JSON 清单或 GitHub Releases API，留空则不启用
UPDATE_CHECK_URL = ''


def get_app_dir() -> Path:
    """获取应用数据目录"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent / 'data'
    else:
        return Path(__file__).resolve().parent.parent / 'data'


# 数据库
DB_DIR = get_app_dir()
DB_NAME = 'clipmind.db'
DB_PATH = DB_DIR / DB_NAME

# 剪贴板轮询间隔（秒）
CLIPBOARD_POLL_INTERVAL = 0.5

# 窗口
WINDOW_TITLE = f'{APP_NAME} - {APP_DESCRIPTION}'
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 500

# 快捷键
HOTKEY = 'ctrl+shift+v'

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004

# 预览截断长度
PREVIEW_MAX_LENGTH = 100

# 内容类型
CONTENT_TYPE_TEXT = 'text'
CONTENT_TYPE_CODE = 'code'
CONTENT_TYPE_IMAGE = 'image'

# 图片存储目录
IMAGE_DIR = get_app_dir() / 'images'

# 常见代码语言关键词
CODE_LANG_KEYWORDS = {
    'python': ['def ', 'import ', 'class ', 'if __name__', 'print(', 'lambda '],
    'javascript': ['function ', 'const ', 'let ', 'var ', '=>', 'console.log'],
    'typescript': [': string', ': number', ': boolean', 'interface ', 'type '],
    'java': ['public class', 'private ', 'System.out', 'import java'],
    'go': ['func ', 'package ', 'import (', 'defer '],
    'rust': ['fn ', 'let mut', 'impl ', 'pub '],
    'cpp': ['#include', 'int main', 'std::', 'using namespace'],
    'csharp': ['using System', 'namespace ', 'class ', 'static void'],
    'sql': ['SELECT ', 'FROM ', 'WHERE ', 'INSERT INTO', 'CREATE TABLE'],
    'shell': ['#!/bin', 'echo ', 'export ', 'chmod '],
    'yaml': ['---', 'apiVersion:', 'kind:', 'metadata:'],
    'json': ['{', '}', '"key"', '"value"'],
    'html': ['<!DOCTYPE', '<html', '<div', '<body', '<head'],
    'css': [': {', 'margin:', 'padding:', 'display:'],
}
