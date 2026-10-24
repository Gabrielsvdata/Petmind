import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Pet, RegistroComportamento, Usuario  # noqa: F401

# Banco de dados de teste PostgreSQL
TEST_DATABASE_URL = "postgresql+psycopg2://petmind:petmind123@localhost:5432/petmind_test"

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


def credenciais(email: str, senha: str) -> dict[str, str]:
    """Faz login e devolve o cabeçalho com o token de acesso."""
    resposta = client.post(
        "/auth/login", json={"email": email, "senha": senha}, headers={}
    )
    assert resposta.status_code == 200, resposta.text
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}


def promover_usuario_para_admin(email: str) -> None:
    db = TestingSessionLocal()
    try:
        usuario = db.query(Usuario).filter(Usuario.email == email).first()
        assert usuario is not None
        usuario.papel = "admin"
        db.commit()
    finally:
        db.close()


@pytest.fixture(autouse=True)
def autenticar_cliente(setup_db):
    """Registra usuário de teste e envia o token de login nas requisições."""
    client.headers.clear()

    email = "tester@petmind.dev"
    senha = "12345678"
    client.post(
        "/auth/register",
        json={"nome": "Tester", "email": email, "senha": senha},
    )

    client.headers.update(credenciais(email, senha))
    yield
    client.headers.clear()


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


def test_listar_pets_retorna_apenas_do_usuario_autenticado():
    client.post(
        "/pets/", json={"nome": "Rex", "raca": "Labrador", "idade": 3, "peso": 25.0}
    )

    outro_email = "outro@petmind.dev"
    outra_senha = "12345678"
    client.post(
        "/auth/register",
        json={"nome": "Outro", "email": outro_email, "senha": outra_senha},
    )
    resposta = client.get(
        "/pets/",
        headers=credenciais(outro_email, outra_senha),
    )

    assert resposta.status_code == 200
    assert resposta.json() == []


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


def test_usuario_nao_pode_acessar_pet_de_outro_usuario():
    cadastra = client.post(
        "/pets/", json={"nome": "Rex", "raca": "Labrador", "idade": 3, "peso": 25.0}
    )
    pet_id = cadastra.json()["id"]

    outro_email = "outro2@petmind.dev"
    outra_senha = "12345678"
    client.post(
        "/auth/register",
        json={"nome": "Outro 2", "email": outro_email, "senha": outra_senha},
    )
    resposta = client.get(
        f"/pets/{pet_id}",
        headers=credenciais(outro_email, outra_senha),
    )

    assert resposta.status_code == 403
    assert resposta.json()["detail"] == "Acesso negado a este pet"


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


def test_admin_pode_criar_outro_administrador():
    email_admin = "tester@petmind.dev"
    promover_usuario_para_admin(email_admin)

    payload = {
        "nome": "Admin Secundario",
        "email": "admin.secundario@petmind.dev",
        "senha": "12345678",
    }
    resposta = client.post("/admin/usuarios/admin", json=payload)

    assert resposta.status_code == 201
    dados = resposta.json()
    assert dados["email"] == payload["email"]
    assert dados["papel"] == "admin"


def test_status_admin_bootstrap_desabilitado_por_padrao(monkeypatch):
    monkeypatch.delenv("ENABLE_ADMIN_BOOTSTRAP", raising=False)
    resposta = client.get("/auth/admin-bootstrap/status")

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados == {"habilitado": False, "exige_chave": False}

    payload = {"nome": "X", "email": "x@petmind.dev", "senha": "12345678"}
    assert client.post("/auth/register-admin", json=payload).status_code == 403


def test_bootstrap_admin_cria_admin_quando_habilitado(monkeypatch):
    monkeypatch.setenv("ENABLE_ADMIN_BOOTSTRAP", "true")
    payload = {
        "nome": "Admin Novo",
        "email": "admin.novo@petmind.dev",
        "senha": "12345678",
    }
    resposta = client.post("/auth/register-admin", json=payload)

    assert resposta.status_code == 201
    dados = resposta.json()
    assert dados["email"] == payload["email"]
    assert dados["papel"] == "admin"


def test_bootstrap_admin_permite_multiplos_admins(monkeypatch):
    monkeypatch.setenv("ENABLE_ADMIN_BOOTSTRAP", "true")
    primeiro = {
        "nome": "Primeiro Admin",
        "email": "primeiro.admin@petmind.dev",
        "senha": "12345678",
    }
    client.post("/auth/register-admin", json=primeiro)

    segundo = {
        "nome": "Segundo Admin",
        "email": "segundo.admin@petmind.dev",
        "senha": "12345678",
    }
    resposta = client.post("/auth/register-admin", json=segundo)

    assert resposta.status_code == 201
    assert resposta.json()["papel"] == "admin"


