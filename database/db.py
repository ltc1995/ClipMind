import sqlite3
import os
from typing import List, Optional
from database.models import ClipboardItem
from utils.config import DB_PATH, DB_DIR
class Database:
    def __init__(self):
        self._ensure_dir()
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
    def _ensure_dir(self):
        os.makedirs(DB_DIR, exist_ok=True)
    def _init_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS clipboard_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            content_type TEXT NOT NULL DEFAULT 'text',
            language TEXT DEFAULT '',
            tags TEXT DEFAULT '',
            is_favorite INTEGER DEFAULT 0,
            image_path TEXT DEFAULT '',
            created_time TEXT NOT NULL,
            updated_time TEXT NOT NULL)""")
        cursor.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS clipboard_fts
            USING fts5(content, tags, content='clipboard_items', content_rowid='id')""")
        cursor.execute("""CREATE TRIGGER IF NOT EXISTS clipboard_ai AFTER INSERT ON clipboard_items
            BEGIN INSERT INTO clipboard_fts(rowid, content, tags) VALUES (new.id, new.content, new.tags); END""")
        cursor.execute("""CREATE TRIGGER IF NOT EXISTS clipboard_ad AFTER DELETE ON clipboard_items
            BEGIN INSERT INTO clipboard_fts(clipboard_fts, rowid, content, tags) VALUES ('delete', old.id, old.content, old.tags); END""")
        cursor.execute("""CREATE TRIGGER IF NOT EXISTS clipboard_au AFTER UPDATE ON clipboard_items
            BEGIN
                INSERT INTO clipboard_fts(clipboard_fts, rowid, content, tags) VALUES ('delete', old.id, old.content, old.tags);
                INSERT INTO clipboard_fts(rowid, content, tags) VALUES (new.id, new.content, new.tags);
            END""")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_time ON clipboard_items(created_time DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_type ON clipboard_items(content_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_content ON clipboard_items(content)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_content_unique ON clipboard_items(content)")
        self.conn.commit()
    def add_item(self, item: 'ClipboardItem') -> int:
        cursor = self.conn.cursor()
        item.content = item.content.rstrip('\x00')
        cursor.execute("INSERT OR IGNORE INTO clipboard_items(content,content_type,language,tags,is_favorite,image_path,created_time,updated_time) VALUES(?,?,?,?,?,?,?,?)",
            (item.content, item.content_type, item.language, item.tags, item.is_favorite, item.image_path, item.created_time, item.updated_time))
        self.conn.commit()
        return cursor.lastrowid
    def get_recent(self, limit: int = 50) -> List:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM clipboard_items ORDER BY created_time DESC LIMIT ?", (limit,))
        return [self._row_to_item(row) for row in cursor.fetchall()]
    def search(self, keyword: str, limit: int = 50) -> List:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM clipboard_items WHERE content LIKE ? OR tags LIKE ? ORDER BY created_time DESC LIMIT ?",
            (f"%{keyword}%", f"%{keyword}%", limit))
        return [self._row_to_item(row) for row in cursor.fetchall()]
    def get_by_id(self, item_id: int):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM clipboard_items WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        return self._row_to_item(row) if row else None
    def update_tags(self, item_id: int, tags: str):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE clipboard_items SET tags = ?, updated_time = datetime('now','localtime') WHERE id = ?", (tags, item_id))
        self.conn.commit()
    def toggle_favorite(self, item_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("SELECT is_favorite FROM clipboard_items WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        if not row: return False
        new_val = 0 if row["is_favorite"] else 1
        cursor.execute("UPDATE clipboard_items SET is_favorite = ?, updated_time = datetime('now','localtime') WHERE id = ?", (new_val, item_id))
        self.conn.commit()
        return bool(new_val)
    def delete_item(self, item_id: int):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM clipboard_items WHERE id = ?", (item_id,))
        self.conn.commit()
    def close(self):
        self.conn.close()
    def count_items(self) -> int:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM clipboard_items")
        row = cursor.fetchone()
        return row[0] if row else 0
    def clear_all(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM clipboard_items")
        cursor.execute("DELETE FROM clipboard_fts")
        self.conn.commit()
    @staticmethod
    def _row_to_item(row) -> 'ClipboardItem':
        return ClipboardItem(
            id=row["id"], content=row["content"], content_type=row["content_type"],
            language=row["language"] or "", tags=row["tags"] or "",
            is_favorite=row["is_favorite"], image_path=row["image_path"] or "",
            created_time=row["created_time"], updated_time=row["updated_time"])
    def find_by_content(self, content: str):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM clipboard_items WHERE content = ? ORDER BY created_time DESC LIMIT 1", (content.rstrip('\x00'),))
        row = cursor.fetchone()
        return self._row_to_item(row) if row else None
    def update_timestamp(self, item_id: int):
        from datetime import datetime
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor = self.conn.cursor()
        cursor.execute("UPDATE clipboard_items SET created_time = ?, updated_time = ? WHERE id = ?", (now, now, item_id))
        self.conn.commit()
