from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from typing import Optional


class Lancamento(BaseModel):
    id: str
    descricao: str
    valor: Decimal
    data_vencimento: date
    fornecedor_nome: str
    fornecedor_cnpj: str
    status: str = "PENDENTE"

    # Enriquecido após cruzamento com Firestore
    chave_pix_tipo: Optional[str] = None
    chave_pix_valor: Optional[str] = None
    tem_chave_pix: bool = False
