from src.app import app

@app.get("/")
def hello():
    return {"Message": "Hello, World!"}