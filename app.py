from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"


def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        amount REAL,
        category TEXT,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()


# ---------- Register ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()

        # Check if username already exists
        existing_user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        if existing_user:
            flash("Username already exists!", "error")
            conn.close()
            return redirect('/register')

        # Hash password
        hashed_password = generate_password_hash(password)

        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_password)
        )
        conn.commit()
        conn.close()

        flash("Registration successful! Please login.", "success")
        return redirect('/')

    return render_template("register.html")


# ---------- Login ----------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            flash("Login successful!", "success")
            return redirect('/dashboard')
        else:
            flash("Invalid username or password!", "error")

    return render_template("login.html")

# ---------- Dashboard ----------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')

    conn = get_db()
    expenses = conn.execute(
        "SELECT * FROM expenses WHERE user_id=?",
        (session['user_id'],)
    ).fetchall()

    total = sum(exp['amount'] for exp in expenses)

    # Category data for chart
    categories = {}
    for exp in expenses:
        categories[exp['category']] = categories.get(exp['category'], 0) + exp['amount']

    conn.close()

    return render_template(
        "dashboard.html",
        expenses=expenses,
        total=total,
        categories=categories
    )


# ---------- Add Expense ----------
@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'user_id' not in session:
        return redirect('/')

    if request.method == 'POST':
        title = request.form['title']
        amount = request.form['amount']
        category = request.form['category']
        date = request.form['date']

        conn = get_db()
        conn.execute(
            "INSERT INTO expenses (user_id, title, amount, category, date) VALUES (?, ?, ?, ?, ?)",
            (session['user_id'], title, amount, category, date)
        )
        conn.commit()
        conn.close()

        return redirect('/dashboard')

    return render_template("add_expense.html")

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if 'user_id' not in session:
        return redirect('/')

    conn = get_db()

    expense = conn.execute(
        "SELECT * FROM expenses WHERE id=? AND user_id=?",
        (id, session['user_id'])
    ).fetchone()

    if request.method == 'POST':
        title = request.form['title']
        amount = request.form['amount']
        category = request.form['category']
        date = request.form['date']

        conn.execute("""
            UPDATE expenses
            SET title=?, amount=?, category=?, date=?
            WHERE id=? AND user_id=?
        """, (title, amount, category, date, id, session['user_id']))

        conn.commit()
        conn.close()

        flash("Expense updated successfully!", "success")
        return redirect('/dashboard')

    conn.close()
    return render_template("edit_expense.html", expense=expense)

@app.route('/delete/<int:id>')
def delete(id):
    if 'user_id' not in session:
        return redirect('/')

    conn = get_db()
    conn.execute(
        "DELETE FROM expenses WHERE id=? AND user_id=?",
        (id, session['user_id'])
    )
    conn.commit()
    conn.close()

    flash("Expense deleted successfully!", "success")
    return redirect('/dashboard')


# ---------- Logout ----------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)