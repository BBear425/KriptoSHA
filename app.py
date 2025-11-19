from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib
import secrets
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Ganti dengan random key
DATABASE = 'database.db'

def init_db():
    """Initialize database"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            success BOOLEAN
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password, salt=None):
    """Hash password dengan salt"""
    if salt is None:
        salt = secrets.token_hex(32)
    salted_password = password + salt
    password_hash = hashlib.sha256(salted_password.encode()).hexdigest()
    return password_hash, salt

def verify_password(password, stored_hash, salt):
    """Verify password"""
    test_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(test_hash, stored_hash)

@app.route('/')
def index():
    """Home page"""
    if 'user_id' in session:
        return f'<h1>Welcome {session["username"]}!</h1><a href="/logout">Logout</a>'
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        try:
            # Hash password
            password_hash, salt = hash_password(password)
            
            # Insert user
            cursor.execute(
                'INSERT INTO users (username, password_hash, salt, email) VALUES (?, ?, ?, ?)',
                (username, password_hash, salt, email)
            )
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except sqlite3.IntegrityError:
            flash('Username already exists!', 'error')
        finally:
            conn.close()
    
    return '''
        <form method="POST">
            <h2>Register</h2>
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="email" name="email" placeholder="Email" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Register</button>
        </form>
        <a href="/login">Login</a>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get user data
        cursor.execute(
            'SELECT id, username, password_hash, salt FROM users WHERE username = ?',
            (username,)
        )
        user = cursor.fetchone()
        
        if user and verify_password(password, user[2], user[3]):
            # Login successful
            session['user_id'] = user[0]
            session['username'] = user[1]
            
            # Log successful attempt
            cursor.execute(
                'INSERT INTO login_attempts (username, success) VALUES (?, ?)',
                (username, True)
            )
            conn.commit()
            conn.close()
            
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            # Login failed
            cursor.execute(
                'INSERT INTO login_attempts (username, success) VALUES (?, ?)',
                (username, False)
            )
            conn.commit()
            conn.close()
            
            flash('Invalid credentials!', 'error')
    
    return '''
        <form method="POST">
            <h2>Login</h2>
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Login</button>
        </form>
        <a href="/register">Register</a>
    '''

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    """Admin page to view users"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, username, email, created_at FROM users')
    users = cursor.fetchall()
    
    cursor.execute('SELECT username, attempt_time, success FROM login_attempts ORDER BY attempt_time DESC LIMIT 10')
    attempts = cursor.fetchall()
    
    conn.close()
    
    users_html = '<h3>Registered Users:</h3><ul>'
    for user in users:
        users_html += f'<li>ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Joined: {user[3]}</li>'
    users_html += '</ul>'
    
    attempts_html = '<h3>Recent Login Attempts:</h3><ul>'
    for attempt in attempts:
        status = '✅' if attempt[2] else '❌'
        attempts_html += f'<li>{status} {attempt[0]} at {attempt[1]}</li>'
    attempts_html += '</ul>'
    
    return f'<h2>Admin Panel</h2>{users_html}{attempts_html}<a href="/">Home</a>'

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)