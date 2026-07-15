"""
Script para criar o primeiro usuário admin.
Executar: python -m app.seeds.admin_seed
"""

from app.database import SessionLocal
from app.services.usuario_service import buscar_usuario_por_email, criar_usuario


def criar_admin() -> None:
    db = SessionLocal()
    try:
        existente = buscar_usuario_por_email(db, "admin@petmind.com")
        if existente:
            print("Admin já existe!")
            return

        criar_usuario(
            db,
            nome="Admin PetMind",
            email="admin@petmind.com",
            senha="admin123",
            papel="admin",
        )
        print("Admin criado com sucesso!")
        print("Email: admin@petmind.com")
        print("Senha: admin123")
    finally:
        db.close()


if __name__ == "__main__":
    criar_admin()
