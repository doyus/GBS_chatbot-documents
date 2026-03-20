import sqlite3
import os
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "users.db")

def get_db_path():
    db_dir = os.path.dirname(DATABASE_PATH)
    os.makedirs(db_dir, exist_ok=True)
    return DATABASE_PATH

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

def create_user(username: str, email: str, hashed_password: str) -> Optional[int]:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, email, hashed_password)
                VALUES (?, ?, ?)
            ''', (username, email, hashed_password))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None

def get_user_by_username(username: str) -> Optional[dict]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_user_by_email(email: str) -> Optional[dict]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_user_by_id(user_id: int) -> Optional[dict]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_user(user_id: int, **kwargs) -> bool:
    valid_fields = {'username', 'email', 'hashed_password', 'is_active'}
    update_fields = {k: v for k, v in kwargs.items() if k in valid_fields}
    
    if not update_fields:
        return False
    
    update_fields['updated_at'] = datetime.now().isoformat()
    
    set_clause = ', '.join([f'{k} = ?' for k in update_fields.keys()])
    values = list(update_fields.values()) + [user_id]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f'UPDATE users SET {set_clause} WHERE id = ?', values)
        conn.commit()
        return cursor.rowcount > 0

init_db()
