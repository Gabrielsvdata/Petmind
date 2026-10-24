"""Contas de demonstração para recrutadores e visitantes."""

from app.models.user import Usuario

CONTAS_DEMO = {
    "usuario": {"nome": "Visitante Tutor", "email": "tutor.demo@petmind.dev"},
    "admin": {"nome": "Visitante Admin", "email": "admin.demo@petmind.dev"},
}
EMAILS_DEMO = {conta["email"] for conta in CONTAS_DEMO.values()}


def eh_conta_demo(usuario: Usuario | None) -> bool:
    return bool(usuario and usuario.email.lower() in EMAILS_DEMO)