def test_bootstrap_admin_exige_chave_quando_configurada(monkeypatch):
    monkeypatch.setenv("ENABLE_ADMIN_BOOTSTRAP", "true")
    monkeypatch.setenv("ADMIN_BOOTSTRAP_KEY", "segredo-teste")

    status = client.get("/auth/admin-bootstrap/status")
    assert status.status_code == 200
    assert status.json() == {"habilitado": True, "exige_chave": True}

    sem_chave = {
        "nome": "Primeiro Admin",
        "email": "admin.sem.chave@petmind.dev",
        "senha": "12345678",
    }
    resposta_sem_chave = client.post("/auth/register-admin", json=sem_chave)
    assert resposta_sem_chave.status_code == 403

    com_chave = {
        "nome": "Primeiro Admin",
        "email": "admin.com.chave@petmind.dev",
        "senha": "12345678",
        "chave_bootstrap": "segredo-teste",
    }
    resposta_com_chave = client.post("/auth/register-admin", json=com_chave)
    assert resposta_com_chave.status_code == 201
    assert resposta_com_chave.json()["papel"] == "admin"


# ─── Token e modo demonstração ─────────────────────────────


def test_rotas_exigem_token():
    assert client.get("/pets/", headers={"Authorization": ""}).status_code == 401
    falso = {"Authorization": "Bearer token-falso"}
    assert client.get("/pets/", headers=falso).status_code == 401


def test_http_basic_nao_e_mais_aceito():
    import base64

    basic = base64.b64encode(b"tester@petmind.dev:12345678").decode()
    resposta = client.get("/pets/", headers={"Authorization": f"Basic {basic}"})
    assert resposta.status_code == 401


def test_login_devolve_token_e_me_funciona():
    resposta = client.post(
        "/auth/login",
        json={"email": "tester@petmind.dev", "senha": "12345678"},
        headers={},
    )
    dados = resposta.json()
    assert dados["access_token"]
    assert "senha" not in dados
    eu = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {dados['access_token']}"}
    )
    assert eu.status_code == 200
    assert eu.json()["email"] == "tester@petmind.dev"


def _popular_demo():
    from app.seeds.demo_seed import popular_demo

    db = TestingSessionLocal()
    try:
        popular_demo(db)
    finally:
        db.close()


def test_login_demo_desligado_por_padrao(monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)
    resposta = client.post("/auth/login-demo", json={"perfil": "usuario"}, headers={})
    assert resposta.status_code == 404


def test_login_demo_entra_e_ve_pets(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    _popular_demo()
    token = client.post(
        "/auth/login-demo", json={"perfil": "usuario"}, headers={}
    ).json()["access_token"]
    pets = client.get("/pets/", headers={"Authorization": f"Bearer {token}"}).json()
    assert {p["nome"] for p in pets} == {"Thor", "Mia", "Pipoca"}


def test_contas_demo_protegidas(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    _popular_demo()
    token = client.post(
        "/auth/login-demo", json={"perfil": "admin"}, headers={}
    ).json()["access_token"]
    cabecalho = {"Authorization": f"Bearer {token}"}
    usuarios = client.get("/admin/usuarios", headers=cabecalho).json()
    tutor_demo = next(u for u in usuarios if u["email"] == "tutor.demo@petmind.dev")
    url = f"/admin/usuarios/{tutor_demo['id']}"
    assert client.delete(url, headers=cabecalho).status_code == 403
    assert (
        client.put(f"{url}/papel", json={"papel": "admin"}, headers=cabecalho)
        .status_code
        == 403
    )


# ─── Análise: números em Python, texto pela IA ─────────────


REGISTROS = [
    {"agitacao": 5, "sono": 2, "apetite": 3, "humor": 3, "observacoes": None},
    {"agitacao": 4, "sono": 2, "apetite": 4, "humor": 3, "observacoes": None},
    {"agitacao": 5, "sono": 3, "apetite": 4, "humor": 4, "observacoes": None},
]


def test_metricas_sao_deterministicas():
    from app.services.groq_service import calcular_metricas

    primeira = calcular_metricas(REGISTROS)  # type: ignore[arg-type]
    segunda = calcular_metricas(REGISTROS)  # type: ignore[arg-type]
    assert primeira == segunda
    assert primeira["medias"] == {
        "agitacao": 4.7, "sono": 2.3, "apetite": 3.7, "humor": 3.3
    }
    assert primeira["estado_predominante"] == "agitado"
    assert 60 <= primeira["confianca"] <= 98
    assert any("Agitação alta" in a for a in primeira["alertas"])
    assert any("Sono baixo" in a for a in primeira["alertas"])


def test_ia_nao_altera_numeros(monkeypatch):
    from app.services import groq_service

    def texto_da_ia(self, nome_pet, especie, analise, eventos):
        return {
            "diagnostico": "Texto da IA",
            "recomendacao": "Ação da IA",
            "confianca": 10,
            "estado_predominante": "triste",
        }

    monkeypatch.setattr(groq_service.GroqService, "_escrever_texto", texto_da_ia)
    analise = groq_service.GroqService().analisar_comportamento(
        "Rex", "cachorro", REGISTROS  # type: ignore[arg-type]
    )
    assert analise["diagnostico"] == "Texto da IA"
    assert analise["estado_predominante"] == "agitado"
    assert analise["confianca"] != 10


def test_analise_funciona_sem_ia(monkeypatch):
    from app.services import groq_service

    monkeypatch.setattr(
        groq_service.GroqService, "_escrever_texto", lambda *args: None
    )
    analise = groq_service.GroqService().analisar_comportamento(
        "Rex", "cachorro", REGISTROS  # type: ignore[arg-type]
    )
    assert analise["diagnostico"].startswith("Rex está predominantemente agitado")
    assert analise["recomendacao"]
