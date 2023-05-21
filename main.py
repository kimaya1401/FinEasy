import dash
from dash import Dash, html, dcc
from dash.dependencies import Input, Output, State
import sqlite3
import bcrypt

app = Dash(__name__, external_stylesheets=['https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css'], suppress_callback_exceptions=True)

# Establish SQLite database connection
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Create users table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL UNIQUE,
              password TEXT NOT NULL,
              interests TEXT);''')
conn.commit()
conn.close()

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


# Dash app layout
app.layout = html.Div(
    className="container",
    style={
        "font-family": "Arial, sans-serif",
        "font-size": "18px",
        "background-color": "#f7f7f7",
        "padding": "20px"
    },
    children=[
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content')
    ]
)

login_layout = html.Div(
    className="login-container",
    style={
        "max-width": "400px",
        "margin": "0 auto",
        "text-align": "center",
        "padding": "20px",
        "background-color": "#ffffff",
        "border": "1px solid #cccccc",
        "border-radius": "5px"
    },
    children=[
        html.H2(
            "Login",
            style={
                "font-size": "28px",
                "margin-bottom": "20px"
            }
        ),
        html.Div(
            className="form-group",
            style={"margin-bottom": "10px"},
            children=[
                html.Label("Username", style={"font-size": "20px"}),
                dcc.Input(id="login-username-input", type="text", className="form-control"),
            ]
        ),
        html.Div(
            className="form-group",
            style={"margin-bottom": "10px"},
            children=[
                html.Label("Password", style={"font-size": "20px"}),
                dcc.Input(id="login-password-input", type="password", className="form-control"),
            ]
        ),

        html.Button(
            "Login",
            id="login-button",
            className='btn btn-primary btn-lg',
            style={"font-size": "20px", "width": "100%"}
        ),
        html.Div(id="login-output", style={"margin-top": "10px"}),
        html.Div(
            children=[
                "Don't have an account? ",
                dcc.Link("Register here", href="/register", style={"font-size": "16px"})
            ],
            className="register-link",
            style={"text-align": "center", "margin-top": "10px"}
        )
    ]
)

register_layout = html.Div(
    className="register-container",
    style={
        "max-width": "400px",
        "margin": "0 auto",
        "text-align": "center",
        "padding": "20px",
        "background-color": "#ffffff",
        "border": "1px solid #cccccc",
        "border-radius": "5px"
    },
    children=[
        html.H2(
            "Register",
            style={
                "font-size": "28px",
                "margin-bottom": "20px"
            }
        ),
        html.Div(
            className="form-group",
            style={"margin-bottom": "10px"},
            children=[
                html.Label("Username", style={"font-size": "20px"}),
                dcc.Input(id="register-username-input", type="text", className="form-control"),
            ]
        ),
        html.Div(
            className="form-group",
            style={"margin-bottom": "10px"},
            children=[
                html.Label("Password", style={"font-size": "20px"}),
                dcc.Input(id="register-password-input", type="password", className="form-control"),
            ]
        ),


        html.Button(
            "Register",
            id="register-button",
            className='btn btn-primary btn-lg',
            style={"font-size": "20px", "width": "100%"}
        ),
        html.Div(id="register-output", style={"margin-top": "10px"}),
        html.Div(
            children=[
                "Already have an account? ",
                dcc.Link("Login here", href="/login", style={"font-size": "16px"})
            ],
            className="login-link",
            style={"text-align": "center", "margin-top": "10px"}
        )
    ]
)

# Home Page Layout
home_layout = html.Div([
    html.H2("Home"),
    html.H3(id='home-greeting'),
    html.H3("Add Interests"),
    dcc.Dropdown(id='interests-dropdown', options=[
        {'label': 'Stocks', 'value': 'Stocks'},
        {'label': 'Crypto', 'value': 'Crypto'},
        {'label': 'Real Estate', 'value': 'Real Estate'},
        {'label': 'Technology', 'value': 'Technology'}
    ], multi=True, placeholder="Select interests"),
    html.Button('Add Interests', id='add-interests-button', n_clicks=0),
    html.Div(id='add-interests-output'),
    html.H3("Interests"),
    html.Div(id='interests-output'),

    html.Div(
            children=[
                dcc.Link("Logout", href="/login", style={"font-size": "16px"})
            ],
            className="logout-link",
            style={"text-align": "center", "margin-top": "10px"}
        )
])

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/login':
        return login_layout
    elif pathname == '/register':
        return register_layout
    elif pathname == '/home':
        return home_layout
    else:
        return login_layout

@app.callback(Output('login-output', 'children'),
              [Input('login-button', 'n_clicks')],
              [State('login-username-input', 'value'),
               State('login-password-input', 'value')])
def login_user(n_clicks, username, password):
    if n_clicks is None:
        return ""
    else:
        if authenticate(username, password):
            return dcc.Location(href='/home?username={}'.format(username), id='login-success')
        else:
            return html.Div("Invalid username or password.", style={"color": "red"})


@app.callback(Output('register-output', 'children'),
              [Input('register-button', 'n_clicks')],
              [State('register-username-input', 'value'),
               State('register-password-input', 'value')])
def register_user(n_clicks, username, password):
    if n_clicks:
        try:
            create_user(username, password)
            create_database(username)
            add_interests(username, [])  # Initialize interests with an empty list
            #dcc.Location(href='/login', id='register-success')
            return "Registration successful. Please log in."
        except ValueError as e:
            return str(e)  # Display the error message

    return None

# Callback for add interests button
@app.callback(Output('add-interests-output', 'children'),
              [Input('add-interests-button', 'n_clicks')],
              [State('url', 'search'),
               State('interests-dropdown', 'value')])
def add_interests_to_user(n_clicks, search, interests):
    if n_clicks > 0 and search:
        params = dict(qc.split("=") for qc in search[1:].split("&"))
        username = params.get("username", "")
        if username and interests:
            add_interests(username, interests)
            return html.Div("Interests added successfully.", style={"color": "green"})
        else:
            return html.Div("Invalid request.", style={"color": "red"})
    return ""


@app.callback(Output('home-greeting', 'children'),
              [Input('url', 'search')])
def display_greeting(search):
    username = ""
    if search:
        params = dict(qc.split("=") for qc in search[1:].split("&"))
        username = params.get("username", "")
    return html.H3(f"Hello, {username}!")

# Callback for displaying interests on the home page
@app.callback(Output('interests-output', 'children'),
              [Input('url', 'search')])
def display_interests(search):
    username = ""
    if search:
        params = dict(qc.split("=") for qc in search[1:].split("&"))
        username = params.get("username", "")
    interests = get_interests(username)
    return html.P(f"Interests: {', '.join(interests)}") if interests else html.P("No interests found.")


if __name__ == '__main__':
    app.run_server(debug=True, port=8050)