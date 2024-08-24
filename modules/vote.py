from flask import Blueprint, Flask, render_template, request, redirect, session, url_for
import sqlite3
from threading import Lock

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
lock = Lock()
vote_bp = Blueprint('vote', __name__, template_folder='templates')

def get_db_connection():
    conn = sqlite3.connect('vote.db')
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                image_url TEXT NOT NULL,
                description TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                candidate_id INTEGER PRIMARY KEY,
                votes INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (candidate_id) REFERENCES candidates(id)
            )
        ''')
        # Create the admin user if it doesn't exist
        try:
            cursor.execute('SELECT * FROM users WHERE username = ?', ('Aladdin',))
            user = cursor.fetchone()
            if not user:
                cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                               ('Aladdin', '1234', 'admin'))  # lowercase 'admin'
                conn.commit()
                print("Admin user created.")
        except sqlite3.IntegrityError as e:
            print(f"Error creating admin user: {e}")

def register(username, password, role):
    with lock:
        try:
            conn = get_db_connection()
            with conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                               (username, password, role.lower()))  # lowercase role
        except sqlite3.IntegrityError as e:
            print(f"Failed to register user: {e}")

@vote_bp.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'user').lower()  # Default role is 'user' if not specified
        register(username, password, role)
        return redirect('/')
    else:
        username = session.get('username')
        return render_template('vote/register.html', username=username)

def login(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user:
        stored_password = user['password'].strip()
        input_password = password.strip()
        print(f"User found: {user['username']} with stored password: '{stored_password}'")
        print(f"Input password: '{input_password}'")
        if stored_password == input_password:
            print("Password matches.")
            return user
        else:
            print("Password does not match.")
    else:
        print("User not found.")
    return None

def admin_login(username, password):
    user = login(username, password)
    return user and user['role'].lower() == 'admin'  # lowercase 'admin'

@vote_bp.route('/candidates')
def candidates():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, image_url, description FROM candidates")
    candidates_data = cursor.fetchall()
    conn.close()

    candidates = [{
        'id': candidate['id'],
        'name': candidate['name'],
        'image_url': candidate['image_url'],
        'description': candidate['description']
    } for candidate in candidates_data]

    username = session.get('username')
    return render_template('vote/view.html', candidates=candidates, username=username)

@vote_bp.route('/add', methods=['GET', 'POST'])
def add_candidate():
    if request.method == 'POST':
        name = request.form['candidate_name']
        image_url = request.form['candidate_image']
        description = request.form['candidate_description']
        if name and image_url and description:
            try:
                conn = get_db_connection()
                with conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO candidates (name, image_url, description) VALUES (?, ?, ?)",
                                   (name, image_url, description))
                    candidate_id = cursor.lastrowid
                    cursor.execute("INSERT INTO votes (candidate_id, votes) VALUES (?, 0)", (candidate_id,))
                return redirect('/candidates')
            except sqlite3.IntegrityError:
                return "Candidate already exists"
        else:
            return "Please fill out all fields"
    else:
        username = session.get('username')
        return render_template('vote/add.html', username=username)

@vote_bp.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = login(username, password)
        if user:
            session['username'] = username
            session['role'] = user['role'].lower()  # lowercase role
            print(f"Logged in user: {username} with role: {user['role'].lower()}")
            if user['role'].lower() == 'admin':
                return redirect('/admin-vote')
            else:
                return redirect('/results')
        else:
            return "Login failed. Invalid username or password."
    else:
        return render_template('login.html')

@vote_bp.route('/vote', methods=['GET', 'POST'])
def vote():
    if request.method == 'POST':
        try:
            candidate_id = request.form['vote_for']
            insert_vote(candidate_id)
            return "Vote submitted successfully"
        except Exception as e:
            print(f"Error in /vote route: {e}")
            return f"Failed to submit vote: {e}"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, image_url, description FROM candidates")
        candidates_data = cursor.fetchall()
        conn.close()

        candidates = [{
            'id': candidate['id'],
            'name': candidate['name'],
            'image_url': candidate['image_url'],
            'description': candidate['description']
        } for candidate in candidates_data]

        return render_template('vote/vote.html', candidates=candidates)

def insert_vote(candidate_id):
    try:
        candidate_id = int(candidate_id)  # Ensure candidate_id is an integer
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO votes (candidate_id, votes)
            VALUES (?, 1)
            ON CONFLICT(candidate_id) DO UPDATE SET votes = votes + 1
        """, (candidate_id,))
        conn.commit()
    except Exception as e:
        print(f"Error inserting vote: {e}")
    finally:
        conn.close()

def get_votes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.name, v.votes
        FROM votes v
        JOIN candidates c ON v.candidate_id = c.id
    """)
    votes = cursor.fetchall()
    conn.close()
    return votes

def is_logged_in():
    return 'username' in session

def is_admin():
    return session.get('role', '').lower() == 'admin'  # lowercase 'admin'

@vote_bp.route('/admin-vote')
def admin_panel():
    if not is_logged_in() or not is_admin():
        return redirect(url_for('login_page'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, image_url, description FROM candidates")
    candidates_data = cursor.fetchall()
    conn.close()

    username = session.get('username')

    candidates = [{
        'id': candidate['id'],
        'name': candidate['name'],
        'image_url': candidate['image_url'],
        'description': candidate['description']
    } for candidate in candidates_data]

    return render_template('vote/admin.html', candidates=candidates, username=username)

@vote_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if admin_login(username, password):
            session['username'] = username
            session['role'] = 'admin'  # lowercase role
            return redirect('/admin-vote')
        else:
            return "Admin login failed. Invalid username or password."
    else:
        return render_template('vote/login.html')

@vote_bp.route('/admin/logout')
def admin_logout():
    session.pop('username', None)
    session.pop('role', None)
    return render_template('index.html')

@vote_bp.route('/results')
def results():
    votes = get_votes()
    username = session.get('username')
    return render_template('vote/results.html', results=results, username=username,  votes=votes)

@vote_bp.route('/remove_candidate', methods=['POST'])
def remove_candidate():
    if request.method == 'POST':
        candidate_id = request.form['candidate_id']
        remove_candidate_from_database(candidate_id)
        return redirect('/admin-vote')
    else:
        return "Method Not Allowed", 405

def remove_candidate_from_database(candidate_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM candidates WHERE id = ?", (candidate_id,))
    cursor.execute("DELETE FROM votes WHERE candidate_id = ?", (candidate_id,))
    conn.commit()
    conn.close()

@vote_bp.route('/users')
def users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users")
    users_data = cursor.fetchall()
    conn.close()

    username = session['username'] if 'username' in session else None

    users = [{
        'id': user['id'],
        'username': user['username'],
        'role': user['role']
    } for user in users_data]

    return render_template('vote/users.html', users=users, username=username)

@vote_bp.route('/remove_user', methods=['POST'])
def remove_user():
    if request.method == 'POST':
        user_id = request.form['user_id']
        remove_user_from_database(user_id)
        return redirect('/admin-vote')
    else:
        return "Method Not Allowed", 405

def remove_user_from_database(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)
