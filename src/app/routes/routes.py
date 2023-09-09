from src.app import app
from dotenv import load_dotenv
from pydantic import BaseModel
import psycopg2, os

@app.get("/")
def hello():
    return {"Message": "Hello, World!"}