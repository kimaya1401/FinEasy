import sqlite3

from config import settings
from data import SQLRepository
from fastapi import FastAPI
from model import GarchModel
from pydantic import BaseModel
import requests
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
import secrets


# Task 8.4.14, `FitIn` class
class FitIn(BaseModel):
    ticker: str
    use_new_data: bool
    n_observations: int
    p: int
    q: int


# Task 8.4.14, `FitOut` class
class FitOut(FitIn):
    success: bool
    message: str


# Task 8.4.18, `PredictIn` class
class PredictIn(BaseModel):
    ticker: str
    n_days: int


# Task 8.4.18, `PredictOut` class
class PredictOut(PredictIn):
    success: bool
    forecast: dict
    message: str


# Task 8.4.15
def build_model(ticker, use_new_data):
    # Create DB connection
    connection = sqlite3.connect(settings.db_name, check_same_thread=False)

    # Create `SQLRepository`
    repo = SQLRepository(connection=connection)

    # Create model
    model = GarchModel(ticker=ticker, use_new_data=use_new_data, repo=repo)

    # Return model
    return model


# Task 8.4.9
app = FastAPI()

API_KEY = secrets.token_urlsafe(32)
print(API_KEY)


# Define a route that requires API key authentication
@app.get("/protected-route")
async def protected_route(api_key: str):
    """
    This is a protected route that requires an API key.

    Args:
        api_key (str): The API key for authentication.

    Returns:
        dict: A response message indicating whether access is granted or not.
    """
    if api_key == API_KEY:
        return {"message": "Access granted! This is a protected route."}
    else:
        return {"message": "Invalid API key. Access denied."}


# Generate the API documentation
@app.get("/docs", response_class=HTMLResponse)
async def custom_swagger_ui_html():
    """
    Custom Swagger UI HTML page that includes the API key.

    Returns:
        HTMLResponse: The Swagger UI HTML page.
    """
    openapi_url = app.openapi_url
    title = app.title or "FastAPI"
    html_content = get_swagger_ui_html(openapi_url=openapi_url, title=title)
    # Add the API key to the Swagger UI HTML page
    api_key_info = f"<h4>API Key:</h4><pre>{API_KEY}</pre>"
    html_content = html_content.replace("</head>", f"{api_key_info}</head>")
    return HTMLResponse(content=html_content)


# Generate the OpenAPI schema
def custom_openapi():
    """
    Custom OpenAPI schema that includes the API key.

    Returns:
        dict: The OpenAPI schema.
    """
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    # Add the API key to the OpenAPI schema
    security_scheme = {
        "API Key": {
            "type": "apiKey",
            "name": "api_key",
            "in": "query",
        }
    }
    openapi_schema["components"]["securitySchemes"] = security_scheme
    return openapi_schema


app.openapi = custom_openapi


@app.post("/fit", status_code=200, response_model=FitOut)
# Task 8.4.16, `"/fit" path, 200 status code
def fit_model(request: FitIn):
    """Fit model, return confirmation message.

    Parameters
    ----------
    request : FitIn

    Returns
    ------
    dict
        Must conform to `FitOut` class
    """
    # Create `response` dictionary from `request`
    response = request.dict()

    # Create try block to handle exceptions
    try:
        # Build model with `build_model` function
        model = build_model(ticker=request.ticker, use_new_data=request.use_new_data)
        # Wrangle data
        model.wrangle_data(n_observations=request.n_observations)
        # Fit model
        model.fit(p=request.p, q=request.q)
        # Save model
        file_name = model.dump()
        # Add `"success"` key to `response`
        response["success"] = True
        # Add `"message"` key to `response` with `filename`
        response["message"] = f"Trained and saved '{file_name}'."
    # Create except block
    except Exception as e:
        # Add `"success"` key to `response`
        response["success"] = False
        # Add `"message"` key to `response` with error message
        response["message"] = str(e)
    # Return response
    return response


@app.post("/predict", status_code=200, response_model=PredictOut)
# Task 8.4.19 `"/predict" path, 200 status code
def get_prediction(request: PredictIn):
    # Create `response` dictionary from `request`
    response = request.dict()
    # Create try block to handle exceptions
    try:
        # Build model with `build_model` function
        model = build_model(ticker=request.ticker, use_new_data=False)
        # Load stored model
        model.load()
        # Generate prediction
        prediction = model.predict_volatility(horizon=request.n_days)
        # Add `"success"` key to `response`
        response["success"] = True
        # Add `"forecast"` key to `response`
        response["forecast"] = prediction
        # Add `"message"` key to `response`
        response["message"] = ""
    # Create except block
    except Exception as e:
        # Add `"success"` key to `response`
        response["success"] = False
        # Add `"forecast"` key to `response`
        response["forecast"] = {}
        #  Add `"message"` key to `response`
        response["message"] = str(e)
    # Return response
    return response