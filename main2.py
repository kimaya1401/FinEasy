import datetime
from urllib.parse import urljoin

from dash import dash_table
import requests
import dash
import pandas as pd
import plotly.express as px
import flask
from dash import Dash, html, dcc
from dash.dependencies import Input, Output, State
import sqlite3
from bs4 import BeautifulSoup

from user import authenticate, add_interests, get_interests, create_user, create_database, get_income, add_income, \
    add_expense, update_income, delete_income, get_all_expenses, get_all_savings
from flask import Flask, session
import dash_bootstrap_components as dbc

server = Flask(__name__)
server.secret_key = 'your_secret_key'

app = Dash(__name__, server=server,
           external_stylesheets=['https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css',
                                 dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

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

# Update the app layout
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


# Function to generate navigation bar component
def generate_navbar(page_name="Home"):
    return html.Nav(
        className="navbar navbar-expand-lg navbar-dark",
        style={"background": "linear-gradient(to right, #007bff, #00a8ff)"},
        children=[
            html.Div(
                className="collapse navbar-collapse",
                id="navbarNav",
                children=[
                    html.Ul(className="navbar-nav mr-auto", children=[
                        html.Li(className="nav-item", children=[
                            dcc.Link("Add Finances", href="/income", className="nav-link", style={"color": "#fff"})
                        ]),
                        html.Li(className="nav-item", children=[
                            dcc.Link("View Insights", href="/expenses", className="nav-link", style={"color": "#fff"})
                        ]),
                        html.Li(className="nav-item", children=[
                            dcc.Link("Savings", href="/savings", className="nav-link", style={"color": "#fff"})
                        ]),
                        html.Li(className="nav-item", children=[
                            dcc.Link("News", href="/news", className="nav-link", style={"color": "#fff"})
                        ]),
                        html.Li(className="nav-item", children=[
                            dcc.Link("Stocks", href="/stocks", className="nav-link", style={"color": "#fff"})
                        ])
                    ])
                ]
            ),
            html.A(
                className="navbar-brand ml-auto",
                href="/home",
                children=[
                    html.H4(page_name)
                ],
                style={"border": "1px solid #fff", "padding": "7px", "color": "#fff"}
            ),
            html.A(
                children=[
                    dcc.Link("Logout", href="/login",
                             style={"border": "1px solid #fff", "padding": "7px", "color": "#fff"})
                ],
                className="navbar-brand ml-auto"
            ),
            html.Button(
                className="navbar-toggler",
                type="button",
                **{"data-toggle": "collapse", "data-target": "#navbarNav"},
                children=[
                    html.Span(className="navbar-toggler-icon")
                ]
            ),
        ]
    )


def get_most_active_stocks():
    url = 'https://finance.yahoo.com/most-active'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')
    rows = table.find_all('tr')
    stocks = []
    for row in rows[1:]:  # skipping header row
        cells = row.find_all('td')
        company_name = cells[1].text.strip()
        last_price = cells[2].text.strip()
        change = cells[3].text.strip()
        percent_change = cells[4].text.strip()
        volume = cells[6].text.strip()
        stocks.append((company_name, last_price, change, percent_change, volume))
    return stocks


def create_table(data):
    df = pd.DataFrame(data, columns=['Company Name', 'Last Price', 'Change', 'Percent Change', 'Volume'])
    table = dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in df.columns],
        style_header={'backgroundColor': '#343a40', 'color': 'white', 'fontWeight': 'bold'},
        style_cell={'backgroundColor': '#f8f9fa', 'color': '#212529', 'textAlign': 'center'},
        style_data={'border': '1px solid #dee2e6'},
        style_table={'margin': 'auto', 'width': '80%'}
    )
    return table


@app.callback(
    dash.dependencies.Output('output-table', 'children'),
    dash.dependencies.Input('refresh-button', 'n_clicks')
)
def update_table(n_clicks):
    stocks = get_most_active_stocks()
    table = create_table(stocks)
    return table


def get_technology_data():
    url = 'https://finance.yahoo.com/screener/predefined/ms_technology/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')
    rows = table.find_all('tr')

    data = []
    for row in rows[1:]:  # skipping header row
        cells = row.find_all('td')
        name = cells[1].text.strip()
        price = cells[2].text.strip()
        change = cells[3].text.strip()
        percent_change = cells[4].text.strip()
        volume = cells[5].text.strip()
        avg_volume = cells[6].text.strip()
        market = cells[7].text.strip()
        data.append({
            'Name': name,
            'Price': price,
            'Change': change,
            '% Change': percent_change,
            'Volume': volume,
            'Avg Volume': avg_volume,
            'Market Cap': market
        })
    return data


def generate_table(data):
    df = pd.DataFrame(data, columns=['Name', 'Price', 'Change', '% Change', 'Volume', 'Avg Volume', 'Market Cap'])
    table = dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in df.columns],
        style_header={'backgroundColor': '#343a40', 'color': 'white', 'fontWeight': 'bold'},
        style_cell={'backgroundColor': '#f8f9fa', 'color': '#212529', 'textAlign': 'center'},
        style_data={'border': '1px solid #dee2e6'},
        style_table={'margin': 'auto', 'width': '80%'}
    )
    return table


