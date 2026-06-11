from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import os

router = APIRouter()

ALLOWED_EMAILS_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'allowed_emails.json'
)


def load_allowed_emails() -> dict:
    """Fallback para bootstrap — usado quando a coleção 'usuarios' está vazia."""
    try:
        with open(ALLOWED_EMAILS_PATH, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def _resolve_role(email: str) -> Optional[str]:
    """Busca role: primeiro no Firestore, depois no JSON (bootstrap)."""
    from app.services.deps import get_store
    store = get_store()
    user = store.obter_usuario(email)
    if user:
        return user.get("role")
    allowed = load_allowed_emails()
    return allowed.get(email)


async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_dev_email: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """Dependência que retorna o usuário autenticado (dev ou produção)."""
    from app.config import get_settings
    settings = get_settings()

    if settings.dev_mode and x_dev_email:
        role = _resolve_role(x_dev_email)
        if not role:
            raise HTTPException(status_code=403, detail=f"Email '{x_dev_email}' não autorizado")
        return {"email": x_dev_email, "role": role}

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")

    token = authorization[len("Bearer "):]
    try:
        from firebase_admin import auth as firebase_auth
        from app.services.firestore_service import get_firestore_client
        get_firestore_client()
        decoded = firebase_auth.verify_id_token(token)
        email = decoded.get("email", "")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")

    role = _resolve_role(email)
    if not role:
        raise HTTPException(
            status_code=403,
            detail=f"Acesso não autorizado. Solicite ao administrador que adicione {email} ao sistema.",
        )
    return {"email": email, "role": role}


def require_auth(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return current_user


def require_gestor(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if current_user.get("role") != "gestor":
        raise HTTPException(status_code=403, detail="Acesso restrito a gestores")
    return current_user


class DevLoginRequest(BaseModel):
    email: str


@router.post("/dev-login")
def dev_login(body: DevLoginRequest):
    """Endpoint exclusivo para desenvolvimento local."""
    from app.config import get_settings
    if not get_settings().dev_mode:
        raise HTTPException(status_code=404, detail="Not found")

    role = _resolve_role(body.email)
    if not role:
        raise HTTPException(
            status_code=403,
            detail=f"Email '{body.email}' não está autorizado no sistema",
        )
    return {"email": body.email, "role": role}


@router.get("/me")
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    return current_user
