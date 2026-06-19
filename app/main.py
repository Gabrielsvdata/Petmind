from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routes import pets

# Carrega variáveis de ambiente
load_dotenv()

# Cria as tabelas no banco de dados
Base.metadata.create_all(bind=engine)

# Instância principal da aplicação
app = FastAPI(
    title="PetMind",
    description="Registro de comportamentos e rotinas de pets com IA",
    version="0.1.0",
)

# CORS — permite requisições do frontend Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra os roteadores
app.include_router(pets.roteador)


@app.get("/")
async def raiz() -> dict[str, str]:
    """Endpoint raiz da aplicação."""
    return {"mensagem": "Bem-vindo ao PetMind!"}


@app.get("/health")
async def verificacao_saude() -> dict[str, str]:
    """Verificação de saúde da aplicação."""
    return {"status": "ok"}
