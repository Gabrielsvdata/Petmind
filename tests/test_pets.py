import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# Banco de dados de teste PostgreSQL
TEST_DATABASE_URL = "postgresql://petmind:petmind123@localhost:5432/petmind_test"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Cria e destrói o banco de dados para cada teste."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_raiz():
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert resposta.json() == {"mensagem": "Bem-vindo ao PetMind!"}


def test_health():
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_cadastrar_pet():
    payload = {
        "nome": "Rex",
        "raca": "Labrador",
        "idade": 3,
        "peso": 25.5,
        "observacoes": "Muito dócil",
    }
    resposta = client.post("/pets/", json=payload)
    assert resposta.status_code == 201
    dados = resposta.json()
    assert dados["nome"] == "Rex"
    assert dados["raca"] == "Labrador"
    assert dados["idade"] == 3
    assert dados["peso"] == 25.5
    assert dados["id"] is not None


def test_listar_pets():
    client.post(
        "/pets/", json={"nome": "Rex", "raca": "Labrador", "idade": 3, "peso": 25.0}
    )
    client.post(
        "/pets/", json={"nome": "Mimi", "raca": "Persa", "idade": 2, "peso": 4.5}
    )
    resposta = client.get("/pets/")
    assert resposta.status_code == 200
    assert len(resposta.json()) == 2


def test_buscar_pet():
    cadastra = client.post(
        "/pets/", json={"nome": "Rex", "raca": "Labrador", "idade": 3, "peso": 25.0}
    )
    pet_id = cadastra.json()["id"]
    resposta = client.get(f"/pets/{pet_id}")
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Rex"


def test_buscar_pet_nao_encontrado():
    resposta = client.get("/pets/999")
    assert resposta.status_code == 404


def test_adicionar_registro():
    cadastra = client.post(
        "/pets/", json={"nome": "Rex", "raca": "Labrador", "idade": 3, "peso": 25.0}
    )
    pet_id = cadastra.json()["id"]

    payload = {
        "agitacao": 3,
        "sono": 4,
        "apetite": 5,
        "humor": 4,
        "observacoes": "Dia tranquilo",
    }
    resposta = client.post(f"/pets/{pet_id}/registros", json=payload)
    assert resposta.status_code == 201
    dados = resposta.json()
    assert dados["pet_id"] == pet_id
    assert dados["agitacao"] == 3
    assert dados["sono"] == 4


def test_listar_registros():
    cadastra = client.post(
        "/pets/", json={"nome": "Rex", "raca": "Labrador", "idade": 3, "peso": 25.0}
    )
    pet_id = cadastra.json()["id"]

    client.post(
        f"/pets/{pet_id}/registros",
        json={"agitacao": 2, "sono": 3, "apetite": 4, "humor": 5},
    )
    client.post(
        f"/pets/{pet_id}/registros",
        json={"agitacao": 4, "sono": 2, "apetite": 3, "humor": 4},
    )

    resposta = client.get(f"/pets/{pet_id}/registros")
    assert resposta.status_code == 200
    assert len(resposta.json()) == 2


def test_validacao_campos_obrigatorios():
    resposta = client.post("/pets/", json={"nome": "Rex"})
    assert resposta.status_code == 422


def test_validacao_nivel_fora_range():
    cadastra = client.post(
        "/pets/", json={"nome": "Rex", "raca": "Labrador", "idade": 3, "peso": 25.0}
    )
    pet_id = cadastra.json()["id"]

    payload = {"agitacao": 6, "sono": 3, "apetite": 3, "humor": 3}
    resposta = client.post(f"/pets/{pet_id}/registros", json=payload)
    assert resposta.status_code == 422


# ── Fase 2 ────────────────────────────────────────────────────────────────────


def test_cadastrar_pet_com_especie():
    payload = {
        "nome": "Bolinha",
        "raca": "Persa",
        "especie": "gato",
        "idade": 2,
        "peso": 4.0,
    }
    resposta = client.post("/pets/", json=payload)
    assert resposta.status_code == 201
    assert resposta.json()["especie"] == "gato"


def test_especie_invalida():
    payload = {
        "nome": "Bolinha",
        "raca": "Persa",
        "especie": "papagaio",
        "idade": 2,
        "peso": 4.0,
    }
    resposta = client.post("/pets/", json=payload)
    assert resposta.status_code == 422


