"""
Gerador CNAB 240 — Itaú SISPAG (versão do layout de arquivo 080)
Pix Transferência por Chave (Tipo Pagamento 20, Forma 45, Câmara 009)

Referência: "Layout de Arquivos CNAB - SISPAG"
- Versão do layout do arquivo = 080 (campo 015-017 do Header de Arquivo)
- Cada registro tem EXATAMENTE 240 caracteres
- Campos alfanuméricos: alinhados à esquerda, completados com espaços
- Campos numéricos: alinhados à direita, completados com zeros
- Sem acentos, cedilhas ou caracteres especiais
"""

import unicodedata
import re
from datetime import datetime, date as date_type
from typing import Dict, Any
from app.config import get_settings


def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", str(text))
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Za-z0-9 .@/\-]", " ", ascii_str).upper()


def _alpha(value: str, size: int) -> str:
    return _normalize(str(value))[:size].ljust(size)


def _num(value, size: int) -> str:
    digits = re.sub(r"\D", "", str(value))
    return digits[:size].zfill(size)


def _valor(decimal_value, size: int = 15) -> str:
    cents = int(round(float(decimal_value) * 100))
    return str(cents).zfill(size)


def _assert_240(record: str, label: str = "") -> str:
    if len(record) != 240:
        raise ValueError(f"Registro {label} tem {len(record)} chars (esperado 240):\n{record!r}")
    return record


def _data_pagto_ddmmaaaa(raw) -> str:
    """Converte YYYY-MM-DD para DDMMAAAA. Se a data for passada, usa hoje."""
    s = str(raw or "")
    if "-" in s:
        try:
            venc = date_type.fromisoformat(s)
            if venc < date_type.today():
                venc = date_type.today()
            return venc.strftime("%d%m%Y")
        except (ValueError, TypeError):
            pass
    return _num(s, 8)


def _tipo_inscricao(documento: str) -> str:
    """Retorna '1' para CPF (11 dígitos) ou '2' para CNPJ (14 dígitos)."""
    digits = re.sub(r"\D", "", str(documento or ""))
    return "1" if len(digits) == 11 else "2"


# =============================================================================
# HEADER DE ARQUIVO — Registro Tipo 0 (Layout 086)
# =============================================================================
def build_header_arquivo() -> str:
    """
    001-003  Código banco = 341                              9(03)
    004-007  Lote = 0000                                     9(04)
    008      Tipo registro = 0                               9(01)
    009-014  Brancos                                         X(06)
    015-017  Versão layout do arquivo = 080                  9(03)
    018      Tipo inscrição empresa (2=CNPJ)                 9(01)
    019-032  CNPJ empresa                                    9(14)
    033-052  Brancos                                         X(20)
    053-057  Agência debitada                                9(05)
    058      Brancos                                         X(01)
    059-070  Conta debitada                                  9(12)
    071      Brancos                                         X(01)
    072      DAC da agência/conta                            9(01)
    073-102  Nome da empresa                                 X(30)
    103-132  Nome do banco = BANCO ITAU SA                   X(30)
    133-142  Brancos                                         X(10)
    143      Código remessa = 1                              9(01)
    144-151  Data geração DDMMAAAA                           9(08)
    152-157  Hora geração HHMMSS                             9(06)
    158-166  Zeros                                           9(09)
    167-171  Densidade = 00000 (teleprocessamento)           9(05)
    172-240  Brancos                                         X(69)
    """
    settings = get_settings()
    now = datetime.now()

    r = ""
    r += _num("341", 3)                              # 001-003
    r += "0000"                                       # 004-007
    r += "0"                                          # 008
    r += " " * 6                                      # 009-014
    r += "080"                                        # 015-017 versão layout
    r += "2"                                          # 018 CNPJ
    r += _num(settings.itau_cnpj_empresa, 14)         # 019-032
    r += " " * 20                                     # 033-052
    r += _num(settings.itau_agencia, 5)               # 053-057
    r += " "                                          # 058
    r += _num(settings.itau_conta, 12)                # 059-070
    r += " "                                          # 071
    r += _num(settings.itau_dac, 1)                   # 072 DAC ag/conta
    r += _alpha(settings.itau_nome_empresa, 30)       # 073-102
    r += _alpha("BANCO ITAU SA", 30)                  # 103-132
    r += " " * 10                                     # 133-142
    r += "1"                                          # 143 remessa
    r += now.strftime("%d%m%Y")                       # 144-151
    r += now.strftime("%H%M%S")                       # 152-157
    r += "0" * 9                                      # 158-166
    r += "00000"                                      # 167-171 densidade
    r += " " * 69                                     # 172-240

    return _assert_240(r, "HEADER_ARQUIVO")


