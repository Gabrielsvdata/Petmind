"""
Serviço de integração com a Groq API.

Responsável por analisar comportamentos dos pets usando IA
e gerar insights sobre padrões e anomalias.
"""

import json
import os
import re
from typing import Literal, TypedDict, cast

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


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


class GroqService:
    """Serviço de IA para análise de comportamento de pets."""

    def __init__(self) -> None:
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = GROQ_MODEL

    def verificar_conexao(self) -> bool:
        """Verifica se a API key está configurada."""
        return bool(GROQ_API_KEY)

    def analisar_comportamento(
        self,
        nome_pet: str,
        especie: str,
        registros: list[RegistroAnalise],
    ) -> AnaliseComportamentoDict:
        """
        Analisa registros e retorna JSON estruturado com métricas reais.
        Retorna dict com estado, confiança, médias, tendências, alertas,
        diagnóstico e recomendação.
        """
        # Calcular médias reais antes de enviar pra Groq
        total = len(registros)
        media_agitacao = round(sum(int(r["agitacao"]) for r in registros) / total, 1)
        media_sono = round(sum(r["sono"] for r in registros) / total, 1)
        media_apetite = round(sum(r["apetite"] for r in registros) / total, 1)
        media_humor = round(sum(r["humor"] for r in registros) / total, 1)

        # Calcular tendências comparando primeira e segunda metade
        metade = max(1, total // 2)
        primeira = registros[:metade]
        segunda = registros[metade:] if total > 1 else registros

        def tendencia(campo: CampoAnalise) -> str:
            media_p = sum(r[campo] for r in primeira) / len(primeira)
            media_s = sum(r[campo] for r in segunda) / len(segunda)
            diff = media_s - media_p
            if diff > 0.4:
                return "piorando" if campo in ["agitacao"] else "melhorando"
            if diff < -0.4:
                return "melhorando" if campo in ["agitacao"] else "piorando"
            return "estável"

        tendencias: TendenciasAnalise = {
            "agitacao": tendencia("agitacao"),
            "sono": tendencia("sono"),
            "apetite": tendencia("apetite"),
            "humor": tendencia("humor"),
        }

        # Extrai eventos codificados em observacoes no formato EVENTOS:id1,id2
        eventos_unicos: set[str] = set()
        for registro in registros:
            obs = str(registro.get("observacoes", "") or "")
            match = re.search(r"EVENTOS:([^|]+)", obs)
            if not match:
                continue
            ids = [ev.strip() for ev in match.group(1).split(",") if ev.strip()]
            eventos_unicos.update(ids)

        contexto_eventos = ""
        if eventos_unicos:
            eventos_lista = ", ".join(sorted(eventos_unicos))
            contexto_eventos = (
                f"\nEVENTOS DO PERÍODO:\n"
                f"- Eventos registrados: {eventos_lista}\n"
            )
            if "jogo_copa" in eventos_unicos or "torcida_casa" in eventos_unicos:
                contexto_eventos += (
                    "- Observação: houve jogos da Copa durante o período analisado.\n"
                )
            if "sozinho" in eventos_unicos:
                contexto_eventos += (
                    "- Observação: o pet ficou sozinho em alguns momentos.\n"
                )
            if any(
                e in eventos_unicos for e in ["reveillon", "festa_junina", "aniversario"]
            ):
                contexto_eventos += (
                    "- Observação: houve festas e barulho no período.\n"
                )
            if "tempestade" in eventos_unicos:
                contexto_eventos += (
                    "- Observação: houve tempestade/trovões no período.\n"
                )

        linhas = "\n".join(
            f"Registro {i+1}: agitação={r['agitacao']}, sono={r['sono']}, "
            f"apetite={r['apetite']}, humor={r['humor']}"
            + (f", obs: {r['observacoes']}" if r.get("observacoes") else "")
            for i, r in enumerate(registros)
        )

        prompt = f"""Você é um sistema de análise comportamental animal com ML.
Analise os dados do pet '{nome_pet}' (espécie: {especie}).

DADOS CALCULADOS:
- Total de registros: {total}
- Média agitação: {media_agitacao}/5
- Média sono: {media_sono}/5
- Média apetite: {media_apetite}/5
- Média humor: {media_humor}/5
- Tendências: agitação={tendencias['agitacao']}, sono={tendencias['sono']}, apetite={tendencias['apetite']}, humor={tendencias['humor']}

REGISTROS BRUTOS:
{linhas}
{contexto_eventos}

Responda APENAS com um JSON válido, sem texto antes ou depois, sem markdown, sem explicações.
O JSON deve seguir EXATAMENTE esta estrutura:

{{
  "estado_predominante": "feliz|agitado|sonolento|com_fome|triste|animado",
  "confianca": <número inteiro de 60 a 98>,
  "medias": {{
    "agitacao": {media_agitacao},
    "sono": {media_sono},
    "apetite": {media_apetite},
    "humor": {media_humor}
  }},
  "tendencias": {{
    "agitacao": "{tendencias['agitacao']}",
    "sono": "{tendencias['sono']}",
    "apetite": "{tendencias['apetite']}",
    "humor": "{tendencias['humor']}"
  }},
  "alertas": [
    "<alerta específico com dados numéricos reais se houver>",
    "<máximo 3 alertas, apenas se média < 2.5 ou > 4.0>"
  ],
  "diagnostico": "<frase curta e direta, máximo 15 palavras, com dado numérico>",
  "recomendacao": "<ação objetiva e específica, máximo 15 palavras>"
}}

Regras obrigatórias:
- estado_predominante deve ser um dos 6 valores aceitos
- alertas só aparecem se realmente houver algo fora do normal
- diagnostico e recomendacao devem ser CURTOS e OBJETIVOS
- confianca deve refletir a consistência dos dados (dados consistentes = confiança alta)
- NUNCA use markdown, NUNCA escreva texto fora do JSON"""

        resposta = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.2,
        )

        conteudo = resposta.choices[0].message.content
        if conteudo is None:
            return self._analise_fallback(
                nome_pet,
                media_agitacao,
                media_sono,
                media_apetite,
                media_humor,
                tendencias,
            )

        # Limpar possível markdown do modelo
        conteudo = conteudo.strip()
        if conteudo.startswith("```"):
            conteudo = conteudo.split("```")[1]
            if conteudo.startswith("json"):
                conteudo = conteudo[4:]

        try:
            return cast(AnaliseComportamentoDict, json.loads(conteudo))
        except Exception:
            return self._analise_fallback(
                nome_pet,
                media_agitacao,
                media_sono,
                media_apetite,
                media_humor,
                tendencias,
            )

    def _analise_fallback(
        self,
        nome_pet: str,
        media_agitacao: float,
        media_sono: float,
        media_apetite: float,
        media_humor: float,
        tendencias: TendenciasAnalise,
    ) -> AnaliseComportamentoDict:
        """Fallback caso o JSON da Groq venha malformado."""
        estado = "feliz"
        if media_agitacao >= 4:
            estado = "agitado"
        elif media_humor <= 2:
            estado = "triste"
        elif media_sono <= 2:
            estado = "sonolento"
        elif media_apetite <= 2:
            estado = "com_fome"

        return {
            "estado_predominante": estado,
            "confianca": 70,
            "medias": {
                "agitacao": media_agitacao,
                "sono": media_sono,
                "apetite": media_apetite,
                "humor": media_humor,
            },
            "tendencias": tendencias,
            "alertas": [],
            "diagnostico": f"{nome_pet} apresenta padrão estável nos registros.",
            "recomendacao": "Continue monitorando diariamente.",
        }


def get_groq_service() -> GroqService:
    """Retorna uma instância do GroqService."""
    return GroqService()
