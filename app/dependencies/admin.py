from fastapi import Depends, HTTPException

from app.dependencies.auth import get_usuario_atual
from app.models.user import Usuario


def get_usuario_admin(
    usuario: Usuario = Depends(get_usuario_atual),
) -> Usuario:
    if usuario.papel != "admin":
        raise HTTPException(
            status_code=403,
            detail="Acesso restrito a administradores",
        )
    return usuario