# =============================================================================
# HEADER DE LOTE — Registro Tipo 1 (Layout 086)
# Pagamentos via crédito em conta / TED / Pix Transferência
# =============================================================================
def build_header_lote(num_lote: int = 1) -> str:
    """
    001-003  Banco = 341                                     9(03)
    004-007  Lote                                            9(04)
    008      Tipo registro = 1                               9(01)
    009      Tipo operação = C (crédito)                     X(01)
    010-011  Tipo pagamento = 20 (Fornecedores)              9(02)
    012-013  Forma pagamento = 45 (Pix Transferência)        9(02)
    014-016  Versão layout do lote = 040                     9(03)
    017      Brancos                                         X(01)
    018      Tipo inscrição empresa (2=CNPJ)                 9(01)
    019-032  CNPJ empresa                                    9(14)
    033-036  Identificação do lançamento (brancos)           X(04)
    037-052  Brancos                                         X(16)
    053-057  Agência debitada                                9(05)
    058      Brancos                                         X(01)
    059-070  Conta debitada                                  9(12)
    071      Brancos                                         X(01)
    072      DAC ag/conta                                    9(01)
    073-102  Nome da empresa                                 X(30)
    103-132  Finalidade do lote                              X(30)
    133-142  Histórico C/C debitada                          X(10)
    143-172  Endereço da empresa                             X(30)
    173-177  Número do local                                 9(05)
    178-192  Complemento                                     X(15)
    193-212  Cidade                                          X(20)
    213-220  CEP                                             9(08)
    221-222  UF                                              X(02)
    223-230  Brancos                                         X(08)
    231-240  Ocorrências (brancos na remessa)                X(10)
    """
    settings = get_settings()

    r = ""
    r += _num("341", 3)                               # 001-003
    r += _num(num_lote, 4)                            # 004-007
    r += "1"                                           # 008
    r += "C"                                           # 009 crédito
    r += "20"                                          # 010-011 fornecedores
    r += "45"                                          # 012-013 Pix Transferência
    r += "040"                                         # 014-016 layout lote
    r += " "                                           # 017
    r += "2"                                           # 018 CNPJ
    r += _num(settings.itau_cnpj_empresa, 14)          # 019-032
    r += " " * 4                                       # 033-036 ident lançamento
    r += " " * 16                                      # 037-052
    r += _num(settings.itau_agencia, 5)                # 053-057
    r += " "                                           # 058
    r += _num(settings.itau_conta, 12)                 # 059-070
    r += " "                                           # 071
    r += _num(settings.itau_dac, 1)                    # 072 DAC
    r += _alpha(settings.itau_nome_empresa, 30)        # 073-102
    r += _alpha("PAGAMENTO FORNECEDORES PIX", 30)      # 103-132 finalidade
    r += " " * 10                                      # 133-142 histórico C/C
    r += " " * 30                                      # 143-172 endereço
    r += "0" * 5                                       # 173-177 número
    r += " " * 15                                      # 178-192 complemento
    r += " " * 20                                      # 193-212 cidade
    r += "0" * 8                                       # 213-220 CEP
    r += " " * 2                                       # 221-222 UF
    r += " " * 8                                       # 223-230
    r += " " * 10                                      # 231-240 ocorrências

    return _assert_240(r, "HEADER_LOTE")


