"""Reseta contas de acesso para ambiente de teste.

Executar:
python -m app.seeds.reset_demo_acessos
"""

from sqlalchemy import delete

from app.database import SessionLocal
from app.models.pet import Pet, RegistroComportamento
from app.models.user import Usuario
from app.services.usuario_service import criar_usuario


def resetar_acessos_demo() -> None:
    db = SessionLocal()
    try:
        db.execute(delete(RegistroComportamento))
        db.execute(delete(Pet))
        db.execute(delete(Usuario))
        db.commit()

        criar_usuario(
            db,
            nome="Usuario Teste",
            email="teste@teste.com",
            senha="12345678",
            papel="usuario",
        )
        criar_usuario(
            db,
            nome="Admin Teste",
            email="admin@admin.com",
            senha="12345678",
            papel="admin",
        )
        print("Acessos de teste recriados com sucesso.")
        print("Usuario: teste@teste.com / 12345678")
        print("Admin: admin@admin.com / 12345678")
    finally:
        db.close()


if __name__ == "__main__":
    resetar_acessos_demo()