@app.callback(
    dash.dependencies.Output('technology-table', 'children'),
    dash.dependencies.Input('refresh-button', 'n_clicks')
)
def update_technology_table(n_clicks):
    data = get_technology_data()
    table = generate_table(data)
    return table


# CSS styles
styles = {
    'header': {
        'textAlign': 'center',
        'paddingTop': '20px',
        'marginBottom': '30px',
        'fontSize': '30px',
        'fontWeight': 'bold'
    },
    'refreshButton': {
        'marginBottom': '20px'
    },
    'table': {
        'margin': '0 auto',
        'width': '80%',
        'borderCollapse': 'collapse'
    },
    'tableHeader': {
        'backgroundColor': '#343a40',
        'color': 'white',
        'fontWeight': 'bold',
        'padding': '10px',
        'border': '1px solid #ddd'
    },
    'tableCell': {
        'padding': '10px',
        'border': '1px solid #ddd',
        'backgroundColor': '#f8f9fa',
        'color': '#212529'
    }
}


def get_real_estate_data():
    url = 'https://finance.yahoo.com/screener/predefined/ms_real_estate/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find('table')
    rows = table.find_all('tr')

    data = []
    for row in rows[1:]:  # skipping header row
        cells = row.find_all('td')
        name = cells[1].text.strip()
        price = cells[2].text.strip()
        change = cells[3].text.strip()
        percent_change = cells[4].text.strip()
        volume = cells[5].text.strip()
        avg_volume = cells[6].text.strip()
        market = cells[7].text.strip()
        data.append({
            'Name': name,
            'Price': price,
            'Change': change,
            '% Change': percent_change,
            'Volume': volume,
            'Avg Volume': avg_volume,
            'Market Cap': market
        })
    return data


def generate_realestate_table(data):
    headers = ['Name', 'Price', 'Change', '% Change', 'Volume', 'Avg Volume', 'Market Cap']
    table_header = [html.Th(header, style=styles['tableHeader']) for header in headers]
    table_body = []
    for row in data:
        table_row = [html.Td(row[header], style=styles['tableCell']) for header in headers]
        table_body.append(html.Tr(table_row))

    table = html.Table([html.Thead(table_header), html.Tbody(table_body)], style=styles['table'])
    return table


@app.callback(
    dash.dependencies.Output('real-estate-table', 'children'),
    dash.dependencies.Input('refresh-button', 'n_clicks')
)
def update_real_estate_table(n_clicks):
    data = get_real_estate_data()
    table = generate_realestate_table(data)
    return table

def top_gainers():
    url = 'https://coinmarketcap.com/gainers-losers/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    gainers_table = soup.find_all('table')[0]
    gainers_rows = gainers_table.find_all('tr')
    gainers_data = []
    for row in gainers_rows[1:]:
        cols = row.find_all('td')
        name = cols[1].text.strip()
        price = cols[3].text.strip()
        percent_change = cols[4].text.strip()
        gainers_data.append((name, price, percent_change))
    return gainers_data


def create_top_gainers_table(data):
    df = pd.DataFrame(data, columns=['Name', 'Price', 'Percent Change'])
    table = dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in df.columns],
        style_header={'backgroundColor': '#343a40', 'color': 'white', 'fontWeight': 'bold'},
        style_cell={'backgroundColor': '#f8f9fa', 'color': '#212529', 'textAlign': 'center'},
        style_data={'border': '1px solid #dee2e6'},
        style_table={'margin': 'auto', 'width': '80%'}
    )
    return table


@app.callback(
    dash.dependencies.Output('gainers-table', 'children'),
    dash.dependencies.Input('refresh-g_button', 'n_clicks')
)
def update_gainers_table(n_clicks):
    if n_clicks is not None and n_clicks > 0:
        stocks = top_gainers()
        table = create_top_gainers_table(stocks)
        return table
    else:
        return ""


def top_losers():
    url = 'https://coinmarketcap.com/gainers-losers/'

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    losers_table = soup.find_all('table')[1]
    losers_rows = losers_table.find_all('tr')
    losers_data = []
    for row in losers_rows[1:]:
        cols = row.find_all('td')
        name = cols[1].text.strip()
        price = cols[3].text.strip()
        percent_change = cols[4].text.strip()
        losers_data.append((name, price, percent_change))
    return losers_data


def create_top_losers_table(data):
    df = pd.DataFrame(data, columns=['Name', 'Price', 'Percent Change'])
    table = dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in df.columns],
        style_header={'backgroundColor': '#343a40', 'color': 'white', 'fontWeight': 'bold'},
        style_cell={'backgroundColor': '#f8f9fa', 'color': '#212529', 'textAlign': 'center'},
        style_data={'border': '1px solid #dee2e6'},
        style_table={'margin': 'auto', 'width': '80%'}
    )
    return table


