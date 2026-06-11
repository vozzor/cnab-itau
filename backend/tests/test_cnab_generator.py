"""
Testes unitários para o gerador CNAB 240 Itaú SISPAG v086.
Validações críticas:
- Cada linha tem exatamente 240 caracteres
- Totalizadores batem
- Campos críticos nos positions corretos
- Normalização de texto (sem acentos)
"""
import pytest
import os
import sys

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configura variáveis de ambiente para os testes
os.environ.setdefault("ITAU_CNPJ_EMPRESA", "12345678000190")
os.environ.setdefault("ITAU_AGENCIA", "12345")
os.environ.setdefault("ITAU_CONTA", "000123456789")
os.environ.setdefault("ITAU_DAC", "0")
os.environ.setdefault("ITAU_NOME_EMPRESA", "EMPRESA TESTE LTDA")
os.environ.setdefault("BIGQUERY_PROJECT_ID", "test-project")
os.environ.setdefault("BIGQUERY_DATASET", "test-dataset")
os.environ.setdefault("FIREBASE_PROJECT_ID", "test-firebase")

from app.services.cnab_generator import (
    build_header_arquivo,
    build_header_lote,
    build_segmento_a,
    build_segmento_b,
    build_trailer_lote,
    build_trailer_arquivo,
    gerar_cnab240,
)


# ──────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────

PAGAMENTO_BASICO = {
    "lancamento_id": "LAN-001",
    "descricao": "Pagamento Fornecedor",
    "fornecedor_nome": "Fornecedor Teste Ltda",
    "fornecedor_cnpj": "98765432000100",
    "valor": 1234.56,
    "data_vencimento": "2099-04-15",
    "chave_pix_tipo": "02",
    "chave_pix_valor": "pag@fornecedor.com",
}

PAGAMENTO_CHAVE_ALEATORIA = {
    "lancamento_id": "LAN-002",
    "descricao": "Pagamento 2",
    "fornecedor_nome": "Outro Fornecedor SA",
    "fornecedor_cnpj": "11222333000144",
    "valor": 500.00,
    "data_vencimento": "2099-04-20",
    "chave_pix_tipo": "04",
    "chave_pix_valor": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
}

REMESSA_BASICA = {
    "id": "remessa-test-001",
    "status": "APROVADA",
    "criado_por": "joao@empresa.com",
    "pagamentos": [PAGAMENTO_BASICO],
}

REMESSA_MULTIPLOS = {
    "id": "remessa-test-002",
    "status": "APROVADA",
    "criado_por": "joao@empresa.com",
    "pagamentos": [PAGAMENTO_BASICO, PAGAMENTO_CHAVE_ALEATORIA],
}


# ──────────────────────────────────────────
# Testes: tamanho exato de 240 chars
# ──────────────────────────────────────────

def test_header_arquivo_240_chars():
    linha = build_header_arquivo()
    assert len(linha) == 240, f"Header arquivo tem {len(linha)} chars"


def test_header_lote_240_chars():
    linha = build_header_lote(1)
    assert len(linha) == 240, f"Header lote tem {len(linha)} chars"


def test_segmento_a_240_chars():
    linha = build_segmento_a(1, 1, PAGAMENTO_BASICO)
    assert len(linha) == 240, f"Segmento A tem {len(linha)} chars"


def test_segmento_b_240_chars():
    linha = build_segmento_b(1, 2, PAGAMENTO_BASICO)
    assert len(linha) == 240, f"Segmento B tem {len(linha)} chars"


def test_trailer_lote_240_chars():
    linha = build_trailer_lote(1, 4, 123456)
    assert len(linha) == 240, f"Trailer lote tem {len(linha)} chars"


def test_trailer_arquivo_240_chars():
    linha = build_trailer_arquivo(1, 6)
    assert len(linha) == 240, f"Trailer arquivo tem {len(linha)} chars"


# ──────────────────────────────────────────
# Testes: campos fixos corretos
# ──────────────────────────────────────────

def test_header_arquivo_campos_fixos():
    linha = build_header_arquivo()
    assert linha[0:3] == "341", "Banco deve ser 341"
    assert linha[3:7] == "0000", "Lote header arquivo deve ser 0000"
    assert linha[7] == "0", "Tipo registro deve ser 0"
    assert linha[14:17] == "080", "Versão layout (015-017) deve ser 080"
    assert linha[17] == "2", "Tipo inscrição deve ser 2 (CNPJ)"
    assert linha[142] == "1", "Código remessa deve ser 1"
    assert linha[157:166] == "0" * 9, "Pos 158-166 devem ser zeros"
    assert linha[166:171] == "00000", "Densidade (167-171) deve ser 00000"


