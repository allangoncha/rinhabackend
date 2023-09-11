from src.app import app
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, text
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

@app.post("/pessoas")
async def pessoas(pessoas: Pessoas):
    id_pessoas = uuid.uuid4()

    if pessoas.stack != None:
        stack_array = "{" + ",".join(pessoas.stack) + "}"
    else:
        stack_array = 'null'
        
    select_pessoas = f"SELECT apelido from public.pessoas where apelido = '{pessoas.apelido}'"
    select_response = conn.execute(text(select_pessoas)).fetchone()
        
    if select_response:
        return JSONResponse(content="Apelido já existente na base.", status_code=422)

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
        
        return JSONResponse(content=content, headers=headers, status_code=201)
        
    except Exception as e:
        return {
                "Exception": {e}
                }

@app.get("/pessoas/{id_pessoa}")
async def searchPessoasById(id_pessoa: str):
    select_idpessoa = f"SELECT * from public.pessoas where id = '{id_pessoa}'"
    select_response = conn.execute(text(select_idpessoa)).fetchall()
    
    if bool(select_response):
        
        for row in select_response:
            
            if row[4] == 'null':
                stack = None
            else:
                #Clean Stack and convert to list using split()
                cleaned_stack = row[4].strip('{}')
                stack = cleaned_stack.split(',')
            
            response = {
                        "id" : row[0],
                        "apelido" : row[1],
                        "nome" : row[2],
                        "nascimento" : row[3],
                        "stack" : stack
                    }
    
            return JSONResponse(content=response, status_code=200)
    
    
    return JSONResponse(content=response, status_code=404)