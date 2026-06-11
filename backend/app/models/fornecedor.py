from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
import re


class ChavePix(BaseModel):
    tipo: str  # 01=telefone, 02=email, 03=CPF/CNPJ, 04=aleatória
    valor: str

    @field_validator("tipo")
    @classmethod
    def tipo_valido(cls, v):
        if v not in ("01", "02", "03", "04"):
            raise ValueError("Tipo de chave inválido. Use 01, 02, 03 ou 04.")
        return v

    @field_validator("valor")
    @classmethod
    def valor_valido(cls, v, info):
        tipo = info.data.get("tipo")
        if tipo == "01":
            if not re.match(r"^\+55\d{10,11}$", v):
                raise ValueError("Telefone deve estar no formato +55XXXXXXXXXXX")
        elif tipo == "02":
            if "@" not in v or len(v) > 77:
                raise ValueError("E-mail inválido ou maior que 77 caracteres")
        elif tipo == "03":
            digits = re.sub(r"\D", "", v)
            if len(digits) not in (11, 14):
                raise ValueError("CPF deve ter 11 dígitos ou CNPJ 14 dígitos (somente números)")
        elif tipo == "04":
            if not re.match(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", v):
                raise ValueError("Chave aleatória deve ser UUID no formato XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX")
        return v


class FornecedorBase(BaseModel):
    nome: str
    cnpj: str
    id_bigquery: Optional[str] = None
    ativo: bool = True


class FornecedorCreate(FornecedorBase):
    chave_pix: Optional[ChavePix] = None


class FornecedorUpdate(BaseModel):
    chave_pix: ChavePix
    atualizado_por: str
    cnpj: Optional[str] = None


class FornecedorResponse(FornecedorBase):
    chave_pix: Optional[ChavePix] = None
    atualizado_em: Optional[datetime] = None
    atualizado_por: Optional[str] = None


class ImportacaoCSVRow(BaseModel):
    cnpj: str
    tipo_chave: str
    chave_pix: str
