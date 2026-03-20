import sys
sys.path.insert(0, 'app')

print("Testing imports...")

try:
    import sqlite3
    print("sqlite3: OK")
except Exception as e:
    print("sqlite3:", e)

try:
    from core import database
    print("core.database: OK")
except Exception as e:
    print("core.database:", str(e)[:100])

try:
    from core import auth
    print("core.auth: OK")
except Exception as e:
    print("core.auth:", str(e)[:100])

print("\nDone!")
