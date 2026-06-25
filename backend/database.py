import os
import json
import sqlite3
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

class DatabaseRepository(ABC):
    @abstractmethod
    def save_post(self, post: Dict[str, Any]) -> bool:
        """Saves a single product post. Returns True if saved, False if it already exists."""
        pass

    @abstractmethod
    def save_posts(self, posts: List[Dict[str, Any]]) -> int:
        """Saves multiple product posts. Returns count of newly saved posts."""
        pass

    @abstractmethod
    def get_latest_posts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns the latest posts, sorted by scraping date/time."""
        pass

    @abstractmethod
    def is_product_exists(self, product_id: str) -> bool:
        """Checks if a product is already in the database by its product ID."""
        pass

    @abstractmethod
    def clear_posts(self) -> None:
        """Clears all posts from the repository."""
        pass


class JsonDatabaseRepository(DatabaseRepository):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        dir_name = os.path.dirname(self.file_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def _read_all(self) -> List[Dict[str, Any]]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _write_all(self, data: List[Dict[str, Any]]):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_post(self, post: Dict[str, Any]) -> bool:
        posts = self._read_all()
        if any(p.get("product_id") == post.get("product_id") for p in posts):
            return False
        
        # Ensure timestamp exists
        if "created_at" not in post or not post["created_at"]:
            post["created_at"] = datetime.now().isoformat()
            
        posts.append(post)
        # Sort by created_at descending
        posts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        self._write_all(posts)
        return True

    def save_posts(self, posts: List[Dict[str, Any]]) -> int:
        existing_posts = self._read_all()
        existing_ids = {p.get("product_id") for p in existing_posts}
        
        new_count = 0
        now_str = datetime.now().isoformat()
        
        for post in posts:
            if post.get("product_id") not in existing_ids:
                if "created_at" not in post or not post["created_at"]:
                    post["created_at"] = now_str
                existing_posts.append(post)
                existing_ids.add(post.get("product_id"))
                new_count += 1
                
        if new_count > 0:
            existing_posts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            self._write_all(existing_posts)
            
        return new_count

    def get_latest_posts(self, limit: int = 10) -> List[Dict[str, Any]]:
        posts = self._read_all()
        # Ensure they are sorted by created_at desc
        posts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return posts[:limit]

    def is_product_exists(self, product_id: str) -> bool:
        posts = self._read_all()
        return any(p.get("product_id") == product_id for p in posts)

    def clear_posts(self) -> None:
        self._write_all([])


class SqliteDatabaseRepository(DatabaseRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_db_exists()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_db_exists(self):
        dir_name = os.path.dirname(self.db_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
            
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                price REAL,
                currency TEXT,
                image_url TEXT,
                product_url TEXT,
                rating REAL,
                reviews_count INTEGER,
                keyword TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def save_post(self, post: Dict[str, Any]) -> bool:
        if self.is_product_exists(post.get("product_id")):
            return False
            
        created_at = post.get("created_at") or datetime.now().isoformat()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO posts (product_id, title, description, price, currency, image_url, product_url, rating, reviews_count, keyword, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                post.get("product_id"),
                post.get("title"),
                post.get("description", ""),
                post.get("price"),
                post.get("currency", "USD"),
                post.get("image_url", ""),
                post.get("product_url", ""),
                post.get("rating"),
                post.get("reviews_count", 0),
                post.get("keyword", ""),
                created_at
            ))
            conn.commit()
            success = True
        except sqlite3.IntegrityError:
            success = False
        finally:
            conn.close()
        return success

    def save_posts(self, posts: List[Dict[str, Any]]) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        new_count = 0
        now_str = datetime.now().isoformat()
        
        for post in posts:
            product_id = post.get("product_id")
            # Inline check to optimize
            cursor.execute("SELECT 1 FROM posts WHERE product_id = ?", (product_id,))
            if cursor.fetchone():
                continue
                
            created_at = post.get("created_at") or now_str
            try:
                cursor.execute("""
                    INSERT INTO posts (product_id, title, description, price, currency, image_url, product_url, rating, reviews_count, keyword, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product_id,
                    post.get("title"),
                    post.get("description", ""),
                    post.get("price"),
                    post.get("currency", "USD"),
                    post.get("image_url", ""),
                    post.get("product_url", ""),
                    post.get("rating"),
                    post.get("reviews_count", 0),
                    post.get("keyword", ""),
                    created_at
                ))
                new_count += 1
            except sqlite3.IntegrityError:
                pass
        
        conn.commit()
        conn.close()
        return new_count

    def get_latest_posts(self, limit: int = 10) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT product_id, title, description, price, currency, image_url, product_url, rating, reviews_count, keyword, created_at
            FROM posts
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        posts = []
        for row in rows:
            posts.append({
                "product_id": row["product_id"],
                "title": row["title"],
                "description": row["description"],
                "price": row["price"],
                "currency": row["currency"],
                "image_url": row["image_url"],
                "product_url": row["product_url"],
                "rating": row["rating"],
                "reviews_count": row["reviews_count"],
                "keyword": row["keyword"],
                "created_at": row["created_at"]
            })
        conn.close()
        return posts

    def is_product_exists(self, product_id: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM posts WHERE product_id = ?", (product_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def clear_posts(self) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM posts")
        conn.commit()
        conn.close()


def get_db_repository() -> DatabaseRepository:
    from backend.config_loader import load_properties
    config = load_properties()
    db_type = config.get("database.type", "json")
    if db_type == "sqlite":
        db_path = config.get("sqlite.path", "data/posts.db")
        return SqliteDatabaseRepository(db_path)
    else:
        file_path = config.get("database.path", "data/posts.json")
        return JsonDatabaseRepository(file_path)