@app.callback(
    dash.dependencies.Output('losers-table', 'children'),
    dash.dependencies.Input('refresh-l_button', 'n_clicks')
)
def update_losers_table(n_clicks):
    if n_clicks is not None and n_clicks > 0:
        stocks = top_losers()
        table = create_top_losers_table(stocks)
        return table
    else:
        return ""

@app.callback(Output('selected-interests-output', 'children'),
              [Input('url', 'pathname')])
def display_selected_interests(pathname):
    username = session.get('username', '')
    selected_interests = get_interests(username)

    sections = {
        ('Stocks', 'Technology'): [
            dbc.Container(
                fluid=True,
                className='p-3',
                children=[
                    dbc.Row(
                        dbc.Col(
                            html.H1('Most Active Stocks', className='text-center mb-4'),
                        )
                    ),
                    dbc.Row(
                        dbc.Col(
                            dbc.Button('Refresh', id='refresh-button', n_clicks=0, color='primary',
                                       className='mx-auto d-block',
                                       style={'width': '200px'}),
                            className='mb-4'
                        )
                    ),
                    dbc.Row(
                        dbc.Col(
                            html.Div(id='output-table'),
                        )
                    ),
                    dbc.Row(
                        dbc.Col(
                            html.H1('Technology Stocks', className='text-center mb-4', style={'padding': '10px'}),
                        )
                    ),
                    dbc.Row(
                        dbc.Col(
                            dbc.Button('Refresh', id='refresh-button', n_clicks=0, color='primary',
                                       className='mx-auto d-block',
                                       style={'width': '200px'}),
                            className='mb-4'
                        )
                    ),
                    dbc.Row(
                        dbc.Col(
                            html.Div(id='technology-table', className='compact-table',
                                     style={'padding': '5px', 'font-size': '14px'})
                        ),
                        className='m-0'  # Adjusted margin class to decrease size
                    )
                ]
            )
        ],
        ('Stocks',): [
            dbc.Container(
                fluid=True,
                className='p-3',
                children=[
                    dbc.Row(
                        dbc.Col(
                            html.H1('Most Active Stocks', className='text-center mb-4'),
                        )
                    ),
                    dbc.Row(
                        dbc.Col(
                            dbc.Button('Refresh', id='refresh-button', n_clicks=0, color='primary',
                                       className='mx-auto d-block',
                                       style={'width': '200px'}),
                            className='mb-4'
                        )
                    ),
                    dbc.Row(
                        dbc.Col(
                            html.Div(id='output-table'),
                        )
                    )
                ]
            )
        ],
        ('Technology',): [
            dbc.Container(
                fluid=True,
                className='p-3',
                children=[
                    dbc.Row(
                        dbc.Col(
                            html.H1('Technology Stocks', className='text-center mb-4'),
                        )
                    ),
                    dbc.Row(
                        dbc.Col(
                            dbc.Button('Refresh', id='refresh-button', n_clicks=0, color='primary',
                                       className='mx-auto d-block',
                                       style={'width': '200px'}),
                            className='mb-4'
                        )
                    ),
                    dbc.Row(
                        dbc.Col(
                            html.Div(id='technology-table', className='compact-table',
                                     style={'padding': '5px', 'font-size': '14px'})
                        ),
                        className='m-0'  # Adjusted margin class to decrease size
                    )
                ]
            )
        ],
        ('Real Estate',): [
            dbc.Container(
                fluid=True,
                className='p-5',
                children=[
                    dbc.Row(
                        dbc.Col(
                            html.H1('Real Estate Table', className='text-center mb-4'),
                        )
                    ),
                    dbc.Row(
                        dbc.Col(
                            dbc.Button('Refresh', id='refresh-button', n_clicks=0, color='primary',
                                       className='mx-auto d-block', style={'width': '200px'}),
                            className='mb-4'
                        )
                    ),
                    dbc.Row(
                        dbc.Col(
                            html.Div(id='real-estate-table'),
                        )
                    )
                ]
            )
        ],
        ('Crypto',): [
            html.Div([
                dbc.Container(
                    fluid=True,
                    className='p-5',
                    children=[
                        dbc.Row(
                            dbc.Col(
                                html.H1('Crypto Top Gainers', className='text-center mb-4'),
                            )
                        ),
                        dbc.Row(
                            dbc.Col(
                                dbc.Button('Refresh', id='refresh-g_button', n_clicks=0, color='primary',
                                           className='mx-auto d-block',
                                           style={'width': '200px'}),
                                className='mb-4'
                            )
                        ),
                        dbc.Row(
                            dbc.Col(
                                html.Div(id='gainers-table'),
                            )
                        )
                    ]
                ),
                html.Div([
                    dbc.Container(
                        fluid=True,
                        className='p-5',
                        children=[
                            dbc.Row(
                                dbc.Col(
                                    html.H1('Crypto Top Losers', className='text-center mb-4'),
                                )
                            ),
                            dbc.Row(
                                dbc.Col(
                                    dbc.Button('Refresh', id='refresh-l_button', n_clicks=0, color='primary',
                                               className='mx-auto d-block',
                                               style={'width': '200px'}),
                                    className='mb-4'
                                )
                            ),
                            dbc.Row(
                                dbc.Col(
                                    html.Div(id='losers-table'),
                                )
                            )
                        ]
                    )
                ], className="container")
            ])
        ]
    }
    return sections.get(tuple(selected_interests), [html.P("No interests found.")])


