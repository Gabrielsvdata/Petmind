"""Serviço de senha — hash bcrypt simples."""
import bcrypt


def hash_senha(senha: str) -> str:
    """Gera hash bcrypt da senha."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha.encode(), salt).decode()


def verificar_senha(senha: str, senha_hash: str) -> bool:
    """Verifica se a senha confere com o hash."""
    return bcrypt.checkpw(senha.encode(), senha_hash.encode())
