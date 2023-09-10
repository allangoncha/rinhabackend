from src.app import app
from fastapi import Response
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import insert, create_engine, text
import os, uuid

#Load Env's
load_dotenv()
HOST = os.environ.get("host")
PORT = os.environ.get("port")
USER = os.environ.get("user")
PASS = os.environ.get("pass")
DBNAME = os.environ.get("dbname")

#DB Connection
SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASS}@{HOST}:{PORT}/{DBNAME}"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, pool_size=10
)

conn = engine.connect()

#Models
class Pessoas(BaseModel):
    apelido: str
    nome: str 
    nascimento: str #AAAA-MM-DD
    stack: Optional[List[str]]

@app.post("/pessoas", response_model=Pessoas, status_code = 201)
def pessoas(pessoas: Pessoas, response: Response):
    id_pessoas = uuid.uuid4()

    if pessoas.stack != None:
        stack_array = "{" + ",".join(pessoas.stack) + "}"
    else:
        stack_array = 'null'

    try:
        insert_pessoas = f"""
        INSERT INTO public.pessoas
        (id, apelido, nome, nascimento, stack)
        VALUES('{id_pessoas}', '{pessoas.apelido}', '{pessoas.nome}', '{pessoas.nascimento}', '{stack_array}');
        """
        conn.execute(text(insert_pessoas))
        conn.commit()

        headers = {"Location": f'pessoas/{id_pessoas}'}
        content = "Hello, world!"
        
        return JSONResponse(content=content, headers=headers)

    except Exception as e:
        return {
                "Exception": {e}
                }