# Home Page Layout
home_layout = html.Div([
    generate_navbar(),
    html.H5(id='home-greeting', style={'text-align': 'right'}),
    html.H5("Add Interests"),
    dcc.Dropdown(id='interests-dropdown', options=[
        {'label': 'Stocks', 'value': 'Stocks'},
        {'label': 'Crypto', 'value': 'Crypto'},
        {'label': 'Real Estate', 'value': 'Real Estate'},
        {'label': 'Technology', 'value': 'Technology'}
    ], multi=True, placeholder="Select interests"),
    dbc.Button('Submit', id='add-interests-button', n_clicks=0, style={"margin-top": "10px"}),
    html.Div(id='add-interests-output'),
    html.Div(id='interests-output', style={'text-align': 'center'}),
    html.Div(id='selected-interests-output', style={'text-align': 'center'}),
])

income_layout = html.Div(
    [
        generate_navbar(),
        html.H1("Expense Tracker", className="text-center mt-5 mb-3"),
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.Label("Amount"),
                                        dcc.Input(
                                            id="expense-amount",
                                            type="number",
                                            className="form-control",
                                            placeholder="Enter amount",
                                            min=0
                                        ),
                                    ],
                                    className="mb-3"
                                ),
                                html.Div(
                                    [
                                        html.Label("Category"),
                                        dcc.Input(
                                            id="expense-category",
                                            type="text",
                                            placeholder="Enter category",
                                            className="form-control"
                                        ),
                                    ],
                                    className="mb-3"
                                ),
                                html.Div(
                                    [
                                        html.Label("Date"),
                                        dcc.DatePickerSingle(
                                            id="expense-date",
                                            date=datetime.date.today().isoformat(),
                                            style={'padding': '10px'}
                                        )
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Button(
                                    "Add Expense",
                                    id="add-expense-button",
                                    n_clicks=0,
                                    color="primary",
                                    className="mb-3"
                                ),
                                html.Div(id="expense-output"),
                            ],
                            width={"size": 6, "offset": 3}
                        )
                    ],
                    className="mb-5"
                )
            ]
        ),
        html.H1("Income Tracker", className="text-center mt-4 mb-3"),
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H4("Add Income"),
                                html.Div(
                                    [
                                        html.Label("Amount"),
                                        dcc.Input(
                                            id="a_amount-input",
                                            type="number",
                                            className="form-control",
                                            placeholder="Enter amount",
                                            min=0
                                        ),
                                    ],
                                    className="mb-3"
                                ),
                                html.Div(
                                    [
                                        html.Label("Date"),
                                        dcc.DatePickerSingle(
                                            id="a_date-picker",
                                            date=datetime.date.today().isoformat(),
                                            style={'padding': '10px'}
                                        ),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Button(
                                    "Add Income",
                                    id="add-income-button",
                                    n_clicks=0,
                                    color="primary",
                                    className="mb-3"
                                ),
                                html.Div(id="add-income-output"),
                                ####
                                html.H4("Update Income"),
                                html.Div(
                                    [
                                        html.Label("Income ID"),
                                        dcc.Input(
                                            id="income_id-input",
                                            type="number",
                                            className="form-control",
                                            placeholder="Enter Income ID",
                                            min=0
                                        ),
                                        html.Label("Amount"),
                                        dcc.Input(
                                            id="u_amount-input",
                                            type="number",
                                            className="form-control",
                                            placeholder="Enter amount",
                                            min=0
                                        ),
                                    ],
                                    className="mb-3"
                                ),
                                html.Div(
                                    [
                                        html.Label("Date"),
                                        dcc.DatePickerSingle(
                                            id="u_date-picker",
                                            date=datetime.date.today().isoformat(),
                                            style={'padding': '10px'}
                                        ),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Button(
                                    "Update Income",
                                    id="update-income-button",
                                    n_clicks=0,
                                    color="primary",
                                    className="mb-3"
                                ),
                                html.Div(id="update-income-output"),
                                ####
                                html.H4("Delete Income"),
                                html.Div(
                                    [
                                        html.Label("Income ID"),
                                        dcc.Input(
                                            id="d_income_id-input",
                                            type="number",
                                            className="form-control",
                                            placeholder="Enter Income ID",
                                            min=0
                                        )
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Button(
                                    "Delete Income",
                                    id="delete-income-button",
                                    n_clicks=0,
                                    color="primary",
                                    className="mb-3"
                                ),
                                html.Div(id="delete-income-output"),
                            ],
                            width={"size": 6, "offset": 3}
                        )
                    ],
                    className="mb-5"
                ),
                dbc.Row(
                    dbc.Col(
                        [
                            html.H3('Income History', className='text-center mb-4'),
                            html.Div(id='income-output')
                        ],
                        width={"size": 8, "offset": 2}
                    )
                )
            ],
            className="mt-5"
        )
    ]
)


