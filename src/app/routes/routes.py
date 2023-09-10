from src.app import app
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional
import psycopg2, os

#Load Env's
load_dotenv()
HOST = os.environ.get("host")
PORT = os.environ.get("port")
USER = os.environ.get("user")
PASS = os.environ.get("pass")
DBNAME = os.environ.get("dbname")

#DB Connection
conn = psycopg2.connect(host=HOST, port=PORT, user=USER, password=PASS, dbname=DBNAME)
cur = conn.cursor()

#Models
class Pessoas(BaseModel):
    apelido: str
    nome: str 
    nascimento: str #AAAA-MM-DD
    stack: Optional[List[str]]

@app.post("/pessoas", response_model=Pessoas)
def pessoas(pessoas: Pessoas):
    return {"apelido": pessoas.apelido,
            "nome": pessoas.nome,
            "nascimento": pessoas.nascimento,
            "stack": pessoas.stack
            }
