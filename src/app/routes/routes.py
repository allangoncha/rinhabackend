from src.app import app
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional, Any
from sqlalchemy import create_engine, text
import os, uuid, redis, re, json

#Load Env's
load_dotenv()
HOST = os.environ.get("host")
PORT = os.environ.get("port")
USER = os.environ.get("user")
PASS = os.environ.get("pass")
DBNAME = os.environ.get("dbname")
R_HOST = os.environ.get("r_host")
R_PORT = os.environ.get("r_port")

#Redis config
pool = redis.ConnectionPool(host=R_HOST, port=R_PORT, db=0)
redis = redis.Redis(connection_pool=pool)

#DB Connection
SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASS}@{HOST}:{PORT}/{DBNAME}"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, pool_size=1000
)

conn = engine.connect()

#Models
class Pessoas(BaseModel):
    apelido: Any
    nome: Any
    nascimento: str #AAAA-MM-DD
    stack: Optional[List]

class Pessoa(BaseModel):
    id: str
    apelido: str
    nome: str 
    nascimento: str #AAAA-MM-DD
    stack: Optional[List[str]]

@app.post("/pessoas")
async def pessoas(pessoas: Pessoas):
    id_pessoas = uuid.uuid4()

    #Validations
    if pessoas.stack != None:
        for i in pessoas.stack:
            if isinstance(i, int):
                return JSONResponse(content=f"Elemento da stack deve ser string e não inteiro.", status_code=400)        
            
            if len(i) > 32:
                return JSONResponse(content=f"Elemento da stack excede o tamanho máximo de 32 caracteres.", status_code=400)        
        
        stack_array = "{" + ",".join(pessoas.stack) + "}"
        
    else:
        stack_array = 'null'
    if isinstance(pessoas.apelido, int):
        return JSONResponse(content="Apelido deve ser do tipo string.", status_code=400)
    
    if pessoas.apelido == None:
        return JSONResponse(content="Apelido deve ser diferente de null.", status_code=422)
    
    if len(pessoas.apelido) > 32:
        return JSONResponse(content="Apelido excede o tamanho máximo de 32 caracteres.", status_code=400)
    
    if isinstance(pessoas.nome, int):
        return JSONResponse(content="Nome deve ser do tipo string.", status_code=400)
    
    if pessoas.nome == None:
        return JSONResponse(content="Nome deve ser diferente de null.", status_code=422)
    
    if len(pessoas.nome) > 100 or isinstance(pessoas.nome, int):
        return JSONResponse(content="Nome excede o tamanho máximo de 100 caracteres.", status_code=400)
    
    regex = re.compile('^\d{4}-\d{2}-\d{2}$')
    if bool(regex.match(pessoas.nascimento)) == False:
        return JSONResponse(content="Formato do campo nascimento diferente de AAAA-MM-DD", status_code=400)
    
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

        redis.set(f'{id_pessoas}', 
            str({   
            "id": str(id_pessoas), 
            "apelido": pessoas.apelido, 
            "nome": pessoas.nome, 
            "nascimento": pessoas.nascimento, 
            "stack": stack_array
                    }
                )
            )

        headers = {"Location": f'pessoas/{id_pessoas}'}
        content = "Hello, world!"
        
        return JSONResponse(content=content, headers=headers, status_code=201)
        
    except Exception as e:
        return JSONResponse(content={"Exception": f'{e}'}, status_code=422)

@app.get("/pessoas/{id_pessoa}", response_model=Pessoa)
async def searchPessoasById(id_pessoa: str):
    select_idpessoa = f"SELECT * from public.pessoas where id = '{id_pessoa}'"
    select_response = conn.execute(text(select_idpessoa)).fetchall()
    
    #Redis Validation
    if redis.exists(f'{id_pessoa}'):
        response = json.loads(redis.get(f'{id_pessoa}').decode().replace("'", '"'))
    
        if response['stack'] == 'null':
                response['stack'] = None
                
        return JSONResponse(content=response, status_code=200)

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
    
    return JSONResponse(content='Not Found', status_code=404)

@app.get("/pessoas")
async def searchPessoasByterm(t: str = None):
    select_termobusca = f"SELECT * from public.pessoas where busca_trgm like '%{t.lower()}%' limit 50;"
    select_response = conn.execute(text(select_termobusca)).fetchall()
    
    if t != "":
        
        if len(select_response) == 0:
            return JSONResponse(content=[], status_code=200)
        
        else:    
            response_list = []
            
            for pessoa in select_response:
                id_pessoa = pessoa[0]
                apelido = pessoa[1]
                nome = pessoa[2]
                nascimento = pessoa[3]
                stack = pessoa[4]
                
                pessoa = {
                    "id": id_pessoa,
                    "apelido": apelido,
                    "nome": nome,
                    "nascimento": nascimento,
                    "stack": stack,
                }
                
                response_list.append(pessoa)
            
            
        return JSONResponse(content=response_list, status_code=200)
    else:
        return JSONResponse(content="Valor de t não pode ser vazio.", status_code=400)

@app.get('/contagem-pessoas')
def contagemPessoas():
    select_count = "select count(id) from public.pessoas;"
    select_response = conn.execute(text(select_count)).fetchone()

    return JSONResponse(content={"Count" : f"{select_response[0]}" }, status_code=200)