@app.callback(Output("expense-output", "children"),
              [Input("add-expense-button", "n_clicks")],
              [State("expense-amount", "value"),
               State("expense-category", "value"),
               State("expense-date", "date")])
def add_expense_callback(n_clicks, amount, category, date):
    if n_clicks > 0:
        # Get username from session or wherever it's stored
        username = session.get('username')

        try:
            # Perform validation on input values
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be greater than 0.")

            if not category:
                raise ValueError("Category must be provided.")

            # Call the add_expense function with validated values
            add_expense(username, amount, category, date)
            return html.Div("Expense added successfully.", style={"color": "green"})

        except (ValueError, TypeError) as e:
            return html.Div("Enter valid expense", style={"color": "red"})


@app.callback(Output('income-output', 'children'),
              [Input('url', 'search')])
def display_income(search):
    username = session.get('username')
    if username:
        income_data = get_income(username=username)

        if income_data:
            # Create a table to display the income data
            table_rows = [
                html.Tr([
                    html.Th('ID'),
                    html.Th('Amount'),
                    html.Th('Date')
                ])
            ]

            for row in income_data:
                id, amount, date = row
                table_rows.append(
                    html.Tr([
                        html.Td(id),
                        html.Td(amount),
                        html.Td(date)
                    ])
                )

            return dbc.Table(
                # Set table striped and bordered
                bordered=True,
                striped=True,
                hover=True,
                responsive=True,
                # Set table headers and rows
                children=table_rows
            )
        else:
            return html.P("No income found.")
    else:
        return html.P("No username found in session.")


# Callback for update income
@app.callback(Output('update-income-output', 'children'),
              [Input('update-income-button', 'n_clicks')],
              [State('income_id-input', 'value'),
               State('u_amount-input', 'value'),
               State('u_date-picker', 'date')])
def execute_update_income(n_clicks, income_id, amount, date):
    if n_clicks > 0:
        username = session.get('username')  # Retrieve the username from the session
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be greater than 0.")

            update_income(username, income_id, amount, date)
            return html.Div("Income updated successfully.", style={"color": "green"})

        except (ValueError, TypeError) as e:
            return html.Div("Enter valid details", style={"color": "red"})
    return None


# Callback for delete income
@app.callback(Output('delete-income-output', 'children'),
              [Input('delete-income-button', 'n_clicks')],
              [State('d_income_id-input', 'value')])
def execute_delete_income(n_clicks, income_id):
    if n_clicks > 0:
        username = session.get('username')  # Retrieve the username from the session
        try:
            if income_id < 0:
                raise ValueError("Amount must be greater than 0.")

            delete_income(username, income_id)
            return html.Div("Income deleted successfully.", style={"color": "green"})

        except ValueError as e:
            return html.Div("Enter valid details", style={"color": "red"})
    return None


# Callback for adding income
@app.callback(Output('add-income-output', 'children'),
              [Input('add-income-button', 'n_clicks')],
              [State('a_amount-input', 'value'),
               State('a_date-picker', 'date')])
def execute_add_income(n_clicks, amount, date):
    if n_clicks > 0:
        username = session.get('username')  # Retrieve the username from the session
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be greater than 0.")

            add_income(username, amount, date)
            return html.Div("Income added successfully.", style={"color": "green"})

        except (ValueError, TypeError) as e:
            return html.Div("Enter valid income", style={"color": "red"})
    return None


# Insights Page Layout
insights_layout = html.Div([
    generate_navbar(),
    html.H3("Insights", style={'text-align': 'center', 'margin': '20px'}),
    html.Div(id='insights-output', style={'text-align': 'center'}),
    dcc.Graph(id='pie-chart'),
    html.Div([
        html.H4("Expenses by Category", style={'padding': '20px'}),
        dcc.Graph(id='expenses-chart')
    ]),
    html.Div([
        html.H4("Expenses and Income", style={'padding': '20px'}),
        dcc.Graph(id='m_expenses-chart'),
        dcc.Graph(id='income-chart')
    ])
])


# Callback function to update the expenses chart
@app.callback(Output('expenses-chart', 'figure'), [Input('url', 'search')])
def update_expenses_chart(search):
    username = session.get('username')
    if username:
        expenses = get_all_expenses(username)

        # Create a dataframe from the expenses data
        df_expenses = pd.DataFrame(expenses, columns=['ID', 'Amount', 'Category', 'Date'])

        # Group expenses by category and calculate the total amount
        category_expenses = df_expenses.groupby('Category')['Amount'].sum().sort_values(ascending=False).reset_index()

        # Create a pie chart of expenses by category using Plotly Express
        fig = px.pie(category_expenses, values='Amount', names='Category',
                     title='Total Expenses by Category')

        return fig
    else:
        return {}


