
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
from core.rag_pipeline import DocumentQA
from core.auth import hash_password, verify_password, create_access_token, verify_token
from core.database import create_user, get_user_by_username, get_user_by_email, get_user_by_id
import os
import shutil

app = FastAPI()
qa_system = None
security = HTTPBearer(auto_error=False)

def get_qa_system():
    global qa_system
    if qa_system is None:
        qa_system = DocumentQA()
    return qa_system

# Permitir acceso desde frontend (Streamlit, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
async def root():
    return {
        "message": "Welcome to RAG Chatbot Documents API",
        "endpoints": {
            "upload": "/upload/ - Upload a PDF document",
            "ask": "/ask/ - Ask a question about uploaded documents",
            "docs": "/docs - Interactive API documentation"
        }
    }

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    qa = get_qa_system()
    qa.load_and_index_pdf(file_path)
    return {"message": "Document loaded and processed", "file": file.filename}

@app.post("/ask/")
async def ask_question(question: str = Form(...)):
    qa = get_qa_system()
    if not qa.qa_chain:
        index_loaded = qa.load_existing_index()
        if not index_loaded:
            return {"error": "No index loaded. Please upload a document first."}

    answer = qa.ask(question)
    return {"question": question, "answer": answer}

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserInfo(BaseModel):
    id: int
    username: str
    email: str

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

@app.post("/auth/register", response_model=dict)
async def register(user: UserRegister):
    existing_user = get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    existing_email = get_user_by_email(user.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = hash_password(user.password)
    user_id = create_user(user.username, user.email, hashed_pwd)
    
    if user_id is None:
        raise HTTPException(status_code=500, detail="Failed to create user")
    
    access_token = create_access_token(user_id, user.username)
    
    return {
        "message": "User registered successfully",
        "user_id": user_id,
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.post("/auth/login", response_model=Token)
async def login(user: UserLogin):
    db_user = get_user_by_username(user.username)
    if db_user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    access_token = create_access_token(db_user["id"], db_user["username"])
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=UserInfo)
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"]
    }

@app.get("/auth/verify")
async def verify_auth(current_user: dict = Depends(get_current_user)):
    return {"authenticated": True, "username": current_user["username"]}

