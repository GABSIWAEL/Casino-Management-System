from flask import Flask, render_template, request, g, redirect, url_for, jsonify
import random
import sqlite3
import string
from datetime import datetime

app = Flask(__name__)

DATABASE = 'casino.db'

# Database initialization functions


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Routes


@app.route('/')
def index():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM operations")
        operations = cur.fetchall()
    return render_template('index.html', operations=operations)


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/create_user', methods=['POST'])
def create_user():
    number = ''.join(random.choices(string.digits, k=5))
    password = ''.join(random.choices(
        string.ascii_letters + string.digits, k=8))
    amount = request.form['amount']
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO users (number, password, balance) VALUES (?, ?, ?)",
                    (number, password, amount))
        cur.execute("INSERT INTO operations (account_number, operation, amount, timestamp) VALUES (?, ?, ?, ?)",
                    (number, "Create User", amount, datetime.now()))
        conn.commit()
    message = "User created successfully! Number: {}, Password: {}".format(
        number, password)
    return render_template('dashboard.html', message1=message)


@app.route('/recharge', methods=['POST'])
def recharge():
    number = request.form['number']
    amount = int(request.form['amount'])
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET balance = balance + ? WHERE number = ?", (amount, number))
        cur.execute("INSERT INTO operations (account_number, operation, amount, timestamp) VALUES (?, ?, ?, ?)",
                    (number, "Recharge", amount, datetime.now()))
        conn.commit()
    return render_template('dashboard.html', message="Recharge successful!")


@app.route('/withdraw', methods=['POST'])
def withdraw():
    number = request.form['number']
    amount = int(request.form['amount'])
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT balance FROM users WHERE number = ?", (number,))
        user = cur.fetchone()
        if user:
            current_balance = user[0]
            if current_balance >= amount:
                cur.execute(
                    "UPDATE users SET balance = balance - ? WHERE number = ?", (amount, number))
                cur.execute("INSERT INTO operations (account_number, operation, amount, timestamp) VALUES (?, ?, ?, ?)",
                            (number, "Withdraw", amount, datetime.now()))
                conn.commit()
                return render_template('dashboard.html', message="Withdrawal successful!")
            else:
                return render_template('dashboard.html', message="Insufficient funds!")
        else:
            return render_template('dashboard.html', message="User not found!")


if __name__ == '__main__':
    app.run(debug=True)