# Callback function to update the expenses chart
@app.callback(Output('m_expenses-chart', 'figure'), [Input('url', 'search')])
def update_m_expenses_chart(search):
    username = session.get('username')
    if username:
        expenses = get_all_expenses(username)

        # Create a dataframe from the expenses data
        df_expenses = pd.DataFrame(expenses, columns=['ID', 'Amount', 'Category', 'Date'])

        # Convert the date column to datetime format
        df_expenses['Date'] = pd.to_datetime(df_expenses['Date'])

        # Group expenses by date and calculate the total amount
        daily_expenses = df_expenses.groupby('Date')['Amount'].sum().reset_index()

        # Create a line plot of expenses by date using Plotly Express
        fig = px.line(daily_expenses, x='Date', y='Amount', labels={'Date': 'Date', 'Amount': 'Expenses'},
                      title='Expenses by Date')

        return fig
    else:
        return {}


# Callback function to update the income chart
@app.callback(Output('income-chart', 'figure'), [Input('url', 'search')])
def update_income_chart(search):
    username = session.get('username')
    if username:
        income = get_income(username)
        df_income = pd.DataFrame(income, columns=['ID', 'Amount', 'Date'])
        df_income['Date'] = pd.to_datetime(df_income['Date'])
        monthly_income = df_income.groupby(df_income['Date'].dt.to_period('M')).sum(numeric_only=True)['Amount']

        # Convert Period object to string for plotting
        monthly_income.index = monthly_income.index.astype(str)

        # Create a line plot of income by month using Plotly Express
        fig = px.line(x=monthly_income.index, y=monthly_income, labels={'x': 'Date (Year-Month)', 'y': 'Income'},
                      title='Monthly Income')

        return fig
    else:
        return {}


# Callback function to retrieve and display insights
@app.callback(Output('insights-output', 'children'), [Input('url', 'search')])
def display_insights(search):
    username = session.get('username')
    if username:
        db_name = f"{username}.db"
        conn = sqlite3.connect(db_name)

        # Retrieve data from income table
        income_query = "SELECT * FROM income"
        df_income = pd.read_sql_query(income_query, conn)
        total_income = df_income['amount'].sum()

        # Retrieve data from expenses table
        expenses_query = "SELECT * FROM expenses"
        df_expenses = pd.read_sql_query(expenses_query, conn)
        total_expenses = df_expenses['amount'].sum()

        conn.close()

        # Calculate balance and expenditure percentage
        balance = total_income - total_expenses
        expenditure_percent = (total_expenses / total_income) * 100

        # Print other insights
        insights_text = [
            html.P(f"Balance: {balance}"),
            html.P(f"Total Expenditure: {total_expenses}"),
            html.P(f"Expenditure is {round(expenditure_percent, 2)}%")
        ]

        return insights_text
    else:
        return html.P("No username found in session.")


# Callback function to update the pie chart
@app.callback(Output('pie-chart', 'figure'), [Input('url', 'search')])
def update_pie_chart(search):
    username = session.get('username')
    if username:
        db_name = f"{username}.db"
        conn = sqlite3.connect(db_name)

        # Retrieve data from income table
        income_query = "SELECT * FROM income"
        df_income = pd.read_sql_query(income_query, conn)
        total_income = df_income['amount'].sum()

        # Retrieve data from expenses table
        expenses_query = "SELECT * FROM expenses"
        df_expenses = pd.read_sql_query(expenses_query, conn)
        total_expenses = df_expenses['amount'].sum()

        conn.close()

        # Create a bar chart of total income and expenses
        df_insights = pd.DataFrame({'Category': ['Income', 'Expenses'], 'Amount': [total_income, total_expenses]})
        # Set custom colors for the bars
        colors = ['#1f77b4', '#ff7f0e']  # Blue for income, orange for expenses

        fig = px.bar(df_insights, x='Category', y='Amount', labels={'Amount': 'Amount', 'Category': 'Category'},
                     title='Total Income vs Total Expenses', color='Category', color_discrete_sequence=colors)

        return fig
    else:
        return {}


# Savings Page Layout
savings_layout = html.Div([
    generate_navbar(),
    html.H2("Savings", style={'text-align': 'center', 'margin': '20px'}),
    html.Div([
        dcc.Graph(id='savings-chart')
    ])
])


# Callback function to update the savings chart
@app.callback(Output('savings-chart', 'figure'), [Input('url', 'search')])
def update_savings_chart(search):
    username = session.get('username')
    if username:
        savings = get_all_savings(username=username)
        # Create a dataframe from the expenses data
        df_savings = pd.DataFrame(savings, columns=['ID', 'Amount', 'Date'])

        # Convert the date column to datetime format
        df_savings['Date'] = pd.to_datetime(df_savings['Date'])

        # Create a line plot of expenses by date using Plotly Express
        fig = px.line(df_savings, x='Date', y='Amount', labels={'Date': 'Date', 'Amount': 'Savings'},
                      title='Savings by Date')
        return fig
    else:
        return {}