# =============================================================================
# SEGMENTO A — Registro Tipo 3 / Segmento A (Layout 086)
# Pix Transferência por Chave (forma 45)
# =============================================================================
def build_segmento_a(num_lote: int, seq: int, pagamento: Dict[str, Any]) -> str:
    """
    001-003  Banco = 341                                     9(03)
    004-007  Lote                                            9(04)
    008      Tipo registro = 3                               9(01)
    009-013  Seq do registro no lote                         9(05)
    014      Segmento = A                                    X(01)
    015-017  Tipo movimento = 000 (inclusão)                 9(03)
    018-020  Câmara = 009 (SPI - Pix)                        9(03)
    021-023  Banco favorecido (000 p/ Pix por chave)         9(03)
    024-043  Agência/conta favorecido                        X(20)
    044-073  Nome do favorecido                              X(30)
    074-093  Seu número (Nota 46: obrigatório em testes Pix) X(20)
    094-101  Data pagamento DDMMAAAA                         9(08)
    102-104  Moeda = REA                                     X(03)
    105-112  Código ISPB (brancos p/ Pix por chave)          X(08)
    113-114  Identif. transferência = 04 (Chave)             X(02)
    115-119  Zeros                                           9(05)
    120-134  Valor do pagamento (centavos)                   9(13)V9(02)
    135-149  Nosso número (brancos na remessa)               X(15)
    150-154  Brancos                                         X(05)
    155-162  Data efetiva (zeros na remessa)                 9(08)
    163-177  Valor efetivo (zeros na remessa)                9(13)V9(02)
    178-197  Finalidade detalhe (brancos)                    X(20)
    198-203  Nº DOC/TED/OP (zeros na remessa)                9(06)
    204-217  CPF/CNPJ do favorecido                          9(14)
    218-219  Finalidade DOC / status funcionário (brancos)   X(02)
    220-224  Finalidade TED (brancos)                        X(05)
    225-229  Brancos                                         X(05)
    230      Aviso ao favorecido = 0 (sem aviso)             X(01)
    231-240  Ocorrências (brancos na remessa)                X(10)
    """
    data_fmt = _data_pagto_ddmmaaaa(pagamento.get("data_vencimento", ""))
    nome_fav = pagamento.get("fornecedor_nome", "")
    valor = pagamento.get("valor", 0)
    seu_numero = pagamento.get("lancamento_id", "")
    cnpj_fav = pagamento.get("fornecedor_cnpj", "")

    r = ""
    r += _num("341", 3)                              # 001-003
    r += _num(num_lote, 4)                           # 004-007
    r += "3"                                          # 008
    r += _num(seq, 5)                                 # 009-013
    r += "A"                                          # 014
    r += "000"                                        # 015-017 tipo movimento inclusão
    r += "009"                                        # 018-020 câmara SPI
    r += "000"                                        # 021-023 banco favorecido
    r += " " * 20                                     # 024-043 agência/conta (opc p/ Pix chave)
    r += _alpha(nome_fav, 30)                         # 044-073
    r += _alpha(seu_numero, 20)                       # 074-093 seu número (Nota 46)
    r += data_fmt                                     # 094-101 data pagamento (já com 8 dígitos)
    r += "REA"                                        # 102-104 moeda
    r += " " * 8                                      # 105-112 ISPB (brancos p/ Pix chave)
    r += "04"                                         # 113-114 identif. transferência = Chave
    r += "0" * 5                                      # 115-119 zeros
    r += _valor(valor, 15)                            # 120-134
    r += " " * 15                                     # 135-149 nosso número (banco preenche)
    r += " " * 5                                      # 150-154
    r += "0" * 8                                      # 155-162 data efetiva
    r += "0" * 15                                     # 163-177 valor efetivo
    r += " " * 20                                     # 178-197 finalidade detalhe
    r += "0" * 6                                      # 198-203 nº doc retorno
    r += _num(cnpj_fav, 14)                           # 204-217 CPF/CNPJ favorecido
    r += " " * 2                                      # 218-219
    r += " " * 5                                      # 220-224 finalidade TED
    r += " " * 5                                      # 225-229
    r += "0"                                          # 230 aviso = 0 (sem aviso)
    r += " " * 10                                     # 231-240 ocorrências

    return _assert_240(r, f"SEGMENTO_A_seq{seq}")


# =============================================================================
# SEGMENTO B — Pix (Layout 086, pg 22)
# Obrigatório para Pix Transferência por Chave
# =============================================================================
def build_segmento_b(num_lote: int, seq: int, pagamento: Dict[str, Any]) -> str:
    """
    001-003  Banco = 341                                     9(03)
    004-007  Lote                                            9(04)
    008      Tipo registro = 3                               9(01)
    009-013  Seq do registro no lote                         9(05)
    014      Segmento = B                                    X(01)
    015-016  Tipo chave Pix (01=tel, 02=email, 03=CPF/CNPJ,  X(02)
                              04=aleatória)
    017      Brancos                                         X(01)
    018      Tipo inscrição favorecido (1=CPF, 2=CNPJ)       9(01)
    019-032  CPF/CNPJ favorecido                             9(14)
    033-062  Brancos (endereço não usado em Pix)             X(30)
    063-127  Informações entre usuários (zeros)              9(65)
    128-227  Chave Pix                                       X(100)
    228-230  Brancos                                         X(03)
    231-240  Ocorrências                                     X(10)
    """
    cnpj_fav = pagamento.get("fornecedor_cnpj", "")
    nome_fav = pagamento.get("fornecedor_nome", "")  # noqa: F841 (kept for futuro endereço)
    tipo_chave = pagamento.get("chave_pix_tipo", "03")
    chave = pagamento.get("chave_pix_valor", "")

    r = ""
    r += _num("341", 3)                               # 001-003
    r += _num(num_lote, 4)                            # 004-007
    r += "3"                                           # 008
    r += _num(seq, 5)                                  # 009-013
    r += "B"                                           # 014
    r += _num(tipo_chave, 2)                           # 015-016 tipo chave Pix
    r += " "                                           # 017
    r += _tipo_inscricao(cnpj_fav)                     # 018 tipo inscrição
    r += _num(cnpj_fav, 14)                            # 019-032 CPF/CNPJ
    r += " " * 30                                      # 033-062
    r += "0" * 65                                      # 063-127 info entre usuários
    r += _alpha(chave, 100)                            # 128-227 chave Pix
    r += " " * 3                                       # 228-230
    r += " " * 10                                      # 231-240 ocorrências

    return _assert_240(r, f"SEGMENTO_B_seq{seq}")


