import sqlite3
import datetime
import bcrypt

# Function to authenticate user
def authenticate(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()

    if result and bcrypt.checkpw(password.encode('utf-8'), result[0]):
        return True
    else:
        return False

# Function to create a new user
def create_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    if password is None:
        raise ValueError("Password cannot be None")

    c.execute("SELECT username FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    if result:
        raise ValueError("Username already exists")

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    conn.close()

# Function to create a database for a user
def create_database(username):
    db_name = f"{username}.db"
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    # create the income table
    c.execute("CREATE TABLE IF NOT EXISTS income (id INTEGER PRIMARY KEY, amount REAL, date TEXT)")

    # create the expenses table
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, amount REAL, category TEXT, date TEXT)''')

    # Create the savings table
    c.execute("CREATE TABLE IF NOT EXISTS savings (id INTEGER PRIMARY KEY AUTOINCREMENT, amount REAL, date TEXT)")
    # commit the changes and close the connection
    conn.commit()
    conn.close()

def add_interests(username, interests):
    # Convert the list of interests to a comma-separated string
    interests_str = ', '.join(interests)

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE users SET interests=? WHERE username=?", (interests_str, username))
    conn.commit()
    conn.close()
    print("Interests added successfully.")

def get_interests(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT interests FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()

    if result:
        interests_str = result[0]
        interests = [interest.strip() for interest in interests_str.split(',')]
        return interests
    else:
        return []

def add_income(username, amount, date):
    if username:
        db_name = f"{username}.db"
        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        # Calculate the month from the date
        dt = datetime.datetime.strptime(date, "%Y-%m-%d")
        month = dt.month

        # Insert the income into the income table
        c.execute("INSERT INTO income (amount, date) VALUES (?, ?)", (amount, date))

        conn.commit()
        conn.close()

        print("Income added successfully.")


    else:
        print("No username found in session.")


def update_income(username: str, income_id: int, amount: float, date: object) -> None:
    """
    Updates an existing income record for the specified user.

    :param username: The username of the user.
    :param income_id: The ID of the income record to update.
    :param amount: The new amount of the income.
    :param month: The new month of the income.
    """
    with sqlite3.connect(f"{username}.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE income SET amount=?, date=? WHERE id=?", (amount, date, income_id))
        print(f"Updated income successfully with id: {income_id}.")
        conn.commit()


def delete_income(username: str, income_id: int) -> None:
    """
    Deletes an existing income record for the specified user.

    :param username: The username of the user.
    :param income_id: The ID of the income record to delete.
    """
    with sqlite3.connect(f"{username}.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM income WHERE id=?", (income_id,))
        print(f"Deleted income with id: {income_id}.")
        conn.commit()

# Helper function to get income data from the database
def get_income(username):
    db_name = f"{username}.db"
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT id, amount, date FROM income ORDER BY date DESC")
    income_data = c.fetchall()
    conn.close()
    return income_data

# Function to add an expense for a user
def add_expense(username, amount, category, date):
    db_name = f"{username}.db"
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO expenses (amount, category, date) VALUES (?, ?, ?)", (amount, category, date))
        conn.commit()
        calculate_savings(username)
    except sqlite3.Error as e:
        conn.close()
        raise sqlite3.Error("Failed to add expense: " + str(e))
    conn.close()

def update_expense(username: str, expense_id: int, amount: float, category: str, date: str) -> None:
    """
    Updates an existing expense record for the specified user.

    :param username: The username of the user.
    :param expense_id: The ID of the expense record to update.
    :param amount: The new amount of the expense.
    :param category: The new category of the expense.
    :param date: The new date of the expense in 'YYYY-MM-DD' format.
    """
    with sqlite3.connect(f"{username}.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE expenses SET amount=?, category=?, date=? WHERE id=?", (amount, category, date, expense_id))
        print(f"Updated expense successfully with id: {expense_id}.")
        conn.commit()


def delete_expense(username: str, expense_id: int) -> None:
    """
    Deletes an existing expense record for the specified user.

    :param username: The username of the user.
    :param expense_id: The ID of the expense record to delete.
    """
    with sqlite3.connect(f"{username}.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
        print(f"Deleted expense with id: {expense_id}.")
        conn.commit()

# Function to get all expenses for a user
def get_all_expenses(username):
    db_name = f"{username}.db"
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("SELECT * FROM expenses")
    all_expenses = c.fetchall()

    conn.close()

    return all_expenses

# Function to get all savings for a user
def get_all_savings(username):
    db_name = f"{username}.db"
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("SELECT * FROM savings")
    all_savings = c.fetchall()

    conn.close()

    return all_savings

# Function to calculate savings for a user
def calculate_savings(username):
    db_name = f"{username}.db"
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    # Get the income for the user
    c.execute("SELECT SUM(amount) FROM income")
    income = c.fetchone()[0]
    if income is None:
        income = 0

    # Get the total expenses for the user
    c.execute("SELECT amount, date FROM expenses")
    expense_data = c.fetchall()

    total_expenses = 0
    for amount, added_date in expense_data:
        total_expenses += amount

    if total_expenses is None:
        total_expenses = 0

    # Calculate the savings for the user
    savings = income - total_expenses

    # Insert the savings into the savings table
    c.execute("INSERT INTO savings (amount, date) VALUES (?, ?)", (savings, added_date))

    conn.commit()
    conn.close()

    print("Savings calculated successfully.")

    return savings
