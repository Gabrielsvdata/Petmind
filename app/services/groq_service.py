"""
Análise de comportamento dos pets.

Divisão de responsabilidades:
- Médias, tendências, estado predominante, confiança e alertas são calculados
  aqui em Python, com regras fixas: os mesmos registros geram sempre os mesmos números.
- A IA (Groq) só escreve o diagnóstico e a recomendação em linguagem natural.
  Se ela falhar, o texto vem de um modelo fixo e a análise continua funcionando.
"""

import json
import logging
import os
import re
import statistics
from typing import Any, Literal, TypedDict

from dotenv import load_dotenv
from groq import Groq

from app.services.emocao_service import calcular_estado_emocional

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "").strip()

# O Groq aposenta modelos com frequência (o LLaMA 3.3 saiu em 2026). A API usa o
# primeiro desta lista que estiver disponível para a chave; GROQ_MODEL força um.
MODELOS_PREFERIDOS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
    "qwen/qwen3.6-27b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]
_modelos_disponiveis: set[str] | None = None


def escolher_modelo(client: Any) -> str:
    """Primeiro modelo preferido liberado para a chave (consulta /models uma vez)."""
    global _modelos_disponiveis
    if GROQ_MODEL:
        return GROQ_MODEL
    if _modelos_disponiveis is None:
        try:
            _modelos_disponiveis = {m.id for m in client.models.list().data}
        except Exception:
            logger.warning("Não foi possível listar os modelos do Groq")
            return MODELOS_PREFERIDOS[0]
    return next(
        (m for m in MODELOS_PREFERIDOS if m in _modelos_disponiveis),
        MODELOS_PREFERIDOS[0],
    )


def esforco_raciocinio(modelo: str) -> str | None:
    """Modelos com raciocínio gastam tokens pensando; aqui só interessa a resposta."""
    if modelo.startswith("openai/gpt-oss"):
        return "low"
    if modelo.startswith("qwen/"):
        return "none"
    return None


def sem_raciocinio(texto: str) -> str:
    """Remove o bloco <think>...</think> que alguns modelos põem antes da resposta."""
    return re.sub(r"<think>.*?</think>", "", texto, flags=re.S).strip()


class RegistroAnalise(TypedDict):
    agitacao: int
    sono: int
    apetite: int
    humor: int
    observacoes: str | None


class MediasAnalise(TypedDict):
    agitacao: float
    sono: float
    apetite: float
    humor: float


class TendenciasAnalise(TypedDict):
    agitacao: str
    sono: str
    apetite: str
    humor: str


class AnaliseComportamentoDict(TypedDict):
    estado_predominante: str
    confianca: int
    medias: MediasAnalise
    tendencias: TendenciasAnalise
    alertas: list[str]
    diagnostico: str
    recomendacao: str


CampoAnalise = Literal["agitacao", "sono", "apetite", "humor"]


CAMPOS: tuple[CampoAnalise, ...] = ("agitacao", "sono", "apetite", "humor")
NOMES_CAMPOS = {
    "agitacao": "agitação",
    "sono": "sono",
    "apetite": "apetite",
    "humor": "humor",
}


