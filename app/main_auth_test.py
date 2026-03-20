from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from core.auth import (
    UserRegister, UserLogin, get_current_user,
    create_access_token, verify_password_strength, validate_email, ACCESS_TOKEN_EXPIRE_MINUTES
)
from core.database import create_user, verify_user, get_user_by_id
from datetime import timedelta
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "JWT Auth API Test",
        "endpoints": {
            "register": "POST /auth/register - Register new user",
            "login": "POST /auth/login - User login",
            "me": "GET /auth/me - Get current user info (requires JWT)",
            "test_page": "/auth/test - Interactive test page",
            "docs": "/docs - API documentation"
        }
    }


@app.post("/auth/register")
async def register(user_data: UserRegister):
    if len(user_data.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters long")
    
    if not validate_email(user_data.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    is_strong, msg = verify_password_strength(user_data.password)
    if not is_strong:
        raise HTTPException(status_code=400, detail=msg)
    
    result = create_user(user_data.username, user_data.email, user_data.password)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return {
        "success": True,
        "message": result["message"],
        "user": {
            "id": result["user_id"],
            "username": result["username"],
            "email": result["email"]
        }
    }


@app.post("/auth/login")
async def login(user_data: UserLogin):
    result = verify_user(user_data.username_or_email, user_data.password)
    
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(result["user_id"]), "username": result["username"], "email": result["email"]},
        expires_delta=access_token_expires
    )
    
    return {
        "success": True,
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": result["user_id"],
            "username": result["username"],
            "email": result["email"]
        }
    }


@app.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user = get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "success": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "created_at": user["created_at"],
            "last_login": user["last_login"]
        }
    }


