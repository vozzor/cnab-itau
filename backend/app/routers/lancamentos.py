from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import date
from typing import List
from app.services.deps import get_store, get_bq
from app.models.lancamento import Lancamento
from app.routers.auth import require_auth

router = APIRouter(dependencies=[Depends(require_auth)])


@router.get("", response_model=List[Lancamento])
def listar_lancamentos(
    data_inicio: date = Query(..., description="Data inicial YYYY-MM-DD"),
    data_fim: date = Query(..., description="Data final YYYY-MM-DD"),
):
    if data_inicio > data_fim:
        raise HTTPException(status_code=400, detail="data_inicio deve ser anterior a data_fim")

    bq = get_bq()
    store = get_store()

    try:
        rows = bq.buscar_lancamentos(str(data_inicio), str(data_fim))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar BigQuery: {str(e)}")

    try:
        lancamentos = []
        for row in rows:
            lanc = Lancamento(**row) if isinstance(row, dict) else row
            fornecedor = store.obter_fornecedor(lanc.fornecedor_cnpj) if lanc.fornecedor_cnpj else None
            if fornecedor and fornecedor.get("chave_pix"):
                lanc.chave_pix_tipo = fornecedor["chave_pix"]["tipo"]
                lanc.chave_pix_valor = fornecedor["chave_pix"]["valor"]
                lanc.tem_chave_pix = True
            lancamentos.append(lanc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar lançamentos: {str(e)}")

    return lancamentos


@router.post("/sincronizar-fornecedores")
def sincronizar_fornecedores():
    """Sincroniza lista de fornecedores do BigQuery para o Firestore."""
    try:
        lista = get_bq().buscar_fornecedores_bigquery()
        resultado = get_store().sincronizar_fornecedores(lista)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
