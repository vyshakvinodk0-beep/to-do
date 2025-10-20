from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'secretkey123'  # Change this to something secure

# ----------------------------
# DATABASE CONNECTION
# ----------------------------
def get_db():
    conn = sqlite3.connect('todo.db')
    conn.row_factory = sqlite3.Row
    return conn

# ----------------------------
# INITIALIZE DATABASE (RUN ONCE)
# ----------------------------
def init_db():
    # Create database file folder if needed (not necessary for sqlite file in working dir,
    # but keeps things explicit)
    db_exists = os.path.exists('todo.db')
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT
                    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        task TEXT,
                        status TEXT,
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')
    conn.commit()
    conn.close()

# ----------------------------
# LOGIN PAGE
# ----------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect('/todo')
        else:
            return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')

# ----------------------------
# REGISTER PAGE
# ----------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        existing = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if existing:
            conn.close()
            return render_template('register.html', error="Username already exists")

        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('register.html')

# ----------------------------
# TO-DO LIST PAGE
# ----------------------------
@app.route('/todo')
def todo():
    if 'user_id' not in session:
        return redirect('/')
    conn = get_db()
    tasks = conn.execute("SELECT * FROM tasks WHERE user_id=?", (session['user_id'],)).fetchall()
    conn.close()
    return render_template('todo.html', tasks=tasks, username=session.get('username'))

# ----------------------------
# ADD TASK
# ----------------------------
@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session:
        return redirect('/')
    task = request.form['task']
    conn = get_db()
    conn.execute(
        "INSERT INTO tasks (user_id, task, status) VALUES (?, ?, 'pending')",
        (session['user_id'], task)
    )
    conn.commit()
    conn.close()
    return redirect('/todo')

# ----------------------------
# MARK TASK AS DONE
# ----------------------------
@app.route('/done/<int:id>')
def done(id):
    if 'user_id' not in session:
        return redirect('/')
    conn = get_db()
    conn.execute("UPDATE tasks SET status='done' WHERE id=? AND user_id=?", (id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect('/todo')

# ----------------------------
# DELETE TASK
# ----------------------------
@app.route('/delete/<int:id>')
def delete(id):
    if 'user_id' not in session:
        return redirect('/')
    conn = get_db()
    conn.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect('/todo')

# ----------------------------
# LOGOUT
# ----------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ----------------------------
# RUN APP
# ----------------------------
if __name__ == '__main__':
    # Ensure DB is initialized before serving requests
    with app.app_context():
        init_db()
    app.run(debug=True)
