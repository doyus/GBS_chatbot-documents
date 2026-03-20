import sqlite3
import hashlib
import secrets
from datetime import datetime
from typing import Optional, Dict, Any
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "users.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


def hash_password(password: str, salt: Optional[str] = None) -> tuple:
    if salt is None:
        salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return password_hash, salt


def create_user(username: str, email: str, password: str) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        password_hash, salt = hash_password(password)
        
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, salt) VALUES (?, ?, ?, ?)",
            (username, email, password_hash, salt)
        )
        conn.commit()
        
        user_id = cursor.lastrowid
        return {
            "success": True,
            "user_id": user_id,
            "username": username,
            "email": email,
            "message": "User created successfully"
        }
    except sqlite3.IntegrityError as e:
        if "username" in str(e).lower():
            return {"success": False, "message": "Username already exists"}
        elif "email" in str(e).lower():
            return {"success": False, "message": "Email already exists"}
        return {"success": False, "message": "User already exists"}
    finally:
        conn.close()


def verify_user(username_or_email: str, password: str) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?",
        (username_or_email, username_or_email)
    )
    user = cursor.fetchone()
    
    if user is None:
        conn.close()
        return {"success": False, "message": "User not found"}
    
    user_dict = dict(user)
    password_hash, _ = hash_password(password, user_dict["salt"])
    
    if password_hash == user_dict["password_hash"]:
        cursor.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.now().isoformat(), user_dict["id"])
        )
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "user_id": user_dict["id"],
            "username": user_dict["username"],
            "email": user_dict["email"],
            "message": "Login successful"
        }
    else:
        conn.close()
        return {"success": False, "message": "Invalid password"}


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username, email, created_at, last_login FROM users WHERE id = ?",
        (user_id,)
    )
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return dict(user)
    return None


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username, email, created_at, last_login FROM users WHERE username = ?",
        (username,)
    )
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return dict(user)
    return None


init_db()
