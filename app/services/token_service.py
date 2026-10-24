"""Tokens de acesso (JWT) emitidos no login."""

import logging
import os
from datetime import UTC, datetime, timedelta

import jwt

ALGORITMO = "HS256"
_CHAVE_DEV = "petmind-chave-de-desenvolvimento"

logger = logging.getLogger(__name__)


def _chave() -> str:
    chave = os.getenv("SECRET_KEY", "").strip()
    if not chave:
        logger.warning("SECRET_KEY não definida: usando chave de desenvolvimento.")
        return _CHAVE_DEV
    return chave


def gerar_token(usuario_id: int, papel: str) -> str:
    """Gera o token de acesso do usuário autenticado."""
    horas = int(os.getenv("TOKEN_EXPIRACAO_HORAS", "8"))
    agora = datetime.now(UTC)
    payload = {
        "sub": str(usuario_id),
        "papel": papel,
        "iat": agora,
        "exp": agora + timedelta(hours=horas),
    }
    return jwt.encode(payload, _chave(), algorithm=ALGORITMO)


def ler_usuario_id(token: str) -> int | None:
    """Valida o token e devolve o id do usuário, ou None se inválido/expirado."""
    try:
        payload = jwt.decode(token, _chave(), algorithms=[ALGORITMO])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
