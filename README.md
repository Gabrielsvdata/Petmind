# PetMind

API REST para registro de comportamentos e rotinas de pets com análise de IA.  
Construída com **FastAPI + PostgreSQL + Groq** para a **World Code Cup**.

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

## Deploy no Render

### Pré-requisitos
- Conta no [Render](https://render.com)
- Repositório no GitHub com o projeto
- Chave de API do [Groq](https://console.groq.com)

### Passo a passo

**1. Suba o código para o GitHub**
```bash
git init
git add .
git commit -m "feat: petmind fase 2"
git remote add origin https://github.com/seu-usuario/petmind.git
git push -u origin main
```

**2. Crie o projeto no Render via Blueprint**

- Acesse [dashboard.render.com](https://dashboard.render.com)
- Clique em **New → Blueprint**
- Conecte seu repositório GitHub
- O Render vai detectar o `render.yaml` e criar automaticamente:
  - **Web Service** `petmind` (FastAPI)
  - **PostgreSQL** `petmind-db` (banco gerenciado)

**3. Configure a variável de ambiente GROQ_API_KEY**

- No painel do serviço `petmind` → **Environment**
- Adicione: `GROQ_API_KEY` = `<sua chave do Groq>`
- Clique em **Save Changes** (o serviço vai reiniciar)

**4. Aguarde o deploy**

- O Render executa `pip install -r requirements.txt`
- Em seguida inicia com `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- As tabelas são criadas automaticamente no primeiro start (`create_all`)
- URL final: `https://petmind.onrender.com/docs`

### Variáveis de ambiente no Render

| Variável | Origem | Valor |
|----------|--------|-------|
| `DATABASE_URL` | Automático (linked database) | — |
| `GROQ_API_KEY` | Manual | sua chave |
| `GROQ_MODEL` | `render.yaml` | `llama-3.3-70b-versatile` |

### Notas importantes

- **Plano free do Render**: o serviço hiberna após 15 min de inatividade — o primeiro request pode demorar ~30s para "acordar".
- **Banco free**: limite de 1 GB de armazenamento e expira após 90 dias sem uso.
- O `render.yaml` já corrige automaticamente a URL `postgres://` → `postgresql://` (necessário para SQLAlchemy).

# Petmind
