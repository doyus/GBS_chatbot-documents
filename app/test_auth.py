import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.auth import hash_password, verify_password, create_access_token, verify_token
from core.database import create_user, get_user_by_username, get_user_by_email, init_db

def test_auth():
    print("=" * 50)
    print("测试认证模块")
    print("=" * 50)
    
    print("\n1. 初始化数据库...")
    init_db()
    print("   数据库初始化成功!")
    
    print("\n2. 测试密码哈希...")
    password = "test123456"
    hashed = hash_password(password)
    print(f"   原始密码: {password}")
    print(f"   哈希后: {hashed[:50]}...")
    
    print("\n3. 测试密码验证...")
    is_valid = verify_password(password, hashed)
    print(f"   正确密码验证: {'通过' if is_valid else '失败'}")
    
    is_invalid = verify_password("wrong_password", hashed)
    print(f"   错误密码验证: {'失败' if not is_invalid else '通过'}")
    
    print("\n4. 测试用户注册...")
    test_username = "testuser_" + str(os.urandom(4).hex())
    test_email = f"{test_username}@test.com"
    
    user_id = create_user(test_username, test_email, hashed)
    if user_id:
        print(f"   用户注册成功! ID: {user_id}")
    else:
        print("   用户注册失败!")
        return
    
    print("\n5. 测试用户查询...")
    user = get_user_by_username(test_username)
    if user:
        print(f"   查询成功! 用户名: {user['username']}, 邮箱: {user['email']}")
    else:
        print("   查询失败!")
    
    print("\n6. 测试JWT令牌...")
    token = create_access_token(user_id, test_username)
    print(f"   生成的令牌: {token[:50]}...")
    
    payload = verify_token(token)
    if payload:
        print(f"   令牌验证成功!")
        print(f"   用户ID: {payload.get('user_id')}")
        print(f"   用户名: {payload.get('sub')}")
    else:
        print("   令牌验证失败!")
    
    print("\n7. 测试重复注册...")
    duplicate_id = create_user(test_username, test_email, hashed)
    if duplicate_id is None:
        print("   重复注册被正确拒绝!")
    else:
        print("   重复注册未被拒绝!")
    
    print("\n" + "=" * 50)
    print("所有测试完成!")
    print("=" * 50)

if __name__ == "__main__":
    test_auth()
