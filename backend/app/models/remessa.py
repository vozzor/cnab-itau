from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum


class StatusRemessa(str, Enum):
    RASCUNHO = "RASCUNHO"
    AGUARDANDO_APROVACAO = "AGUARDANDO_APROVACAO"
    APROVADA = "APROVADA"
    DEVOLVIDA = "DEVOLVIDA"


class PagamentoRemessa(BaseModel):
    lancamento_id: str
    descricao: str
    fornecedor_nome: str
    fornecedor_cnpj: str
    valor: Decimal
    data_vencimento: str
    chave_pix_tipo: str
    chave_pix_valor: str


class RemessaCreate(BaseModel):
    pagamentos: List[PagamentoRemessa]


class SolicitarAprovacaoRequest(BaseModel):
    usuario: str


class AprovarRequest(BaseModel):
    usuario: str


class DevolverRequest(BaseModel):
    usuario: str
    comentario: str


class RemessaResponse(BaseModel):
    id: str
    status: StatusRemessa
    criado_por: str
    criado_em: datetime
    total_pagamentos: int
    valor_total: Decimal
    pagamentos: List[PagamentoRemessa]
    comentario_devolucao: Optional[str] = None
    aprovado_por: Optional[str] = None
    aprovado_em: Optional[datetime] = None