@app.get("/auth/page", response_class=HTMLResponse)
async def auth_page():
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>用户认证</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }
        .container { background: white; border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); max-width: 400px; width: 100%; overflow: hidden; }
        .tabs { display: flex; }
        .tab { flex: 1; padding: 16px; text-align: center; cursor: pointer; background: #f5f5f5; border: none; font-size: 16px; font-weight: 500; transition: all 0.3s; }
        .tab.active { background: white; color: #667eea; }
        .tab:hover { background: #e8e8e8; }
        .form-container { padding: 30px; }
        .form { display: none; }
        .form.active { display: block; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; font-weight: 500; color: #333; }
        .form-group input { width: 100%; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 16px; transition: border-color 0.3s; }
        .form-group input:focus { outline: none; border-color: #667eea; }
        .btn { width: 100%; padding: 14px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4); }
        .btn:disabled { opacity: 0.7; cursor: not-allowed; transform: none; }
        .message { margin-top: 15px; padding: 12px; border-radius: 8px; text-align: center; display: none; }
        .message.success { background: #d4edda; color: #155724; display: block; }
        .message.error { background: #f8d7da; color: #721c24; display: block; }
        .user-info { display: none; text-align: center; padding: 30px; }
        .user-info.active { display: block; }
        .user-info h2 { color: #333; margin-bottom: 20px; }
        .user-info p { color: #666; margin-bottom: 10px; }
        .logout-btn { background: #dc3545; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="tabs">
            <button class="tab active" onclick="showTab('login')">登录</button>
            <button class="tab" onclick="showTab('register')">注册</button>
        </div>
        <div class="form-container">
            <div id="login-form" class="form active">
                <div class="form-group">
                    <label>用户名</label>
                    <input type="text" id="login-username" placeholder="请输入用户名">
                </div>
                <div class="form-group">
                    <label>密码</label>
                    <input type="password" id="login-password" placeholder="请输入密码">
                </div>
                <button class="btn" onclick="login()">登录</button>
                <div id="login-message" class="message"></div>
            </div>
            <div id="register-form" class="form">
                <div class="form-group">
                    <label>用户名</label>
                    <input type="text" id="reg-username" placeholder="请输入用户名">
                </div>
                <div class="form-group">
                    <label>邮箱</label>
                    <input type="email" id="reg-email" placeholder="请输入邮箱">
                </div>
                <div class="form-group">
                    <label>密码</label>
                    <input type="password" id="reg-password" placeholder="请输入密码">
                </div>
                <button class="btn" onclick="register()">注册</button>
                <div id="register-message" class="message"></div>
            </div>
            <div id="user-info" class="user-info">
                <h2>欢迎回来!</h2>
                <p id="user-name"></p>
                <p id="user-email"></p>
                <button class="btn logout-btn" onclick="logout()">退出登录</button>
            </div>
        </div>
    </div>
    <script>
        const API_BASE = window.location.origin;
        let token = localStorage.getItem('token');
        
        function showTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.form').forEach(f => f.classList.remove('active'));
            document.querySelector(`.tab:nth-child(${tab === 'login' ? 1 : 2})`).classList.add('active');
            document.getElementById(`${tab}-form`).classList.add('active');
        }
        
        function showMessage(elementId, message, isSuccess) {
            const el = document.getElementById(elementId);
            el.textContent = message;
            el.className = 'message ' + (isSuccess ? 'success' : 'error');
        }
        
        function showUserInfo(username, email) {
            document.querySelectorAll('.form').forEach(f => f.style.display = 'none');
            document.querySelectorAll('.tab').forEach(t => t.style.display = 'none');
            document.getElementById('user-info').classList.add('active');
            document.getElementById('user-name').textContent = '用户名: ' + username;
            document.getElementById('user-email').textContent = '邮箱: ' + email;
        }
        
        function showAuthForms() {
            document.querySelectorAll('.form').forEach(f => f.style.display = '');
            document.querySelectorAll('.tab').forEach(t => t.style.display = '');
            document.getElementById('user-info').classList.remove('active');
        }
        
        async function checkAuth() {
            if (!token) return;
            try {
                const res = await fetch(API_BASE + '/auth/me', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                if (res.ok) {
                    const data = await res.json();
                    showUserInfo(data.username, data.email);
                } else {
                    localStorage.removeItem('token');
                    token = null;
                }
            } catch (e) {
                console.error('Auth check failed:', e);
            }
        }
        
        async function register() {
            const username = document.getElementById('reg-username').value;
            const email = document.getElementById('reg-email').value;
            const password = document.getElementById('reg-password').value;
            
            if (!username || !email || !password) {
                showMessage('register-message', '请填写所有字段', false);
                return;
            }
            
            try {
                const res = await fetch(API_BASE + '/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email, password })
                });
                const data = await res.json();
                
                if (res.ok) {
                    token = data.access_token;
                    localStorage.setItem('token', token);
                    showMessage('register-message', '注册成功!', true);
                    setTimeout(() => checkAuth(), 500);
                } else {
                    showMessage('register-message', data.detail || '注册失败', false);
                }
            } catch (e) {
                showMessage('register-message', '网络错误', false);
            }
        }
        
        async function login() {
            const username = document.getElementById('login-username').value;
            const password = document.getElementById('login-password').value;
            
            if (!username || !password) {
                showMessage('login-message', '请填写所有字段', false);
                return;
            }
            
            try {
                const res = await fetch(API_BASE + '/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                const data = await res.json();
                
                if (res.ok) {
                    token = data.access_token;
                    localStorage.setItem('token', token);
                    showMessage('login-message', '登录成功!', true);
                    setTimeout(() => checkAuth(), 500);
                } else {
                    showMessage('login-message', data.detail || '登录失败', false);
                }
            } catch (e) {
                showMessage('login-message', '网络错误', false);
            }
        }
        
        function logout() {
            localStorage.removeItem('token');
            token = null;
            showAuthForms();
            showTab('login');
        }
        
        checkAuth();
    </script>
</body>
</html>
"""
    return html_content
