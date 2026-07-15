"""
Script para criar o primeiro usuário admin.
Executar: python -m app.seeds.admin_seed
"""

from app.database import SessionLocal
from app.models.user import Usuario
from app.services.auth_service import hash_senha


def criar_admin() -> None:
    db = SessionLocal()
    try:
        existente = db.query(Usuario).filter(
            Usuario.email == "admin@petmind.com"
        ).first()
        if existente:
            print("Admin já existe!")
            return

        admin = Usuario(
            nome="Admin PetMind",
            email="admin@petmind.com",
            senha_hash=hash_senha("admin123"),
            papel="admin",
        )
        db.add(admin)
        db.commit()
        print("Admin criado com sucesso!")
        print("Email: admin@petmind.com")
        print("Senha: admin123")
    finally:
        db.close()


if __name__ == "__main__":
    criar_admin()