@app.get("/auth/test", response_class=HTMLResponse)
async def auth_test_page():
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>JWT 认证测试页面</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
            }
            h1 {
                text-align: center;
                color: white;
                margin-bottom: 30px;
                font-size: 2.5em;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            }
            .card {
                background: white;
                border-radius: 16px;
                padding: 30px;
                margin-bottom: 20px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            }
            .card h2 {
                color: #333;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid #667eea;
            }
            .form-group {
                margin-bottom: 15px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                color: #555;
                font-weight: 600;
            }
            input {
                width: 100%;
                padding: 12px 15px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            input:focus {
                outline: none;
                border-color: #667eea;
            }
            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
                margin-right: 10px;
                margin-bottom: 10px;
            }
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
            }
            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            .result {
                margin-top: 15px;
                padding: 15px;
                border-radius: 8px;
                font-family: monospace;
                font-size: 14px;
                word-break: break-all;
                max-height: 300px;
                overflow-y: auto;
            }
            .result.success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .result.error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            .result.info {
                background: #d1ecf1;
                color: #0c5460;
                border: 1px solid #bee5eb;
            }
            .token-display {
                background: #f8f9fa;
                padding: 10px;
                border-radius: 6px;
                margin-top: 10px;
                font-size: 12px;
                word-break: break-all;
                max-height: 100px;
                overflow-y: auto;
            }
            .user-info {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }
            .user-info-item {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
            }
            .user-info-item label {
                font-size: 12px;
                color: #888;
                text-transform: uppercase;
            }
            .user-info-item value {
                font-size: 16px;
                color: #333;
                font-weight: 600;
            }
            .hidden { display: none; }
            .tabs {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
            }
            .tab {
                padding: 10px 20px;
                background: #f0f0f0;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                color: #666;
            }
            .tab.active {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 JWT 认证测试</h1>
            
            <div class="card">
                <div class="tabs">
                    <button class="tab active" onclick="showTab('register')">注册</button>
                    <button class="tab" onclick="showTab('login')">登录</button>
                    <button class="tab" onclick="showTab('profile')">用户信息</button>
                </div>
                
                <!-- 注册表单 -->
                <div id="register-tab">
                    <h2>用户注册</h2>
                    <div class="form-group">
                        <label>用户名</label>
                        <input type="text" id="reg-username" placeholder="至少3个字符">
                    </div>
                    <div class="form-group">
                        <label>邮箱</label>
                        <input type="email" id="reg-email" placeholder="example@email.com">
                    </div>
                    <div class="form-group">
                        <label>密码</label>
                        <input type="password" id="reg-password" placeholder="至少6位，包含字母和数字">
                    </div>
                    <button onclick="register()">注册</button>
                    <div id="register-result" class="result hidden"></div>
                </div>
                
                <!-- 登录表单 -->
                <div id="login-tab" class="hidden">
                    <h2>用户登录</h2>
                    <div class="form-group">
                        <label>用户名或邮箱</label>
                        <input type="text" id="login-username" placeholder="用户名或邮箱">
                    </div>
                    <div class="form-group">
                        <label>密码</label>
                        <input type="password" id="login-password" placeholder="密码">
                    </div>
                    <button onclick="login()">登录</button>
                    <div id="login-result" class="result hidden"></div>
                    <div id="token-display" class="token-display hidden"></div>
                </div>
                
                <!-- 用户信息 -->
                <div id="profile-tab" class="hidden">
                    <h2>当前用户信息</h2>
                    <button onclick="getProfile()">获取用户信息</button>
                    <button onclick="clearToken()">清除 Token</button>
                    <div id="profile-result" class="result hidden"></div>
                </div>
            </div>
            
            <div class="card">
                <h2>API 端点说明</h2>
                <div class="user-info">
                    <div class="user-info-item">
                        <label>注册</label>
                        <value>POST /auth/register</value>
                    </div>
                    <div class="user-info-item">
                        <label>登录</label>
                        <value>POST /auth/login</value>
                    </div>
                    <div class="user-info-item">
                        <label>获取用户信息</label>
                        <value>GET /auth/me</value>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let currentToken = localStorage.getItem('access_token') || '';
            
            function showTab(tabName) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('[id$="-tab"]').forEach(t => t.classList.add('hidden'));
                
                event.target.classList.add('active');
                document.getElementById(tabName + '-tab').classList.remove('hidden');
            }
            
            function showResult(elementId, message, type) {
                const el = document.getElementById(elementId);
                el.textContent = typeof message === 'object' ? JSON.stringify(message, null, 2) : message;
                el.className = 'result ' + type;
                el.classList.remove('hidden');
            }
            
            async function register() {
                const username = document.getElementById('reg-username').value;
                const email = document.getElementById('reg-email').value;
                const password = document.getElementById('reg-password').value;
                
                try {
                    const response = await fetch('/auth/register', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, email, password })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        showResult('register-result', data, 'success');
                        document.getElementById('reg-username').value = '';
                        document.getElementById('reg-email').value = '';
                        document.getElementById('reg-password').value = '';
                    } else {
                        showResult('register-result', data.detail || data.message || '注册失败', 'error');
                    }
                } catch (error) {
                    showResult('register-result', '网络错误: ' + error.message, 'error');
                }
            }
            
            async function login() {
                const username_or_email = document.getElementById('login-username').value;
                const password = document.getElementById('login-password').value;
                
                try {
                    const response = await fetch('/auth/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username_or_email, password })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        currentToken = data.access_token;
                        localStorage.setItem('access_token', currentToken);
                        showResult('login-result', '登录成功！', 'success');
                        
                        const tokenEl = document.getElementById('token-display');
                        tokenEl.textContent = 'Token: ' + currentToken.substring(0, 50) + '...';
                        tokenEl.classList.remove('hidden');
                        
                        document.getElementById('login-username').value = '';
                        document.getElementById('login-password').value = '';
                    } else {
                        showResult('login-result', data.detail || data.message || '登录失败', 'error');
                    }
                } catch (error) {
                    showResult('login-result', '网络错误: ' + error.message, 'error');
                }
            }
            
            async function getProfile() {
                if (!currentToken) {
                    showResult('profile-result', '请先登录获取 Token', 'error');
                    return;
                }
                
                try {
                    const response = await fetch('/auth/me', {
                        headers: { 'Authorization': 'Bearer ' + currentToken }
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        showResult('profile-result', data, 'success');
                    } else {
                        showResult('profile-result', data.detail || '获取失败', 'error');
                    }
                } catch (error) {
                    showResult('profile-result', '网络错误: ' + error.message, 'error');
                }
            }
            
            function clearToken() {
                currentToken = '';
                localStorage.removeItem('access_token');
                showResult('profile-result', 'Token 已清除', 'info');
                document.getElementById('token-display').classList.add('hidden');
            }
            
            // 页面加载时检查是否有保存的 token
            if (currentToken) {
                document.getElementById('token-display').textContent = 'Token: ' + currentToken.substring(0, 50) + '...';
                document.getElementById('token-display').classList.remove('hidden');
            }
        </script>
    </body>
    </html>
    """
    return html_content


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
