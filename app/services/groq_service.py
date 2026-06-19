"""
Serviço de integração com a Groq API.

Responsável por analisar comportamentos dos pets usando IA
e gerar insights sobre padrões e anomalias.
"""

import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


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
        registros: list[dict[str, object]],
    ) -> str:
        """Analisa registros e gera análise em português usando IA."""
        linhas_registros = "\n".join(
            f"- agitação={r['agitacao']}, sono={r['sono']}, "
            f"apetite={r['apetite']}, humor={r['humor']}"
            + (f", obs: {r['observacoes']}" if r.get("observacoes") else "")
            for r in registros
        )

        prompt = (
            f"Você é um especialista em comportamento animal. "
            f"Analise os seguintes registros de comportamento do pet '{nome_pet}' "
            f"(espécie: {especie}) e forneça uma análise detalhada em português "
            f"sobre o estado emocional e bem-estar do animal, identificando padrões "
            f"e sugerindo cuidados se necessário.\n\n"
            f"Registros de comportamento (escala 1-5):\n{linhas_registros}\n\n"
            f"Forneça uma análise clara e objetiva em no máximo 3 parágrafos."
        )

        resposta = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.7,
        )

        conteudo = resposta.choices[0].message.content
        return conteudo if conteudo is not None else "Análise não disponível."

    # def detectar_anomalias(self, registros) -> list[dict]:
    #     """Identifica comportamentos anômalos nos registros."""
    #     pass