def get_crypto_news():
    url = 'https://www.bing.com/news/search?q=Latest+Cryptocurrency&qpvt=latest+cryptocurrency+news+today&FORM=EWRE'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    news = []

    for card in soup.find_all('div', class_='news-card newsitem cardcommon'):
        news_item = {}

        try:
            img_tag = card.find('div', {'class': 'image right'})
            if img_tag and img_tag.find('img'):
                img_url = img_tag.find('img')['src']
                img_url = "http://www.bing.com" + img_url
                news_item['img_url'] = img_url

            title_tag = card.find('a', class_='title')
            if title_tag:
                title = title_tag.text.strip()
                link = title_tag['href']
                news_item['title'] = title
                news_item['link'] = link

            div_tag = card.find('div', class_='snippet')
            if div_tag:
                div_data = div_tag.text.strip()
                news_item['div_data'] = div_data

            news.append(news_item)

        except Exception as e:
            print(f"Error occurred while processing a news card: {e}")

    return news


def scrape_news(url):
    # Function to scrape news data
    # Replace with your own implementation
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    each_stories = soup.select('div.tabdata div.eachStory')

    news_data = []

    for story in each_stories:
        img = story.find('img')['data-original']
        h3 = story.find('h3').text.strip()
        p = story.find('p').text.strip()
        link = story.find('a')['href']
        full_link = urljoin(url, link)  # Append base URL to the extracted link

        news_item = {
            'title': h3,
            'image': img,
            'content': p,
            'link': full_link
        }

        news_data.append(news_item)

    return news_data


