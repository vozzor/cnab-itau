from fastapi import APIRouter, HTTPException, UploadFile, File, Body, Depends
from typing import List
import csv
import io
import re
import unicodedata
from app.services.deps import get_store
from app.models.fornecedor import FornecedorUpdate
from app.utils.validators import validate_chave_pix
from app.routers.auth import require_auth


def _normalizar_nome(s: str) -> str:
    """Normaliza nome para match resiliente: sem acentos, lowercase,
    espaços colapsados, sem pontuação comum."""
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(s))
    sem_acento = nfkd.encode("ascii", "ignore").decode("ascii")
    limpo = re.sub(r"[.,&/\-]+", " ", sem_acento)
    return re.sub(r"\s+", " ", limpo).strip().lower()


def _sem_prefixo_numerico(s: str) -> str:
    """Remove prefixo tipo '32.484.343 ' ou '12345 ' antes do nome real
    (padrão Conta Azul para MEIs)."""
    return re.sub(r"^\s*[\d.\-/]+\s+", "", s or "")

router = APIRouter(dependencies=[Depends(require_auth)])


@router.get("", response_model=List[dict])
def listar_fornecedores():
    return get_store().listar_fornecedores()


@router.get("/{fornecedor_id}")
def obter_fornecedor(fornecedor_id: str):
    fornecedor = get_store().obter_fornecedor(fornecedor_id)
    if not fornecedor:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    return fornecedor


@router.put("/{fornecedor_id}/chave-pix")
def atualizar_chave_pix(fornecedor_id: str, body: FornecedorUpdate):
    erro = validate_chave_pix(body.chave_pix.tipo, body.chave_pix.valor)
    if erro:
        raise HTTPException(status_code=422, detail=erro)

    store = get_store()
    if not store.obter_fornecedor(fornecedor_id):
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado. Sincronize primeiro.")

    store.atualizar_chave_pix(
        fornecedor_id,
        body.chave_pix.tipo,
        body.chave_pix.valor,
        body.atualizado_por,
        cnpj=body.cnpj or None,
    )
    return {"message": "Chave Pix atualizada com sucesso"}


@router.post("/importar")
async def importar_csv(file: UploadFile = File(...), usuario: str = Body(...)):
    """Importa chaves Pix em lote via CSV.

    Colunas aceitas: nome, razao_social (opcional), cnpj, cpf.
    O match é resiliente a acentos, caixa, espaços duplos e pontuação,
    e tenta nome OU razão social — útil porque o Conta Azul guarda os dois
    e o BigQuery pode trazer qualquer um deles.
    """
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser CSV")

    contents = await file.read()
    try:
        text = contents.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = contents.decode("cp1252", errors="replace")

    if any(seq in text for seq in ("Ã£", "Ã§", "Ãª", "Ã©", "Ã³", "Ã¡", "Ã­", "Ãº", "Ã‰", "Ã“", "Ã‚", "Ã”")):
        try:
            text = text.encode("cp1252").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass

    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ";" if sample.count(";") > sample.count(",") else ","

    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)

    store = get_store()

    indice: dict[str, list[dict]] = {}
    for f in store.listar_fornecedores():
        nome_db = f.get("nome") or ""
        for variante in {nome_db, _sem_prefixo_numerico(nome_db)}:
            chave = _normalizar_nome(variante)
            if chave and f not in indice.setdefault(chave, []):
                indice[chave].append(f)

    erros = []
    atualizados = 0

    for i, row in enumerate(reader, start=2):
        normalized = {(k or "").strip().lower(): v for k, v in row.items()}
        nome = (normalized.get("nome") or "").strip()
        razao = (
            normalized.get("razao_social")
            or normalized.get("razão social")
            or normalized.get("razao social")
            or ""
        ).strip()
        cnpj = re.sub(r"\D", "", normalized.get("cnpj") or "")
        cpf = re.sub(r"\D", "", normalized.get("cpf") or "")

        if not nome and not razao:
            erros.append({"linha": i, "erro": "Nome ou Razão Social obrigatório"})
            continue

        documento = cnpj or cpf
        if not documento:
            erros.append({"linha": i, "nome": nome or razao, "erro": "Informe CNPJ ou CPF"})
            continue

        if cnpj and len(cnpj) != 14:
            erros.append({"linha": i, "nome": nome or razao, "erro": f"CNPJ inválido ({len(cnpj)} dígitos, esperado 14)"})
            continue
        if not cnpj and len(cpf) != 11:
            erros.append({"linha": i, "nome": nome or razao, "erro": f"CPF inválido ({len(cpf)} dígitos, esperado 11)"})
            continue

        chaves_tentadas: list[str] = []
        for origem in (nome, razao, _sem_prefixo_numerico(nome), _sem_prefixo_numerico(razao)):
            k = _normalizar_nome(origem)
            if k and k not in chaves_tentadas:
                chaves_tentadas.append(k)

        candidatos: list[dict] = []
        for chave in chaves_tentadas:
            achados = indice.get(chave, [])
            if achados:
                candidatos = achados
                break

        if not candidatos:
            label = nome or razao
            erros.append({"linha": i, "nome": label, "erro": "Fornecedor não encontrado (sincronize o BigQuery primeiro)"})
            continue
        if len(candidatos) > 1:
            label = nome or razao
            erros.append({"linha": i, "nome": label, "erro": f"{len(candidatos)} fornecedores com este nome — edite manualmente"})
            continue

        fornecedor = candidatos[0]
        store.atualizar_chave_pix(fornecedor["id"], "03", documento, usuario, cnpj=documento)
        atualizados += 1

    return {"atualizados": atualizados, "erros": erros, "total_erros": len(erros)}
