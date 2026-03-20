import sqlite3
from sqlite3 import Connection
from typing import Optional, Dict, Any
import hashlib
import os

DATABASE_PATH = "app.db"

def get_connection() -> Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + key.hex()

def verify_password(stored_password: str, provided_password: str) -> bool:
    salt = bytes.fromhex(stored_password[:64])
    stored_key = stored_password[64:]
    key = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    return key.hex() == stored_key

def create_user(username: str, email: str, password: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    
    hashed_pw = hash_password(password)
    
    try:
        cursor.execute('''
            INSERT INTO users (username, email, hashed_password)
            VALUES (?, ?, ?)
        ''', (username, email, hashed_pw))
        
        conn.commit()
        user_id = cursor.lastrowid
        
        cursor.execute('SELECT id, username, email, is_active, created_at FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        conn.close()
        return dict(user) if user else None
    except sqlite3.IntegrityError:
        conn.close()
        return None

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, username, email, hashed_password, is_active, created_at FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    
    conn.close()
    return dict(user) if user else None

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, username, email, hashed_password, is_active, created_at FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    
    conn.close()
    return dict(user) if user else None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, username, email, is_active, created_at FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    conn.close()
    return dict(user) if user else None

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_username(username)
    if not user:
        return None
    if not verify_password(user['hashed_password'], password):
        return None
    return user
