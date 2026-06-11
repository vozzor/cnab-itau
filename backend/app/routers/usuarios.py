from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any
from app.services.deps import get_store
from app.routers.auth import require_gestor

router = APIRouter()

ROLES_VALIDAS = {"gestor", "financeiro"}


class UsuarioCreate(BaseModel):
    email: str
    role: str


class UsuarioUpdate(BaseModel):
    role: str


@router.get("/")
def listar(_: Dict[str, Any] = Depends(require_gestor)):
    store = get_store()
    return store.listar_usuarios()


@router.post("/", status_code=201)
def criar(body: UsuarioCreate, current_user: Dict[str, Any] = Depends(require_gestor)):
    if body.role not in ROLES_VALIDAS:
        raise HTTPException(status_code=422, detail=f"Role inválida. Use: {ROLES_VALIDAS}")
    if not body.email or "@" not in body.email:
        raise HTTPException(status_code=422, detail="Email inválido")
    store = get_store()
    store.salvar_usuario(body.email.lower().strip(), body.role, current_user["email"])
    return {"email": body.email, "role": body.role}


@router.put("/{email:path}")
def atualizar(email: str, body: UsuarioUpdate, current_user: Dict[str, Any] = Depends(require_gestor)):
    if body.role not in ROLES_VALIDAS:
        raise HTTPException(status_code=422, detail=f"Role inválida. Use: {ROLES_VALIDAS}")
    store = get_store()
    if not store.obter_usuario(email):
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    store.salvar_usuario(email, body.role, current_user["email"])
    return {"email": email, "role": body.role}


@router.delete("/{email:path}", status_code=204)
def remover(email: str, current_user: Dict[str, Any] = Depends(require_gestor)):
    if email == current_user["email"]:
        raise HTTPException(status_code=400, detail="Você não pode remover sua própria conta")
    store = get_store()
    if not store.obter_usuario(email):
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    store.remover_usuario(email)