# =============================================================================
# TRAILER DE LOTE — Registro Tipo 5 (Layout 086)
# =============================================================================
def build_trailer_lote(num_lote: int, qtd_registros: int, soma_centavos: int) -> str:
    """
    001-003  Banco = 341                                     9(03)
    004-007  Lote                                            9(04)
    008      Tipo registro = 5                               9(01)
    009-017  Brancos                                         X(09)
    018-023  Total qtd registros no lote                     9(06)
    024-041  Soma dos valores (centavos)                     9(16)V9(02)
    042-059  Zeros                                           9(18)
    060-230  Brancos                                         X(171)
    231-240  Ocorrências                                     X(10)

    soma_centavos: soma dos centavos já arredondados por pagamento, para
    garantir que o total bata exatamente com a soma dos Segmentos A
    (divergência gera ocorrência "TA" no Itaú).
    """
    r = ""
    r += _num("341", 3)                               # 001-003
    r += _num(num_lote, 4)                            # 004-007
    r += "5"                                           # 008
    r += " " * 9                                       # 009-017
    r += _num(qtd_registros, 6)                        # 018-023
    r += _num(soma_centavos, 18)                       # 024-041
    r += "0" * 18                                      # 042-059
    r += " " * 171                                     # 060-230
    r += " " * 10                                      # 231-240 ocorrências

    return _assert_240(r, "TRAILER_LOTE")


# =============================================================================
# TRAILER DE ARQUIVO — Registro Tipo 9 (Layout 086)
# =============================================================================
def build_trailer_arquivo(qtd_lotes: int, qtd_registros_total: int) -> str:
    """
    001-003  Banco = 341                                     9(03)
    004-007  Lote = 9999                                     9(04)
    008      Tipo registro = 9                               9(01)
    009-017  Brancos                                         X(09)
    018-023  Total qtd lotes no arquivo                      9(06)
    024-029  Total qtd registros no arquivo                  9(06)
    030-240  Brancos                                         X(211)
    """
    r = ""
    r += _num("341", 3)                               # 001-003
    r += "9999"                                        # 004-007
    r += "9"                                           # 008
    r += " " * 9                                       # 009-017
    r += _num(qtd_lotes, 6)                            # 018-023
    r += _num(qtd_registros_total, 6)                  # 024-029
    r += " " * 211                                     # 030-240

    return _assert_240(r, "TRAILER_ARQUIVO")


# =============================================================================
# GERADOR PRINCIPAL
# =============================================================================
def gerar_cnab240(remessa: Dict[str, Any]) -> str:
    """Gera arquivo CNAB 240 SISPAG v086 para uma remessa Pix."""
    pagamentos = remessa.get("pagamentos", [])
    if not pagamentos:
        raise ValueError("Remessa sem pagamentos")

    linhas = []
    num_lote = 1

    linhas.append(build_header_arquivo())
    linhas.append(build_header_lote(num_lote))

    seq_registro = 1  # contagem dentro do lote, começa em 1 após header de lote
    soma_centavos = 0  # soma em centavos para bater exatamente com os Segmentos A
    qtd_registros_detalhe = 0  # apenas segmentos A+B

    for pagamento in pagamentos:
        seq_registro += 1
        linhas.append(build_segmento_a(num_lote, seq_registro, pagamento))
        qtd_registros_detalhe += 1

        seq_registro += 1
        linhas.append(build_segmento_b(num_lote, seq_registro, pagamento))
        qtd_registros_detalhe += 1

        soma_centavos += int(round(float(pagamento.get("valor", 0)) * 100))

    # Trailer de lote: header_lote(1) + segmentos + trailer_lote(1)
    qtd_total_lote = 1 + qtd_registros_detalhe + 1
    linhas.append(build_trailer_lote(num_lote, qtd_total_lote, soma_centavos))

    # Trailer de arquivo: header_arq(1) + header_lote(1) + segmentos + trailer_lote(1) + trailer_arq(1)
    qtd_total_arquivo = 1 + qtd_total_lote + 1
    linhas.append(build_trailer_arquivo(1, qtd_total_arquivo))

    return "\r\n".join(linhas) + "\r\n"