def test_header_lote_campos_fixos():
    linha = build_header_lote(1)
    assert linha[0:3] == "341", "Banco deve ser 341"
    assert linha[7] == "1", "Tipo registro deve ser 1"
    assert linha[8] == "C", "Tipo operação deve ser C"
    assert linha[9:11] == "20", "Tipo serviço deve ser 20 (Fornecedores)"
    assert linha[11:13] == "45", "Forma pagamento deve ser 45 (Pix)"
    assert linha[13:16] == "040", "Versão lote deve ser 040"


def test_segmento_a_campos_criticos():
    linha = build_segmento_a(1, 1, PAGAMENTO_BASICO)
    assert linha[0:3] == "341", "Banco deve ser 341"
    assert linha[7] == "3", "Tipo registro deve ser 3"
    assert linha[13] == "A", "Segmento deve ser A"
    assert linha[14:17] == "000", "Tipo movimento (015-017) deve ser 000 (inclusão)"
    assert linha[17:20] == "009", "Câmara deve ser 009 (SPI)"
    assert linha[20:23] == "000", "Banco favorecido deve ser 000 para Pix por chave"
    assert linha[101:104] == "REA", "Moeda (102-104) deve ser REA"
    assert linha[112:114] == "04", "Identificação transferência (113-114) deve ser 04 (Chave)"
    assert linha[203:217] == "98765432000100", "CPF/CNPJ favorecido (204-217) deve ser preenchido"


def test_segmento_a_valor_correto():
    linha = build_segmento_a(1, 1, PAGAMENTO_BASICO)
    # Valor 1234.56 = 123456 centavos, em 15 chars = "000000000123456"
    valor_str = linha[119:134]
    assert valor_str == "000000000123456", f"Valor incorreto: {valor_str!r}"


def test_segmento_a_data_formato():
    linha = build_segmento_a(1, 1, PAGAMENTO_BASICO)
    # data_vencimento = "2099-04-15" → DDMMAAAA = "15042099"
    data_str = linha[93:101]
    assert data_str == "15042099", f"Data incorreta: {data_str!r}"


def test_segmento_b_campos_criticos():
    linha = build_segmento_b(1, 2, PAGAMENTO_BASICO)
    assert linha[0:3] == "341", "Banco deve ser 341"
    assert linha[7] == "3", "Tipo registro deve ser 3"
    assert linha[13] == "B", "Segmento deve ser B"

    # Tipo chave email = 02 (pos 15-16, índices 14-15)
    tipo_chave = linha[14:16]
    assert tipo_chave == "02", f"Tipo chave deve ser 02: {tipo_chave!r}"

    assert linha[16] == " ", "Pos 017 deve ser branco"
    assert linha[17] == "2", "Pos 018 deve ser 2 (CNPJ — 14 dígitos no fixture)"

    # CNPJ favorecido (pos 19-32, índices 18-31) = 14 chars
    cnpj_fav = linha[18:32]
    assert cnpj_fav == "98765432000100", f"CNPJ incorreto: {cnpj_fav!r}"

    # Chave Pix (pos 128-227, índices 127-226) = 100 chars
    chave = linha[127:227].rstrip()
    assert chave == "PAG@FORNECEDOR.COM", f"Chave Pix incorreta: {chave!r}"

    # Ocorrências (pos 231-240, índices 230-239) = 10 chars brancos na remessa
    assert linha[230:240] == " " * 10, "Ocorrências (231-240) devem ser brancos"


def test_segmento_b_tipo_inscricao_cpf():
    pagamento_cpf = {**PAGAMENTO_BASICO, "fornecedor_cnpj": "12345678900"}  # 11 dígitos
    linha = build_segmento_b(1, 2, pagamento_cpf)
    assert linha[17] == "1", "Pos 018 deve ser 1 (CPF — 11 dígitos)"


def test_segmento_b_chave_aleatoria():
    linha = build_segmento_b(1, 2, PAGAMENTO_CHAVE_ALEATORIA)
    tipo_chave = linha[14:16]
    assert tipo_chave == "04", f"Tipo chave aleatória deve ser 04: {tipo_chave!r}"

    chave = linha[127:227].rstrip()
    assert chave == "A1B2C3D4-E5F6-7890-ABCD-EF1234567890", f"UUID incorreto: {chave!r}"


def test_trailer_lote_totalizador():
    linha = build_trailer_lote(1, 4, 123456)
    assert linha[7] == "5", "Tipo registro deve ser 5"
    # 123456 centavos em 18 chars = "000000000000123456"
    soma_str = linha[23:41]
    assert soma_str == "000000000000123456", f"Somatória incorreta: {soma_str!r}"


