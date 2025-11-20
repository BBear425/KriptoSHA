import sqlite3
import os

def check_database():
    db_file = 'auth_system.db'
    
    print(f"📁 Database file exists: {os.path.exists(db_file)}")
    
    if os.path.exists(db_file):
        print(f"📊 Database size: {os.path.getsize(db_file)} bytes")
        
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print("📋 Tables in database:", [table[0] for table in tables])
            
            # Check users
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            print(f"👥 Users: {len(users)} rows")
            for user in users:
                print(f"   - ID: {user[0]}, Username: {user[1]}, Email: {user[4]}")
            
            # Check login attempts
            cursor.execute("SELECT * FROM login_attempts")
            attempts = cursor.fetchall()
            print(f"📝 Login attempts: {len(attempts)} rows")
            for attempt in attempts:
                print(f"   - Username: {attempt[1]}, Success: {attempt[3]}, Time: {attempt[2]}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error reading database: {e}")
    else:
        print("❌ Database file not found!")

if __name__ == "__main__":
    check_database()