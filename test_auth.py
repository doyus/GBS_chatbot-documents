import sys
sys.path.insert(0, 'app')

from core.database import init_db, create_user, authenticate_user, get_user_by_id, get_user_by_username
from core.auth import create_access_token
from core.database import verify_password, hash_password

# Test database operations
print("Testing database operations...")
init_db()

# Test password hashing
print("\nTesting password hashing...")
test_password = "test123"
hashed = hash_password(test_password)
print(f"Password: {test_password}")
print(f"Hashed: {hashed}")
print(f"Verify: {verify_password(hashed, test_password)}")
print(f"Verify wrong: {verify_password(hashed, 'wrong')}")

# Test user creation
print("\nTesting user creation...")
user = create_user("testuser", "test@example.com", "password123")
if user:
    print(f"User created: {user}")
else:
    print("User already exists, testing login...")

# Test authentication
print("\nTesting authentication...")
auth_user = authenticate_user("testuser", "password123")
if auth_user:
    print(f"Authenticated: {auth_user['username']}")
else:
    print("Authentication failed")

# Test wrong password
wrong_auth = authenticate_user("testuser", "wrongpassword")
if wrong_auth:
    print("ERROR: Wrong password should not authenticate")
else:
    print("Wrong password correctly rejected")

# Test JWT token creation
print("\nTesting JWT token...")
if auth_user:
    token = create_access_token(data={"sub": auth_user["username"], "user_id": auth_user["id"]})
    print(f"Token created: {token[:50]}...")

print("\nAll tests completed!")