def test_soma_trailer_bate_com_segmentos_a():
    """Valores com meio centavo não podem divergir entre Segmento A e trailer
    (ocorrência TA no Itaú). Soma deve ser feita em centavos por pagamento."""
    pagamentos = [
        {**PAGAMENTO_BASICO, "valor": 1.005},
        {**PAGAMENTO_CHAVE_ALEATORIA, "valor": 1.005},
    ]
    remessa = {**REMESSA_BASICA, "pagamentos": pagamentos}
    conteudo = gerar_cnab240(remessa)
    linhas = [l for l in conteudo.split("\r\n") if l]

    soma_segmentos = sum(
        int(linha[119:134]) for linha in linhas if linha[13] == "A" and linha[7] == "3"
    )
    trailer_lote = [l for l in linhas if l[7] == "5"][0]
    soma_trailer = int(trailer_lote[23:41])
    assert soma_trailer == soma_segmentos, (
        f"Trailer ({soma_trailer}) difere da soma dos Segmentos A ({soma_segmentos})"
    )


def test_trailer_arquivo_campos():
    linha = build_trailer_arquivo(1, 6)
    assert linha[0:3] == "341"
    assert linha[3:7] == "9999", "Lote trailer arquivo deve ser 9999"
    assert linha[7] == "9", "Tipo registro deve ser 9"
    # Qtd lotes = 1
    assert linha[17:23] == "000001"
    # Qtd registros = 6
    assert linha[23:29] == "000006"


# ──────────────────────────────────────────
# Testes: arquivo completo
# ──────────────────────────────────────────

def test_todas_linhas_240_chars():
    conteudo = gerar_cnab240(REMESSA_BASICA)
    linhas = [l for l in conteudo.split("\r\n") if l]
    for i, linha in enumerate(linhas):
        assert len(linha) == 240, f"Linha {i+1} tem {len(linha)} chars: {linha!r}"


def test_estrutura_arquivo_1_pagamento():
    conteudo = gerar_cnab240(REMESSA_BASICA)
    linhas = [l for l in conteudo.split("\r\n") if l]
    # Estrutura: header_arquivo + header_lote + seg_A + seg_B + trailer_lote + trailer_arquivo = 6
    assert len(linhas) == 6, f"Esperado 6 linhas, obtido {len(linhas)}"
    assert linhas[0][7] == "0", "1ª linha deve ser Header Arquivo"
    assert linhas[1][7] == "1", "2ª linha deve ser Header Lote"
    assert linhas[2][13] == "A", "3ª linha deve ser Segmento A"
    assert linhas[3][13] == "B", "4ª linha deve ser Segmento B"
    assert linhas[4][7] == "5", "5ª linha deve ser Trailer Lote"
    assert linhas[5][7] == "9", "6ª linha deve ser Trailer Arquivo"


def test_estrutura_arquivo_2_pagamentos():
    conteudo = gerar_cnab240(REMESSA_MULTIPLOS)
    linhas = [l for l in conteudo.split("\r\n") if l]
    # header_arquivo + header_lote + (seg_A + seg_B) * 2 + trailer_lote + trailer_arquivo = 8
    assert len(linhas) == 8, f"Esperado 8 linhas, obtido {len(linhas)}"


def test_soma_valores_bate():
    conteudo = gerar_cnab240(REMESSA_MULTIPLOS)
    linhas = [l for l in conteudo.split("\r\n") if l]
    trailer_lote = linhas[-2]  # penúltima linha
    assert trailer_lote[7] == "5"
    # Soma: 1234.56 + 500.00 = 1734.56 → 173456 centavos → "000000000000173456"
    soma_str = trailer_lote[23:41]
    assert soma_str == "000000000000173456", f"Soma incorreta: {soma_str!r}"


def test_sem_acentos_no_arquivo():
    pagamento_com_acento = {
        **PAGAMENTO_BASICO,
        "fornecedor_nome": "Fornecedor Ação Ltdá",
    }
    remessa = {**REMESSA_BASICA, "pagamentos": [pagamento_com_acento]}
    conteudo = gerar_cnab240(remessa)
    # Verificar que não há caracteres não-ASCII
    conteudo.encode("ascii")  # Levanta UnicodeEncodeError se houver acentos


def test_remessa_vazia_levanta_erro():
    remessa_vazia = {**REMESSA_BASICA, "pagamentos": []}
    with pytest.raises(ValueError, match="sem pagamentos"):
        gerar_cnab240(remessa_vazia)


def test_qtd_registros_trailer_arquivo():
    conteudo = gerar_cnab240(REMESSA_BASICA)
    linhas = [l for l in conteudo.split("\r\n") if l]
    trailer_arq = linhas[-1]
    qtd_total = int(trailer_arq[23:29])
    assert qtd_total == len(linhas), f"Qtd registros no trailer ({qtd_total}) != linhas ({len(linhas)})"
