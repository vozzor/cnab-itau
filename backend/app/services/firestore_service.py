import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from app.config import get_settings
import os

_app = None


def get_firestore_client():
    global _app
    settings = get_settings()

    if not firebase_admin._apps:
        if settings.google_application_credentials and os.path.exists(settings.google_application_credentials):
            cred = credentials.Certificate(settings.google_application_credentials)
            _app = firebase_admin.initialize_app(cred)
        else:
            _app = firebase_admin.initialize_app()

    return firestore.client()


# ---------- FORNECEDORES ----------

def listar_fornecedores() -> List[Dict[str, Any]]:
    db = get_firestore_client()
    docs = db.collection("fornecedores").where("ativo", "==", True).stream()
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]


def obter_fornecedor(fornecedor_id: str) -> Optional[Dict[str, Any]]:
    """Busca fornecedor pelo id_bigquery (UUID) que é a chave do documento."""
    if not fornecedor_id or not fornecedor_id.strip():
        return None
    db = get_firestore_client()
    doc = db.collection("fornecedores").document(fornecedor_id.strip()).get()
    if doc.exists:
        return {"id": doc.id, **doc.to_dict()}
    return None


def obter_fornecedor_por_cnpj(cnpj: str) -> Optional[Dict[str, Any]]:
    """Busca fornecedor pelo campo cnpj (usado para importação CSV)."""
    db = get_firestore_client()
    docs = list(db.collection("fornecedores").where("cnpj", "==", cnpj).limit(1).stream())
    if docs:
        doc = docs[0]
        return {"id": doc.id, **doc.to_dict()}
    return None


def upsert_fornecedor(fornecedor_id: str, dados: Dict[str, Any]) -> None:
    db = get_firestore_client()
    db.collection("fornecedores").document(fornecedor_id).set(dados, merge=True)


def atualizar_chave_pix(fornecedor_id: str, tipo: str, valor: str, usuario: str, cnpj: Optional[str] = None) -> None:
    db = get_firestore_client()
    update: Dict[str, Any] = {
        "chave_pix": {"tipo": tipo, "valor": valor},
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "atualizado_por": usuario,
    }
    if cnpj:
        update["cnpj"] = cnpj
    db.collection("fornecedores").document(fornecedor_id).update(update)


def sincronizar_fornecedores(lista: List[Dict[str, Any]]) -> Dict[str, int]:
    """Cria ou atualiza fornecedores no Firestore.
    Usa id_bigquery (UUID) como chave do documento. CNPJ fica em branco
    para ser preenchido manualmente pelo usuário.
    Novos: cria com todos os campos.
    Existentes: atualiza somente o nome (não toca em cnpj nem chave_pix).
    """
    db = get_firestore_client()
    criados = 0
    atualizados = 0

    for item in lista:
        id_bigquery = item["id_bigquery"]
        ref = db.collection("fornecedores").document(id_bigquery)
        doc = ref.get()
        if not doc.exists:
            ref.set({
                "nome": item["nome"],
                "cnpj": "",
                "id_bigquery": id_bigquery,
                "chave_pix": None,
                "ativo": True,
                "atualizado_em": datetime.now(timezone.utc).isoformat(),
                "atualizado_por": "sistema",
            })
            criados += 1
        else:
            # Atualiza apenas o nome caso tenha mudado
            existing = doc.to_dict() or {}
            if existing.get("nome") != item["nome"]:
                ref.update({"nome": item["nome"]})
                atualizados += 1

    return {"criados": criados, "atualizados": atualizados}


# ---------- USUÁRIOS ----------

def listar_usuarios() -> List[Dict[str, Any]]:
    db = get_firestore_client()
    docs = db.collection("usuarios").stream()
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]


def obter_usuario(email: str) -> Optional[Dict[str, Any]]:
    if not email:
        return None
    db = get_firestore_client()
    doc = db.collection("usuarios").document(email).get()
    if doc.exists:
        return {"id": doc.id, **doc.to_dict()}
    return None


def salvar_usuario(email: str, role: str, criado_por: str) -> None:
    db = get_firestore_client()
    db.collection("usuarios").document(email).set({
        "email": email,
        "role": role,
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "atualizado_por": criado_por,
    }, merge=True)


def remover_usuario(email: str) -> None:
    db = get_firestore_client()
    db.collection("usuarios").document(email).delete()


# ---------- REMESSAS ----------

def criar_remessa(dados: Dict[str, Any]) -> str:
    db = get_firestore_client()
    _, ref = db.collection("remessas").add(dados)
    return ref.id


def obter_remessa(remessa_id: str) -> Optional[Dict[str, Any]]:
    db = get_firestore_client()
    doc = db.collection("remessas").document(remessa_id).get()
    if doc.exists:
        return {"id": doc.id, **doc.to_dict()}
    return None


def atualizar_remessa(remessa_id: str, dados: Dict[str, Any]) -> None:
    db = get_firestore_client()
    db.collection("remessas").document(remessa_id).update(dados)


def listar_remessas(status: Optional[str] = None) -> List[Dict[str, Any]]:
    db = get_firestore_client()
    if status:
        # where + order_by em campos distintos exige índice composto no Firestore;
        # ordenamos em memória para evitar a dependência de índice.
        docs = db.collection("remessas").where("status", "==", status).stream()
        items = [{"id": doc.id, **doc.to_dict()} for doc in docs]
        items.sort(key=lambda r: r.get("criado_em") or "", reverse=True)
        return items
    docs = db.collection("remessas").order_by(
        "criado_em", direction=firestore.Query.DESCENDING
    ).stream()
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]
