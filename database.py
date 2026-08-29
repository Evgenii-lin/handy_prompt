"""Centralized database operations for prompt storage."""
import sqlite3
from typing import Optional

from config import DB_NAME


class PromptDatabase:
    """Manages all SQLite operations for the prompts table."""

    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self._init_db()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def _init_db(self) -> None:
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_name TEXT NOT NULL UNIQUE,
                content TEXT
            )
        """)
        self.conn.commit()

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def insert_prompt(self, prompt_name: str, content: str) -> bool:
        try:
            self.cursor.execute(
                "INSERT INTO prompts (prompt_name, content) VALUES (?, ?)",
                (prompt_name, content),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        except sqlite3.Error:
            raise

    def update_prompt(self, old_name: str, new_name: str, content: str) -> bool:
        try:
            self.cursor.execute(
                "UPDATE prompts SET prompt_name = ?, content = ? WHERE prompt_name = ?",
                (new_name, content, old_name),
            )
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error:
            raise

    def delete_prompt(self, prompt_name: str) -> bool:
        try:
            self.cursor.execute(
                "DELETE FROM prompts WHERE prompt_name = ?", (prompt_name,)
            )
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error:
            raise

    def get_prompt(self, prompt_name: str) -> Optional[tuple[str, Optional[str]]]:
        self.cursor.execute(
            "SELECT prompt_name, content FROM prompts WHERE prompt_name = ?",
            (prompt_name,),
        )
        return self.cursor.fetchone()

    def get_all_prompt_names(self) -> list[str]:
        self.cursor.execute("SELECT prompt_name FROM prompts ORDER BY prompt_name")
        return [row[0] for row in self.fetchall()]

    def get_content(self, prompt_name: str) -> Optional[str]:
        self.cursor.execute(
            "SELECT content FROM prompts WHERE prompt_name = ?", (prompt_name,)
        )
        row = self.cursor.fetchone()
        return row[0] if row else None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def fetchall(self):
        return self.cursor.fetchall()

    def exists(self, prompt_name: str) -> bool:
        self.cursor.execute(
            "SELECT 1 FROM prompts WHERE prompt_name = ?", (prompt_name,)
        )
        return self.cursor.fetchone() is not None
