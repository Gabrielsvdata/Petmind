# PetMind

API REST para registro de comportamentos e rotinas de pets com análise de IA.  
Construída com **FastAPI + PostgreSQL + Groq** para a **World Code Cup**.  
Deploy: **Docker + Google Cloud Run**, banco **Postgres (Neon)**.

---

## Stack

- Python 3.11+ · FastAPI 0.115+ · SQLAlchemy 2.0 · Pydantic v2
- PostgreSQL 17 · Groq SDK (LLM)

---

## Configuração local

```bash
# 1. PostgreSQL — criar usuário e bancos (executar uma vez)
psql -U postgres -c "CREATE USER petmind WITH PASSWORD 'petmind123';"
psql -U postgres -c "CREATE DATABASE petmind OWNER petmind;"
psql -U postgres -c "CREATE DATABASE petmind_test OWNER petmind;"
psql -U postgres -c "ALTER USER petmind CREATEDB;"

# 2. Projeto
python -m venv .venv
.venv\Scripts\activate          # Linux/Mac: source .venv/bin/activate
pip install -e ".[dev]"         # dependências base + dev
pip install -e ".[ia]"          # dependências de IA (Groq)
cp .env.example .env            # preencher GROQ_API_KEY no .env

# 3. Servidor
python -m uvicorn app.main:app --reload
# Docs: http://127.0.0.1:8000/docs
```

---

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Raiz |
| GET | `/health` | Health check |
| POST | `/pets/` | Cadastrar pet |
| GET | `/pets/` | Listar pets |
| GET | `/pets/{id}` | Buscar pet |
| POST | `/pets/{id}/registros` | Adicionar registro de comportamento |
| GET | `/pets/{id}/registros` | Listar registros do pet |
| GET | `/pets/{id}/registros/ultimo` | Último registro com estado emocional |
| POST | `/pets/{id}/analisar` | Análise de comportamento via IA (Groq) |
| POST | `/auth/login` | Login (devolve token) |
| POST | `/auth/login-demo` | Login de visitante (com `DEMO_MODE=true`) |
| GET | `/auth/me` | Usuário do token |

---

## Estrutura

```
app/
├── main.py              # Entrypoint FastAPI + CORS
├── database/__init__.py # Engine, sessão, Base
├── models/pet.py        # ORM: Pet, RegistroComportamento
├── schemas/pet.py       # Pydantic: request/response schemas
├── routes/pets.py       # Todos os endpoints /pets
└── services/
    ├── emocao_service.py # Cálculo do estado emocional (lógica pura)
    └── groq_service.py  # Integração com Groq API
tests/
└── test_pets.py         # 18 testes (Fase 1 + Fase 2)
```

---

## Qualidade de código

```bash
python -m ruff check .           # Lint
python -m ruff format --check .  # Formatação
python -m mypy app/              # Typecheck (strict)
python -m pytest                 # Testes
```

---

## Migrations (Alembic)

Usar Alembic para versionamento seguro do schema do banco:

```bash
# Criar nova migration (autogenera mudanças)
python -m alembic revision --autogenerate -m "descrição"

# Aplicar todas as migrations pendentes
python -m alembic upgrade head

# Desfazer última migration
python -m alembic downgrade -1

# Ver histórico de migrations
python -m alembic history
```

**Nota:** As migrations são geradas automaticamente ao comparar o schema SQLAlchemy com o banco. Sempre revise a migration gerada antes de aplicar em produção.

---

## Autenticação

- `POST /auth/login` devolve um **token de acesso (JWT)**, válido por 8 h por padrão.
- As rotas de pets e admin exigem `Authorization: Bearer <token>`.
- `GET /auth/me` retorna o usuário do token.
- A senha não trafega nem fica guardada no navegador depois do login.
- Criar admin pela tela (`/auth/register-admin`) fica **desligado por padrão**
  (`ENABLE_ADMIN_BOOTSTRAP=true` só em ambiente de teste).

## Análise com IA

Os números da análise são calculados em Python, com regras fixas: médias, tendências,
estado predominante, confiança e alertas. A IA (Groq) só escreve o diagnóstico e a
recomendação em texto. Assim, os mesmos registros geram sempre os mesmos números,
e se a IA estiver fora do ar a análise continua funcionando com um texto padrão.

## Modo demonstração

Com `DEMO_MODE=true`, a API cria na subida duas contas de visitante (tutor e admin),
outros tutores, pets e uma semana de registros, e libera:

```
POST /auth/login-demo   {"perfil": "usuario" | "admin"}
```

As contas de demonstração não podem ser removidas nem ter o papel alterado.
Para recriar os dados: `python -m app.seeds.demo_seed --reset`.

## Deploy no Google Cloud Run

A API roda num container (veja o `Dockerfile`). Na subida, as migrations do Alembic
são aplicadas automaticamente. O banco é um Postgres gerenciado (ex.: Neon).

```bash
gcloud run deploy petmind-api \
  --source . \
  --region southamerica-east1 \
  --allow-unauthenticated \
  --set-env-vars DEMO_MODE=true,CORS_ALLOW_ORIGINS=https://petmind.pages.dev \
  --set-secrets SECRET_KEY=petmind-secret-key:latest,DATABASE_URL=petmind-database-url:latest,GROQ_API_KEY=petmind-groq-key:latest
```

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `DATABASE_URL` | sim | Postgres (Neon: com `?sslmode=require`) |
| `SECRET_KEY` | sim em produção | Assina os tokens de login |
| `GROQ_API_KEY` | para IA | Texto da análise de comportamento |
| `CORS_ALLOW_ORIGINS` | não | Origens extras do front, separadas por vírgula |
| `DEMO_MODE` | não | `true` cria os dados de demonstração e libera o login de visitante |
| `ENABLE_ADMIN_BOOTSTRAP` | não | `true` libera criar admin pela tela (padrão: desligado) |