def calcular_tendencias(registros: list[RegistroAnalise]) -> TendenciasAnalise:
    """Compara a primeira e a segunda metade dos registros."""
    total = len(registros)
    metade = max(1, total // 2)
    primeira = registros[:metade]
    segunda = registros[metade:] if total > 1 else registros

    def tendencia(campo: CampoAnalise) -> str:
        media_p = sum(r[campo] for r in primeira) / len(primeira)
        media_s = sum(r[campo] for r in segunda) / len(segunda)
        diff = media_s - media_p
        if diff > 0.4:
            return "piorando" if campo == "agitacao" else "melhorando"
        if diff < -0.4:
            return "melhorando" if campo == "agitacao" else "piorando"
        return "estável"

    return {
        "agitacao": tendencia("agitacao"),
        "sono": tendencia("sono"),
        "apetite": tendencia("apetite"),
        "humor": tendencia("humor"),
    }


def calcular_confianca(registros: list[RegistroAnalise]) -> int:
    """
    Confiança da análise (60 a 98): cresce com a quantidade de registros
    e com a consistência deles (menor variação entre um registro e outro).
    """
    volume = min(len(registros), 10) * 2  # até +20
    if len(registros) > 1:
        desvio_medio = sum(
            statistics.pstdev([r[c] for r in registros]) for c in CAMPOS
        ) / len(CAMPOS)
        consistencia = max(0.0, 1 - desvio_medio / 2)
    else:
        consistencia = 0.5
    return max(60, min(98, round(60 + volume + consistencia * 18)))


def calcular_alertas(medias: MediasAnalise) -> list[str]:
    """Alerta quando a média de um campo foge da faixa normal (2,5 a 4,0)."""
    alertas: list[str] = []
    for campo in CAMPOS:
        media = medias[campo]
        nome = NOMES_CAMPOS[campo]
        if campo == "agitacao" and media > 4.0:
            alertas.append(f"Agitação alta: média {media}/5 nos registros.")
        elif campo != "agitacao" and media < 2.5:
            alertas.append(
                f"{nome.capitalize()} baixo: média {media}/5 nos registros."
            )
    return alertas[:3]


def extrair_eventos(registros: list[RegistroAnalise]) -> set[str]:
    """Extrai eventos codificados em observações no formato EVENTOS:id1,id2."""
    eventos: set[str] = set()
    for registro in registros:
        obs = str(registro.get("observacoes", "") or "")
        match = re.search(r"EVENTOS:([^|]+)", obs)
        if match:
            eventos.update(ev.strip() for ev in match.group(1).split(",") if ev.strip())
    return eventos


def calcular_metricas(registros: list[RegistroAnalise]) -> AnaliseComportamentoDict:
    """Calcula toda a parte numérica da análise, sem IA."""
    total = len(registros)
    def media(campo: CampoAnalise) -> float:
        return round(sum(int(r[campo]) for r in registros) / total, 1)

    medias: MediasAnalise = {
        "agitacao": media("agitacao"),
        "sono": media("sono"),
        "apetite": media("apetite"),
        "humor": media("humor"),
    }
    estado = calcular_estado_emocional(
        round(medias["agitacao"]),
        round(medias["sono"]),
        round(medias["apetite"]),
        round(medias["humor"]),
    )
    return {
        "estado_predominante": estado,
        "confianca": calcular_confianca(registros),
        "medias": medias,
        "tendencias": calcular_tendencias(registros),
        "alertas": calcular_alertas(medias),
        "diagnostico": "",
        "recomendacao": "",
    }


def texto_padrao(nome_pet: str, metricas: AnaliseComportamentoDict) -> tuple[str, str]:
    """Diagnóstico e recomendação fixos, usados quando a IA não responde."""
    estado = metricas["estado_predominante"].replace("_", " ")
    medias = metricas["medias"]
    diagnostico = (
        f"{nome_pet} está predominantemente {estado} "
        f"(humor médio {medias['humor']}/5)."
    )
    if metricas["alertas"]:
        recomendacao = (
            "Observe os pontos de alerta e, se persistirem, consulte um veterinário."
        )
    else:
        recomendacao = "Continue registrando a rotina diariamente."
    return diagnostico, recomendacao


class GroqService:
    """Serviço de análise de comportamento de pets."""

    def __init__(self) -> None:
        self.client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

    def verificar_conexao(self) -> bool:
        """Verifica se a API key está configurada."""
        return bool(GROQ_API_KEY)

    def analisar_comportamento(
        self,
        nome_pet: str,
        especie: str,
        registros: list[RegistroAnalise],
    ) -> AnaliseComportamentoDict:
        """Métricas calculadas em Python + texto escrito pela IA."""
        analise = calcular_metricas(registros)
        diagnostico, recomendacao = texto_padrao(nome_pet, analise)

        eventos = extrair_eventos(registros)
        texto_ia = self._escrever_texto(nome_pet, especie, analise, eventos)
        if texto_ia:
            diagnostico = texto_ia.get("diagnostico") or diagnostico
            recomendacao = texto_ia.get("recomendacao") or recomendacao

        analise["diagnostico"] = str(diagnostico)[:200]
        analise["recomendacao"] = str(recomendacao)[:200]
        return analise

    def _escrever_texto(
        self,
        nome_pet: str,
        especie: str,
        analise: AnaliseComportamentoDict,
        eventos: set[str],
    ) -> dict[str, str] | None:
        """Pede à IA só o diagnóstico e a recomendação. Retorna None se falhar."""
        if self.client is None:
            return None

        contexto_eventos = (
            f"Eventos no período: {', '.join(sorted(eventos))}.\n" if eventos else ""
        )
        prompt = f"""Você é um assistente de comportamento animal.
Os números abaixo já foram calculados e NÃO devem ser alterados nem recalculados.

Pet: {nome_pet} ({especie})
Estado predominante: {analise['estado_predominante']}
Médias (1 a 5): {json.dumps(analise['medias'], ensure_ascii=False)}
Tendências: {json.dumps(analise['tendencias'], ensure_ascii=False)}
Alertas: {json.dumps(analise['alertas'], ensure_ascii=False)}
{contexto_eventos}
Escreva em português, de forma direta:
- "diagnostico": uma frase de no máximo 15 palavras citando um dado numérico acima;
- "recomendacao": uma ação objetiva de no máximo 15 palavras.

Responda somente com um JSON: {{"diagnostico": "...", "recomendacao": "..."}}"""

        try:
            modelo = escolher_modelo(self.client)
            parametros: dict[str, Any] = {
                "model": modelo,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 600,
                "temperature": 0,
                "response_format": {"type": "json_object"},
            }
            esforco = esforco_raciocinio(modelo)
            try:
                resposta = self.client.chat.completions.create(
                    **parametros,
                    extra_body={"reasoning_effort": esforco} if esforco else None,
                )
            except Exception as erro:
                # Modelo que não aceita o ajuste de raciocínio: tenta sem ele
                if not esforco or getattr(erro, "status_code", None) != 400:
                    raise
                resposta = self.client.chat.completions.create(**parametros)
            conteudo = sem_raciocinio(resposta.choices[0].message.content or "{}")
            dados = json.loads(conteudo)
            return dados if isinstance(dados, dict) else None
        except Exception:  # rede, limite de uso, modelo indisponível, JSON inválido
            logger.exception("Falha ao gerar texto da análise com a Groq")
            return None


def get_groq_service() -> GroqService:
    """Retorna uma instância do GroqService."""
    return GroqService()
