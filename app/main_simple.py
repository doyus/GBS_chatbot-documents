from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from core.auth import (
    Token, User, UserCreate, UserLogin,
    create_access_token, get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from core.database import init_db, create_user, authenticate_user, get_user_by_username, get_user_by_email
import os
from datetime import timedelta

app = FastAPI(title="Authentication API")

# Initialize database
init_db()

# CORS middleware
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
        "message": "Welcome to Authentication API",
        "endpoints": {
            "register": "/auth/register - User registration",
            "login": "/auth/login - User login (get JWT token)",
            "me": "/users/me - Get current user info",
            "docs": "/docs - Interactive API documentation",
            "test_page": "/test - Test authentication page"
        }
    }

# Authentication endpoints
@app.post("/auth/register", response_model=User)
async def register(user: UserCreate):
    db_user = get_user_by_username(user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    db_user = get_user_by_email(user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    new_user = create_user(user.username, user.email, user.password)
    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    return User(**new_user)

@app.post("/auth/login", response_model=Token)
async def login(user: UserLogin):
    db_user = authenticate_user(user.username, user.password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user["username"], "user_id": db_user["id"]},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Protected endpoints
@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# Test page
@app.get("/test", response_class=HTMLResponse)
async def test_page():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authentication Test</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; }
            input { width: 100%; padding: 8px; margin-bottom: 10px; }
            button { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; }
            button:hover { background: #0056b3; }
            #result { margin-top: 20px; padding: 10px; border: 1px solid #ddd; }
            .token-display { word-break: break-all; background: #f5f5f5; padding: 10px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <h1>Authentication Test</h1>
        
        <h2>Register</h2>
        <div class="form-group">
            <label>Username:</label>
            <input type="text" id="reg-username">
        </div>
        <div class="form-group">
            <label>Email:</label>
            <input type="email" id="reg-email">
        </div>
        <div class="form-group">
            <label>Password:</label>
            <input type="password" id="reg-password">
        </div>
        <button onclick="register()">Register</button>

        <h2>Login</h2>
        <div class="form-group">
            <label>Username:</label>
            <input type="text" id="login-username">
        </div>
        <div class="form-group">
            <label>Password:</label>
            <input type="password" id="login-password">
        </div>
        <button onclick="login()">Login</button>

        <h2>Get User Info (Requires Login)</h2>
        <button onclick="getUserInfo()">Get My Info</button>

        <div id="result"></div>

        <script>
            let token = '';

            function displayResult(data) {
                document.getElementById('result').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
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
                    displayResult(data);
                } catch (error) {
                    displayResult({ error: error.message });
                }
            }

            async function login() {
                const username = document.getElementById('login-username').value;
                const password = document.getElementById('login-password').value;

                try {
                    const response = await fetch('/auth/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, password })
                    });
                    const data = await response.json();
                    if (data.access_token) {
                        token = data.access_token;
                        displayResult({ 
                            message: 'Login successful! Token stored.',
                            token: token
                        });
                    } else {
                        displayResult(data);
                    }
                } catch (error) {
                    displayResult({ error: error.message });
                }
            }

            async function getUserInfo() {
                if (!token) {
                    displayResult({ error: 'Please login first' });
                    return;
                }

                try {
                    const response = await fetch('/users/me', {
                        headers: { 'Authorization': 'Bearer ' + token }
                    });
                    const data = await response.json();
                    displayResult(data);
                } catch (error) {
                    displayResult({ error: error.message });
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)
