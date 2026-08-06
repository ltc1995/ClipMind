# 剪贴板管理模块

import os
import hashlib
import time
from PySide6.QtCore import QBuffer, QIODevice
from datetime import datetime
from typing import Optional
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage
from database.models import ClipboardItem
from database.db import Database
from utils.config import CODE_LANG_KEYWORDS, CONTENT_TYPE_TEXT, CONTENT_TYPE_CODE, CONTENT_TYPE_IMAGE, IMAGE_DIR

class ClipboardManager:
    # 截图工具框选/确认过程中可能向剪贴板写入多张尺寸相差 1-2px 的同一截图，
    # 在该时间窗口内做重叠区域像素比对去重
    _RECENT_IMAGE_WINDOW = 5.0
    _MAX_RECENT_IMAGES = 3
    _MAX_SIZE_DIFF = 2

    def __init__(self, db):
        self.db = db
        self._last_content = None
        self._last_image_hash = None
        self._recently_deleted = set()
        self._last_self_copy_key = None
        self._last_self_copy_at = 0.0
        self._recent_images = []  # [(monotonic_ts, QImage)] 最近保存的图片
        os.makedirs(IMAGE_DIR, exist_ok=True)

    def _get_clipboard(self):
        app = QApplication.instance()
        if app is None:
            return None
        return app.clipboard()

    @staticmethod
    def _strip_nulls(text: str) -> str:
        """Windows 剪贴板读写会在文本尾部附加 \x00，统一剥掉避免内容比对失败。"""
        return text.rstrip('\x00')

    @staticmethod
    def _image_fingerprint(image: QImage) -> str:
        """基于像素生成稳定指纹，避免同一张图因 PNG 重编码产生不同哈希。"""
        img = image.convertToFormat(QImage.Format.Format_RGBA8888)
        if img.isNull():
            return ""
        raw = bytes(img.constBits())
        return hashlib.md5(f"{img.width()}x{img.height()}:".encode() + raw).hexdigest()

    @staticmethod
    def _images_identical_overlap(a: QImage, b: QImage) -> bool:
        """两张图重叠区域是否像素完全一致（允许尺寸差 _MAX_SIZE_DIFF）。"""
        if a.isNull() or b.isNull():
            return False
        ra = a.convertToFormat(QImage.Format.Format_RGBA8888)
        rb = b.convertToFormat(QImage.Format.Format_RGBA8888)
        if abs(ra.width() - rb.width()) > ClipboardManager._MAX_SIZE_DIFF or \
                abs(ra.height() - rb.height()) > ClipboardManager._MAX_SIZE_DIFF:
            return False
        w = min(ra.width(), rb.width())
        h = min(ra.height(), rb.height())
        if w <= 0 or h <= 0:
            return False
        la, lb = ra.bytesPerLine(), rb.bytesPerLine()
        ba, bb = bytes(ra.constBits()), bytes(rb.constBits())
        row = w * 4
        for y in range(h):
            if ba[y * la: y * la + row] != bb[y * lb: y * lb + row]:
                return False
        return True

    def _is_duplicate_of_recent(self, image: QImage) -> bool:
        """与最近保存过的图片比较：重叠区域完全一致 → 视为同一次截图被重复写入剪贴板。"""
        now = time.monotonic()
        self._recent_images = [(ts, img) for ts, img in self._recent_images
                               if now - ts <= self._RECENT_IMAGE_WINDOW]
        for _, saved in self._recent_images:
            if self._images_identical_overlap(image, saved):
                return True
        return False

    def _note_recent_image(self, image: QImage):
        """记录刚保存的图片，用于短时间窗口内的相似去重。"""
        now = time.monotonic()
        self._recent_images.append((now, image))
        self._recent_images = [(ts, img) for ts, img in self._recent_images
                               if now - ts <= self._RECENT_IMAGE_WINDOW]
        if len(self._recent_images) > self._MAX_RECENT_IMAGES:
            self._recent_images = self._recent_images[-self._MAX_RECENT_IMAGES:]

    def _note_self_copy(self, key):
        self._last_self_copy_key = key
        self._last_self_copy_at = time.monotonic()

    def _is_recent_self_copy(self, key) -> bool:
        return (key is not None
                and key == self._last_self_copy_key
                and time.monotonic() - self._last_self_copy_at < 2.0)

    def mark_deleted(self, content):
        self._recently_deleted.add(content)
        if len(self._recently_deleted) > 200:
            self._recently_deleted.clear()

    def forget_deleted(self, content):
        self._recently_deleted.discard(content)

    def detect_type(self, text):
        for lang, keywords in CODE_LANG_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    return CONTENT_TYPE_CODE, lang
        return CONTENT_TYPE_TEXT, ""

    def check_and_save(self, force: bool = False):
        text_item = self._check_text(force=force)
        if text_item:
            return text_item
        return self._check_image(force=force)

    def _check_text(self, force: bool = False):
        try:
            clipboard = self._get_clipboard()
            if clipboard is None:
                return None
            if clipboard.mimeData().hasImage():
                return None
            current = self._strip_nulls(clipboard.text())
        except Exception:
            return None
        if not current:
            return None
        if not force and current == self._last_content:
            return None
        if self._is_recent_self_copy(current):
            self._last_content = current
            return None
        if current in self._recently_deleted:
            if force:
                # 用户再次主动复制了已删除的文本，允许重新入库
                self._recently_deleted.discard(current)
            else:
                self._last_content = current
                return None
        existing = self.db.find_by_content(current)
        if existing:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.db.update_timestamp(existing.id)
            existing.created_time = now
            existing.updated_time = now
            self._last_content = current
            return existing
        self._last_content = current
        content_type, language = self.detect_type(current)
        item = ClipboardItem(content=current, content_type=content_type, language=language)
        item_id = self.db.add_item(item)
        item.id = item_id
        return item

    def _check_image(self, force: bool = False):
        try:
            clipboard = self._get_clipboard()
            if clipboard is None:
                return None
            mime_data = clipboard.mimeData()
            if not mime_data.hasImage():
                return None
            image = clipboard.image()
            if image.isNull():
                return None
            image_hash = self._image_fingerprint(image)
            if not image_hash:
                return None
            if image_hash == self._last_image_hash:
                return None
            self._last_image_hash = image_hash
            if image_hash in self._recently_deleted:
                return None
            existing = self.db.find_by_content(image_hash)
            if existing:
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.db.update_timestamp(existing.id)
                existing.created_time = now
                existing.updated_time = now
                return existing
            if self._is_duplicate_of_recent(image):
                # 与刚保存过的图片重叠区域一致（截图工具的重复写入），丢弃
                return None
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{image_hash[:8]}.png"
            filepath = os.path.join(IMAGE_DIR, filename)
            # Save image in original format from clipboard
            img_to_save = clipboard.image()
            if img_to_save.isNull() or not img_to_save.save(filepath, "PNG"):
                return None
            item = ClipboardItem(content=image_hash, content_type=CONTENT_TYPE_IMAGE,
                                 image_path=filepath)
            item_id = self.db.add_item(item)
            item.id = item_id
            self._note_recent_image(image)
            return item
        except Exception as e:
            print(f"Image capture error: {e}")
            return None

    def copy_to_clipboard(self, item):
        try:
            if item.content_type == CONTENT_TYPE_IMAGE:
                self._copy_image_to_clipboard(item)
                return
            clipboard = self._get_clipboard()
            if clipboard is None:
                return
            clipboard.setText(item.content)
            pasted = self._strip_nulls(clipboard.text()) or item.content
            self._last_content = pasted
            self._recently_deleted.discard(pasted)
            self._note_self_copy(pasted)
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.db.update_timestamp(item.id)
            item.created_time = now
            item.updated_time = now
        except Exception as e:
            print(f"clipboard copy failed: {e}")

    def _copy_image_to_clipboard(self, item):
        if not item.image_path or not os.path.exists(item.image_path):
            return
        try:
            image = QImage(item.image_path)
            if image.isNull():
                return
            app = QApplication.instance()
            if app:
                app.clipboard().setImage(image)
                re_read = app.clipboard().image()
                if not re_read.isNull():
                    computed = self._image_fingerprint(re_read)
                    if computed:
                        self._last_image_hash = computed
                        self._recently_deleted.add(computed)
                        self._note_self_copy(computed)
                        if len(self._recently_deleted) > 200:
                            self._recently_deleted.clear()
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.db.update_timestamp(item.id)
                    item.created_time = now
                    item.updated_time = now
        except Exception as e:
            print(f"copy image to clipboard failed: {e}")
