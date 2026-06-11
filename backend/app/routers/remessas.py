from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import io

from app.services.deps import get_store, get_audit
from app.services.cnab_generator import gerar_cnab240
from app.models.remessa import (
    RemessaCreate, DevolverRequest, StatusRemessa
)
from app.routers.auth import require_auth, require_gestor

router = APIRouter(dependencies=[Depends(require_auth)])


@router.post("")
def criar_remessa(body: RemessaCreate, current_user: Dict[str, Any] = Depends(require_auth)):
    usuario = current_user["email"]
    store = get_store()

    pagamentos_enriquecidos = []
    for p in body.pagamentos:
        if not p.chave_pix_tipo or not p.chave_pix_valor:
            raise HTTPException(
                status_code=422,
                detail=f"Fornecedor '{p.fornecedor_nome}' sem chave Pix cadastrada"
            )

        fornecedor = store.obter_fornecedor(p.fornecedor_cnpj) if p.fornecedor_cnpj else None
        cnpj_real = (fornecedor or {}).get("cnpj", "").strip()

        if not cnpj_real:
            raise HTTPException(
                status_code=422,
                detail=f"Fornecedor '{p.fornecedor_nome}' sem CNPJ cadastrado. "
                       "Acesse Fornecedores e preencha o CNPJ antes de incluir na remessa."
            )

        dados_p = p.model_dump(mode="json")
        dados_p["fornecedor_id"] = p.fornecedor_cnpj
        dados_p["fornecedor_cnpj"] = cnpj_real
        pagamentos_enriquecidos.append(dados_p)

    valor_total = sum(float(p.valor) for p in body.pagamentos)
    dados = {
        "status": StatusRemessa.RASCUNHO,
        "criado_por": usuario,
        "criado_em": datetime.now(timezone.utc).isoformat(),
        "total_pagamentos": len(body.pagamentos),
        "valor_total": valor_total,
        "pagamentos": pagamentos_enriquecidos,
        "comentario_devolucao": None,
        "aprovado_por": None,
        "aprovado_em": None,
    }

    remessa_id = store.criar_remessa(dados)
    get_audit().registrar_auditoria(
        acao="REMESSA_CRIADA",
        usuario=usuario,
        remessa_id=remessa_id,
        valor_total=valor_total,
        qtd_pagamentos=len(body.pagamentos),
    )
    return {"id": remessa_id, "status": StatusRemessa.RASCUNHO}


@router.get("")
def listar_remessas(status: Optional[str] = None):
    return get_store().listar_remessas(status)


@router.get("/{remessa_id}")
def obter_remessa(remessa_id: str):
    remessa = get_store().obter_remessa(remessa_id)
    if not remessa:
        raise HTTPException(status_code=404, detail="Remessa não encontrada")
    return remessa


@router.post("/{remessa_id}/solicitar-aprovacao")
def solicitar_aprovacao(
    remessa_id: str,
    current_user: Dict[str, Any] = Depends(require_auth),
):
    usuario = current_user["email"]
    store = get_store()
    remessa = store.obter_remessa(remessa_id)
    if not remessa:
        raise HTTPException(status_code=404, detail="Remessa não encontrada")
    if remessa["status"] not in (StatusRemessa.RASCUNHO, StatusRemessa.DEVOLVIDA):
        raise HTTPException(status_code=400, detail="Remessa não pode ser enviada para aprovação no status atual")

    store.atualizar_remessa(remessa_id, {"status": StatusRemessa.AGUARDANDO_APROVACAO})
    get_audit().registrar_auditoria(acao="APROVACAO_SOLICITADA", usuario=usuario, remessa_id=remessa_id)
    return {"status": StatusRemessa.AGUARDANDO_APROVACAO}


@router.post("/{remessa_id}/aprovar")
def aprovar_remessa(
    remessa_id: str,
    current_user: Dict[str, Any] = Depends(require_gestor),
):
    usuario = current_user["email"]
    store = get_store()
    remessa = store.obter_remessa(remessa_id)
    if not remessa:
        raise HTTPException(status_code=404, detail="Remessa não encontrada")
    if remessa["status"] != StatusRemessa.AGUARDANDO_APROVACAO:
        raise HTTPException(status_code=400, detail="Remessa não está aguardando aprovação")

    store.atualizar_remessa(remessa_id, {
        "status": StatusRemessa.APROVADA,
        "aprovado_por": usuario,
        "aprovado_em": datetime.now(timezone.utc).isoformat(),
    })
    get_audit().registrar_auditoria(
        acao="REMESSA_APROVADA",
        usuario=usuario,
        remessa_id=remessa_id,
        valor_total=remessa.get("valor_total"),
        qtd_pagamentos=remessa.get("total_pagamentos"),
    )
    return {"status": StatusRemessa.APROVADA}


@router.post("/{remessa_id}/devolver")
def devolver_remessa(
    remessa_id: str,
    body: DevolverRequest,
    current_user: Dict[str, Any] = Depends(require_gestor),
):
    usuario = current_user["email"]
    store = get_store()
    remessa = store.obter_remessa(remessa_id)
    if not remessa:
        raise HTTPException(status_code=404, detail="Remessa não encontrada")
    if remessa["status"] != StatusRemessa.AGUARDANDO_APROVACAO:
        raise HTTPException(status_code=400, detail="Remessa não está aguardando aprovação")

    store.atualizar_remessa(remessa_id, {
        "status": StatusRemessa.DEVOLVIDA,
        "comentario_devolucao": body.comentario,
    })
    get_audit().registrar_auditoria(
        acao="REMESSA_DEVOLVIDA",
        usuario=usuario,
        remessa_id=remessa_id,
        detalhes={"comentario": body.comentario},
    )
    return {"status": StatusRemessa.DEVOLVIDA}


@router.get("/{remessa_id}/download")
def download_cnab(remessa_id: str, current_user: Dict[str, Any] = Depends(require_auth)):
    usuario = current_user["email"]
    remessa = get_store().obter_remessa(remessa_id)
    if not remessa:
        raise HTTPException(status_code=404, detail="Remessa não encontrada")
    if remessa["status"] != StatusRemessa.APROVADA:
        raise HTTPException(status_code=400, detail="Apenas remessas aprovadas podem ser baixadas")

    try:
        conteudo = gerar_cnab240(remessa)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar CNAB: {str(e)}")

    get_audit().registrar_auditoria(acao="CNAB_DOWNLOAD", usuario=usuario, remessa_id=remessa_id)

    nome_arquivo = f"remessa_{remessa_id}.rem"
    return StreamingResponse(
        io.StringIO(conteudo),
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={nome_arquivo}"},
    )
