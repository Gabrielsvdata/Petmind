import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import Base, engine
from app.models import pet, user  # noqa: F401
from app.routes import auth, pets

# Carrega variáveis de ambiente
load_dotenv()

# Cria as tabelas no banco de dados
Base.metadata.create_all(bind=engine)

# Compatibilidade com banco antigo sem owner_id
with engine.connect() as conn:
    conn.execute(text("ALTER TABLE pets ADD COLUMN IF NOT EXISTS owner_id INTEGER"))
    conn.execute(
        text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.table_constraints
                    WHERE constraint_name = 'fk_pets_owner_id_usuarios'
                ) THEN
                    ALTER TABLE pets
                    ADD CONSTRAINT fk_pets_owner_id_usuarios
                    FOREIGN KEY (owner_id) REFERENCES usuarios(id);
                END IF;
            END $$;
            """
        )
    )
    conn.commit()

# Instância principal da aplicação
app = FastAPI(
    title="PetMind",
    description="Registro de comportamentos e rotinas de pets com IA",
    version="0.1.0",
)

origens_permitidas = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

origens_env = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
if origens_env:
    origens_permitidas.extend(
        origem.strip().rstrip("/")
        for origem in origens_env.split(",")
        if origem.strip()
    )

frontend_url = os.getenv("FRONTEND_URL", "").strip()
if frontend_url:
    origens_permitidas.append(frontend_url.rstrip("/"))

# Remove duplicidades preservando ordem.
origens_permitidas = list(dict.fromkeys(origens_permitidas))

# CORS — permite requisições do frontend Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=origens_permitidas,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra os roteadores
app.include_router(auth.roteador)
app.include_router(pets.roteador)


@app.get("/")
async def raiz() -> dict[str, str]:
    """Endpoint raiz da aplicação."""
    return {"mensagem": "Bem-vindo ao PetMind!"}


@app.get("/health")
async def verificacao_saude() -> dict[str, str]:
    """Verificação de saúde da aplicação."""
    return {"status": "ok"}