def test_ultimo_registro():
    cadastra = client.post(
        "/pets/",
        json={
            "nome": "Rex",
            "raca": "Labrador",
            "especie": "cachorro",
            "idade": 3,
            "peso": 25.0,
        },
    )
    pet_id = cadastra.json()["id"]

    client.post(
        f"/pets/{pet_id}/registros",
        json={"agitacao": 2, "sono": 3, "apetite": 4, "humor": 5},
    )
    client.post(
        f"/pets/{pet_id}/registros",
        json={"agitacao": 4, "sono": 4, "apetite": 4, "humor": 4},
    )

    resposta = client.get(f"/pets/{pet_id}/registros/ultimo")
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["pet_id"] == pet_id
    assert "estado_emocional" in dados
    assert dados["estado_emocional"] == "animado"


def test_ultimo_registro_sem_registros():
    cadastra = client.post(
        "/pets/",
        json={"nome": "Rex", "raca": "Labrador", "idade": 3, "peso": 25.0},
    )
    pet_id = cadastra.json()["id"]

    resposta = client.get(f"/pets/{pet_id}/registros/ultimo")
    assert resposta.status_code == 400
    assert resposta.json()["detail"] == "Nenhum registro encontrado para este pet"


def test_estado_emocional_agitado():
    cadastra = client.post(
        "/pets/",
        json={"nome": "Rex", "raca": "Labrador", "idade": 3, "peso": 25.0},
    )
    pet_id = cadastra.json()["id"]

    client.post(
        f"/pets/{pet_id}/registros",
        json={"agitacao": 5, "sono": 3, "apetite": 3, "humor": 3},
    )

    resposta = client.get(f"/pets/{pet_id}/registros/ultimo")
    assert resposta.status_code == 200
    assert resposta.json()["estado_emocional"] == "agitado"


def test_estado_emocional_feliz():
    cadastra = client.post(
        "/pets/",
        json={"nome": "Rex", "raca": "Labrador", "idade": 3, "peso": 25.0},
    )
    pet_id = cadastra.json()["id"]

    client.post(
        f"/pets/{pet_id}/registros",
        json={"agitacao": 2, "sono": 4, "apetite": 4, "humor": 4},
    )

    resposta = client.get(f"/pets/{pet_id}/registros/ultimo")
    assert resposta.status_code == 200
    assert resposta.json()["estado_emocional"] == "feliz"


def test_analisar_comportamento(monkeypatch):
    from app.services import groq_service

    def mock_analisar(self, nome_pet, especie, registros):
        return {
            "estado_predominante": "feliz",
            "confianca": 85,
            "medias": {"agitacao": 3.0, "sono": 4.0, "apetite": 4.0, "humor": 4.0},
            "tendencias": {"agitacao": "estável", "sono": "estável", "apetite": "estável", "humor": "estável"},
            "alertas": [],
            "diagnostico": "Pet apresenta padrão equilibrado.",
            "recomendacao": "Continue monitorando diariamente.",
        }

    monkeypatch.setattr(
        groq_service.GroqService, "analisar_comportamento", mock_analisar
    )

    cadastra = client.post(
        "/pets/",
        json={
            "nome": "Rex",
            "raca": "Labrador",
            "especie": "cachorro",
            "idade": 3,
            "peso": 25.0,
        },
    )
    pet_id = cadastra.json()["id"]

    client.post(
        f"/pets/{pet_id}/registros",
        json={"agitacao": 3, "sono": 4, "apetite": 4, "humor": 4},
    )

    resposta = client.post(f"/pets/{pet_id}/analisar")
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["pet_id"] == pet_id
    assert dados["nome_pet"] == "Rex"
    assert dados["especie"] == "cachorro"
    assert dados["total_registros"] == 1
    assert dados["estado_predominante"] == "feliz"
    assert dados["confianca"] == 85
    assert dados["medias"]["agitacao"] == 3.0
    assert dados["tendencias"]["sono"] == "estável"
    assert dados["alertas"] == []
    assert "diagnostico" in dados
    assert "recomendacao" in dados


def test_analisar_sem_registros():
    cadastra = client.post(
        "/pets/",
        json={"nome": "Rex", "raca": "Labrador", "idade": 3, "peso": 25.0},
    )
    pet_id = cadastra.json()["id"]

    resposta = client.post(f"/pets/{pet_id}/analisar")
    assert resposta.status_code == 400
    assert resposta.json()["detail"] == "Nenhum registro encontrado para este pet"
