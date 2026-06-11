import re
from typing import Optional


def validate_chave_pix(tipo: str, valor: str) -> Optional[str]:
    """
    Retorna mensagem de erro ou None se válida.
    tipo: 01=telefone, 02=email, 03=CPF/CNPJ, 04=aleatória
    """
    if tipo == "01":
        if not re.match(r"^\+55\d{10,11}$", valor):
            return "Telefone deve estar no formato +55XXXXXXXXXXX"
    elif tipo == "02":
        if "@" not in valor:
            return "E-mail inválido"
        if len(valor) > 77:
            return "E-mail deve ter no máximo 77 caracteres"
    elif tipo == "03":
        digits = re.sub(r"\D", "", valor)
        if len(digits) not in (11, 14):
            return "CPF deve ter 11 dígitos ou CNPJ 14 dígitos (somente números)"
    elif tipo == "04":
        pattern = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
        if not re.match(pattern, valor):
            return "Chave aleatória deve ser UUID no formato XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
    else:
        return "Tipo de chave inválido. Use 01, 02, 03 ou 04."
    return None


def validate_cnpj_format(cnpj: str) -> bool:
    """Verifica se o CNPJ tem 14 dígitos numéricos."""
    digits = re.sub(r"\D", "", cnpj)
    return len(digits) == 14
