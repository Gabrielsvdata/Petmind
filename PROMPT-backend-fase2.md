# Prompt — PetMind Backend Fase 2

Cole este prompt no Claude Code do Cursor dentro do repositório do backend.

---

Você é um assistente especialista em Python e FastAPI.

Estou evoluindo o projeto **PetMind** para a Fase 2 da World Code Cup.
A Fase 1 já está completa com CRUD de pets e registros de comportamento.

## O que precisa ser implementado na Fase 2

### 1. Adicionar campo `especie` no model Pet

No arquivo `app/models/pet.py`, adicionar o campo:
```python
especie: Mapped[str] = mapped_column(String(20), nullable=False, default="cachorro")
# Valores aceitos: "cachorro", "gato", "hamster", "coelho"
```

No arquivo `app/schemas/pet.py`, adicionar em `PetBase`:
```python
especie: str = Field(..., description="Espécie do pet", pattern="^(cachorro|gato|hamster|coelho)$")
```

---

### 2. Criar `app/services/emocao_service.py`

Arquivo novo com função pura que calcula o estado emocional do pet:

Regras de cálculo:
- "animado"   → agitacao >= 4 E sono >= 4 E apetite >= 4 E humor >= 4
- "agitado"   → agitacao >= 4
- "triste"    → humor <= 2 E agitacao <= 2
- "sonolento" → sono <= 2
- "com_fome"  → apetite <= 2
- "feliz"     → qualquer outro caso

---

### 3. Novo endpoint — último registro com estado emocional

```
GET /pets/{pet_id}/registros/ultimo
```

- Busca o registro mais recente do pet
- Calcula o estado emocional usando o `emocao_service`
- Retorna 404 se pet não encontrado
- Retorna 400 com mensagem "Nenhum registro encontrado para este pet" se não houver registros

Schema de resposta (adicionar em `app/schemas/pet.py`):
```python
class UltimoRegistroResponse(BaseModel):
    id: int
    pet_id: int
    data_hora: datetime
    agitacao: int
    sono: int
    apetite: int
    humor: int
    observacoes: str | None
    estado_emocional: str  # "feliz" | "agitado" | "sonolento" | "com_fome" | "triste" | "animado"

    model_config = {"from_attributes": True}
```

---

### 4. Integração com Groq API

Completar `app/services/groq_service.py`:

```python
from groq import Groq

class GroqService:
    def __init__(self) -> None:
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = GROQ_MODEL

    def analisar_comportamento(self, nome_pet: str, especie: str, registros: list[dict]) -> str:
        # Montar prompt com os registros
        # Pedir análise em português
        # Retornar texto da análise
```

Novo endpoint:
```
POST /pets/{pet_id}/analisar
```

Schema de resposta:
```python
class AnaliseComportamentoResponse(BaseModel):
    pet_id: int
    nome_pet: str
    especie: str
    total_registros: int
    estado_emocional_atual: str
    analise: str
```

---

### 5. Habilitar CORS em `app/main.py`

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 6. Testes da Fase 2

Adicionar em `tests/test_pets.py`:
- `test_cadastrar_pet_com_especie`
- `test_especie_invalida` — 422
- `test_ultimo_registro`
- `test_ultimo_registro_sem_registros` — 400
- `test_estado_emocional_agitado`
- `test_estado_emocional_feliz`
- `test_analisar_comportamento`
- `test_analisar_sem_registros` — 400

---

## Regras obrigatórias — NUNCA viole

1. Nomes de domínio em português: `especie`, `estado_emocional`, `nome_pet`
2. Mensagens de erro em português
3. Route handlers síncronos (`def`, não `async def`) — exceto `/` e `/health`
4. SQLAlchemy 2.0: sempre `Mapped[]`, `mapped_column()`
5. Pydantic v2: sempre `model_dump()`, `model_config`, `Field()`
6. Datetime: sempre `datetime.now(UTC)`
7. Mypy strict: sem `Any` solto
8. Preservar toda funcionalidade da Fase 1