def create_stock_news_cards(news_data):
    # Function to create news cards
    # Replace with your own implementation
    news_cards = []

    for news in news_data:
        news_card = dbc.Card(
            className='news-card',
            children=[
                dbc.Row(
                    children=[
                        dbc.Col(
                            width=12,
                            children=[

                                dbc.CardImg(src=news['image'], top=True, style={'max-width': '300px'}),

                                dbc.CardBody(
                                    [
                                        html.H4(news['title'], className="card-title"),
                                        html.P(news['content'], className="card-text"),
                                        dbc.Button("Read More", href=news['link'], color="primary", target="_blank"),
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ]
        )
        news_cards.append(news_card)

    return news_cards


def create_news_cards(news):
    cards = []
    for item in news:
        card = dbc.Card(
            className='news-card',
            children=[
                dbc.Row(
                    children=[
                        dbc.Col(
                            width=8,
                            children=[
                                dbc.CardBody(
                                    children=[
                                        html.H5(item.get('title', ''), className='news-title'),
                                        html.P(item.get('div_data', ''), className='news-description'),
                                        dbc.Button('Read More', href=item.get('link', ''), color='primary',
                                                   className='read-more-button')
                                    ]
                                )
                            ]
                        ),
                        dbc.Col(
                            width=4,
                            children=[
                                dbc.CardImg(src=item.get('img_url', ''), top=True, style={'max-width': '300px'})
                            ]
                        )
                    ]
                )
            ]
        )

        cards.append(card)
    return cards


# News Page Layout
news_layout = html.Div([
    generate_navbar(),
    # Add savings-related components and callbacks here
    dbc.Container(
        className='crypto-news-container',
        children=[
            html.Div(
                className='jumbotron-fluid',
                children=[
                    dbc.Container(
                        className='container text-center',
                        children=[
                            html.H2("Cryptocurrency News"),
                            html.P("Stay updated with the latest news on cryptocurrencies.")
                        ]
                    )
                ]
            ),
            dbc.Spinner(
                dbc.Row(
                    id='news-cards',
                    className='news-cards-row justify-content-center align-items-center',
                    children=create_news_cards(get_crypto_news())
                ),
                color="primary",
                fullscreen=True,
            )
        ]
    ),
    html.Div([
        dbc.Container(
            className='stocks-news-container',
            children=[
                html.Div(
                    className='jumbotron-fluid',
                    children=[
                        dbc.Container(
                            className='container text-center',
                            children=[
                                html.H2("Stocks News")
                            ]
                        )
                    ]
                ),
                dbc.Spinner(
                    dbc.Row(
                        id='news-cards',
                        className='news-cards-row justify-content-center align-items-center',
                        children=create_stock_news_cards(
                            scrape_news("https://economictimes.indiatimes.com/markets/stocks/news"))
                    ),
                    color="primary",
                    fullscreen=True,
                )
            ]
        )
    ], className="container")
])

# Stock Volatility Page Layout
stocks_layout = html.Div([
    generate_navbar(),
    html.H4("Stock Volatility Prediction", style={'text-align': 'center', 'margin': '20px'}),
    # stock volatility components
    html.Div(style={'margin': 'auto'}, children=[
        html.Div(
            style={'display': 'flex', 'flex-direction': 'row', 'justify-content': 'center', 'align-items': 'center'},
            children=[
                html.Label("Ticker Symbol", style={'margin-right': '10px'}),
                dcc.Input(id="ticker-input", type="text", placeholder="COMPANY.BSE", className='input-field')
            ]
        ),
        html.Div(
            style={'display': 'flex', 'flex-direction': 'row', 'justify-content': 'center', 'padding': '20px'},
            children=[
                dbc.Button("Fit", id="fit-button", n_clicks=0, color="primary", className="action-button"),
            ]
        ),
        html.Div(
            style={'display': 'flex', 'flex-direction': 'row', 'justify-content': 'center', 'align-items': 'center'},
            children=[
                html.Label("Number of Days to Predict", style={'margin-right': '10px'}),
                dcc.Input(id="days-input", type="number", min=1, step=1, className='input-field'),
            ]
        ),
        html.Div(
            style={'display': 'flex', 'flex-direction': 'row', 'justify-content': 'center', 'padding': '20px'},
            children=[
                dbc.Button("Predict", id="predict-button", n_clicks=0, color="primary", className="action-button"),
            ]
        ),

        html.Div(id="prediction-output"),
        dcc.Graph(id="prediction-graph", style={'margin-top': '30px'})
    ])
])


@app.callback(
    dash.dependencies.Output("prediction-output", "children"),
    [dash.dependencies.Input("fit-button", "n_clicks")],
    [dash.dependencies.State("ticker-input", "value")]
)
def fit_data(n_clicks, ticker):
    if n_clicks > 0:
        # URL of `/fit` path
        url_fit = "http://localhost:8008/fit"

        # Data to send for fitting
        json_fit = {
            "ticker": ticker,
            "use_new_data": True,
            "n_observations": 2000,
            "p": 1,
            "q": 1
        }

        # Make API request for fitting
        response_fit = requests.post(url_fit, json=json_fit)

        return html.Div(f"Data fitted for {ticker}.", style={"color": "green"})


# Callback function to update the graph based on user input
@app.callback(
    dash.dependencies.Output("prediction-graph", "figure"),
    [dash.dependencies.Input("predict-button", "n_clicks")],
    [dash.dependencies.State("ticker-input", "value"),
     dash.dependencies.State("days-input", "value")]
)
def update_graph(n_clicks, ticker, num_days):
    if n_clicks > 0:
        # URL of `/predict` path
        url = "http://localhost:8008/predict"

        # Data to send to path
        json = {"ticker": ticker, "n_days": num_days}

        # Response of post request
        response = requests.post(url=url, json=json)

        # Response JSON
        submission = response.json()

        # Create a DataFrame from the response data
        df = pd.DataFrame.from_dict(submission, orient="columns")

        # Create the line plot using Plotly Express
        fig = px.line(df, x=df.index, y="forecast", title=f"Volatility Prediction For {ticker}")

        # Customize the layout of the plot
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Volatility Rate",
            xaxis_tickangle=0,
            showlegend=False,
            plot_bgcolor="white",
            yaxis=dict(gridcolor='lightgray'),  # Add horizontal grid lines
            xaxis=dict(gridcolor='lightgray'),  # Add vertical grid lines
            hovermode='x'  # Display only the x-axis value on hover
        )

        fig.update_traces(line=dict(color='blue', width=2))

        return fig
    return {}


# Update the callback to display different pages based on the URL
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if 'username' in session:  # Check if the user session exists
        if pathname == '/home':
            return home_layout
        elif pathname == '/income':
            return income_layout
        elif pathname == '/expenses':
            return insights_layout
        elif pathname == '/savings':
            return savings_layout
        elif pathname == '/news':
            return news_layout
        elif pathname == '/stocks':
            return stocks_layout
    if pathname == '/login':
        return login_layout
    elif pathname == '/register':
        return register_layout
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
            session['username'] = username  # Store the username in the session
            create_database(username=username)
            return dcc.Location(href='/home', id='login-success')
        else:
            return html.Div("Invalid username or password.", style={"color": "red"})


@app.server.route('/logout')
def logout():
    session.clear()  # Clear the user session
    return flask.redirect('/login')


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
            # dcc.Location(href='/login', id='register-success')
            return "Registration successful. Please log in."
        except ValueError as e:
            return str(e)  # Display the error message

    return None


# Callback for add interests button
@app.callback(Output('add-interests-output', 'children'),
              [Input('add-interests-button', 'n_clicks')],
              [State('url', 'pathname'),
               State('interests-dropdown', 'value')])
def add_interests_to_user(n_clicks, search, interests):
    if n_clicks > 0 and search:
        username = session.get('username')
        if username and interests:
            add_interests(username, interests)
            return html.Div("Interests added successfully.", style={"color": "green"})
        else:
            return html.Div("Invalid request.", style={"color": "red"})
    return ""


@app.callback(Output('home-greeting', 'children'),
              [Input('url', 'search')])
def display_greeting(search):
    username = session.get('username')
    return html.H5(f"Username: {username}")


@app.callback(Output('interests-output', 'children'),
              [Input('url', 'pathname')])
def display_interests(pathname):
    username = session.get('username', '')
    interests = get_interests(username)
    if interests:
        return html.P(f"Interests: {', '.join(interests)}")
    else:
        return html.P("No interests found.")


if __name__ == '__main__':
    app.run_server(debug=True, port=8051, host='127.0.0.1')
