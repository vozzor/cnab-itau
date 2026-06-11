"""
Serviço mock para desenvolvimento local sem credenciais GCP/Firebase.
Ativado quando MOCK_MODE=true no .env.
Todos os dados ficam em memória (resetam ao reiniciar o servidor).
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

# ── Fornecedores (chave = id_bigquery/UUID) ───────────────────────
_fornecedores: Dict[str, Dict[str, Any]] = {
    "uuid-001": {
        "cnpj": "12345678000190",
        "nome": "Papelaria Central Ltda",
        "id_bigquery": "uuid-001",
        "chave_pix": {"tipo": "02", "valor": "pag@papelaria.com.br"},
        "ativo": True,
        "atualizado_em": "2026-01-10T00:00:00Z",
        "atualizado_por": "financeiro@dev.local",
    },
    "uuid-002": {
        "cnpj": "98765432000100",
        "nome": "TechSupply Informatica SA",
        "id_bigquery": "uuid-002",
        "chave_pix": {"tipo": "03", "valor": "98765432000100"},
        "ativo": True,
        "atualizado_em": "2026-02-01T00:00:00Z",
        "atualizado_por": "financeiro@dev.local",
    },
    "uuid-003": {
        "cnpj": "11222333000144",
        "nome": "Limpeza Express Servicos",
        "id_bigquery": "uuid-003",
        "chave_pix": None,
        "ativo": True,
        "atualizado_em": "2026-01-15T00:00:00Z",
        "atualizado_por": "sistema",
    },
    "uuid-004": {
        "cnpj": "55566677000188",
        "nome": "Grafica Moderna Ltda",
        "id_bigquery": "uuid-004",
        "chave_pix": {"tipo": "04", "valor": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"},
        "ativo": True,
        "atualizado_em": "2026-03-01T00:00:00Z",
        "atualizado_por": "financeiro@dev.local",
    },
    "uuid-005": {
        "cnpj": "99988877000155",
        "nome": "Distribuidora Norte Sul",
        "id_bigquery": "uuid-005",
        "chave_pix": None,
        "ativo": True,
        "atualizado_em": "2026-01-20T00:00:00Z",
        "atualizado_por": "sistema",
    },
    "uuid-006": {
        "cnpj": "44433322000111",
        "nome": "Construtora Almeida ME",
        "id_bigquery": "uuid-006",
        "chave_pix": {"tipo": "01", "valor": "+5511987654321"},
        "ativo": True,
        "atualizado_em": "2026-02-20T00:00:00Z",
        "atualizado_por": "financeiro@dev.local",
    },
}

# ── Lançamentos (BigQuery mock) ───────────────────────────────────
_lancamentos_base = [
    {
        "id": "LAN-001",
        "descricao": "Compra de material de escritorio",
        "valor": Decimal("1250.00"),
        "data_vencimento": "2026-04-05",
        "fornecedor_nome": "Papelaria Central Ltda",
        "fornecedor_cnpj": "uuid-001",
        "status": "ABERTO",
    },
    {
        "id": "LAN-002",
        "descricao": "Servico de suporte TI - marco",
        "valor": Decimal("3800.00"),
        "data_vencimento": "2026-04-10",
        "fornecedor_nome": "TechSupply Informatica SA",
        "fornecedor_cnpj": "uuid-002",
        "status": "ABERTO",
    },
    {
        "id": "LAN-003",
        "descricao": "Limpeza predial - marco",
        "valor": Decimal("950.00"),
        "data_vencimento": "2026-04-10",
        "fornecedor_nome": "Limpeza Express Servicos",
        "fornecedor_cnpj": "uuid-003",
        "status": "ABERTO",
    },
    {
        "id": "LAN-004",
        "descricao": "Impressao catalogo produto",
        "valor": Decimal("4200.50"),
        "data_vencimento": "2026-04-15",
        "fornecedor_nome": "Grafica Moderna Ltda",
        "fornecedor_cnpj": "uuid-004",
        "status": "ABERTO",
    },
    {
        "id": "LAN-005",
        "descricao": "Frete produtos - lote 42",
        "valor": Decimal("780.00"),
        "data_vencimento": "2026-04-15",
        "fornecedor_nome": "Distribuidora Norte Sul",
        "fornecedor_cnpj": "uuid-005",
        "status": "ABERTO",
    },
    {
        "id": "LAN-006",
        "descricao": "Reforma banheiros andar 3",
        "valor": Decimal("12500.00"),
        "data_vencimento": "2026-04-20",
        "fornecedor_nome": "Construtora Almeida ME",
        "fornecedor_cnpj": "uuid-006",
        "status": "ABERTO",
    },
    {
        "id": "LAN-007",
        "descricao": "Manutencao preventiva AC",
        "valor": Decimal("2100.00"),
        "data_vencimento": "2026-04-25",
        "fornecedor_nome": "TechSupply Informatica SA",
        "fornecedor_cnpj": "uuid-002",
        "status": "ABERTO",
    },
    {
        "id": "LAN-008",
        "descricao": "Compra de toner e cartuchos",
        "valor": Decimal("640.00"),
        "data_vencimento": "2026-04-30",
        "fornecedor_nome": "Papelaria Central Ltda",
        "fornecedor_cnpj": "uuid-001",
        "status": "ABERTO",
    },
]

# ── Remessas ──────────────────────────────────────────────────────
_remessas: Dict[str, Dict[str, Any]] = {}

# ── Usuários ──────────────────────────────────────────────────────
_usuarios: Dict[str, Dict[str, Any]] = {
    "gestor@dev.local": {
        "email": "gestor@dev.local",
        "role": "gestor",
        "atualizado_em": "2026-01-01T00:00:00Z",
        "atualizado_por": "sistema",
    },
    "financeiro@dev.local": {
        "email": "financeiro@dev.local",
        "role": "financeiro",
        "atualizado_em": "2026-01-01T00:00:00Z",
        "atualizado_por": "sistema",
    },
}

# ── Auditoria ─────────────────────────────────────────────────────
_auditoria: List[Dict[str, Any]] = []


# =============================================================================
# Funções mock — mesma assinatura dos serviços reais
# =============================================================================

# Fornecedores
def listar_fornecedores() -> List[Dict[str, Any]]:
    return [{"id": fid, **f} for fid, f in _fornecedores.items() if f["ativo"]]


def obter_fornecedor(fornecedor_id: str) -> Optional[Dict[str, Any]]:
    f = _fornecedores.get(fornecedor_id)
    return {"id": fornecedor_id, **f} if f else None


def obter_fornecedor_por_cnpj(cnpj: str) -> Optional[Dict[str, Any]]:
    for fid, f in _fornecedores.items():
        if f.get("cnpj") == cnpj:
            return {"id": fid, **f}
    return None


def upsert_fornecedor(fornecedor_id: str, dados: Dict[str, Any]) -> None:
    _fornecedores[fornecedor_id] = {**_fornecedores.get(fornecedor_id, {}), **dados}


def atualizar_chave_pix(fornecedor_id: str, tipo: str, valor: str, usuario: str, cnpj: Optional[str] = None) -> None:
    if fornecedor_id not in _fornecedores:
        raise ValueError(f"Fornecedor {fornecedor_id} nao encontrado")
    _fornecedores[fornecedor_id]["chave_pix"] = {"tipo": tipo, "valor": valor}
    _fornecedores[fornecedor_id]["atualizado_em"] = datetime.now(timezone.utc).isoformat()
    _fornecedores[fornecedor_id]["atualizado_por"] = usuario
    if cnpj:
        _fornecedores[fornecedor_id]["cnpj"] = cnpj


def sincronizar_fornecedores(lista: List[Dict[str, Any]]) -> Dict[str, int]:
    criados = 0
    atualizados = 0
    for item in lista:
        fid = item["id_bigquery"]
        if fid not in _fornecedores:
            _fornecedores[fid] = {
                "nome": item["nome"],
                "cnpj": "",
                "id_bigquery": fid,
                "chave_pix": None,
                "ativo": True,
                "atualizado_em": datetime.now(timezone.utc).isoformat(),
                "atualizado_por": "sistema",
            }
            criados += 1
        elif _fornecedores[fid].get("nome") != item["nome"]:
            _fornecedores[fid]["nome"] = item["nome"]
            atualizados += 1
    return {"criados": criados, "atualizados": atualizados}


# Lançamentos
def buscar_lancamentos(data_inicio: str, data_fim: str) -> List[Dict[str, Any]]:
    return [
        {**l, "valor": float(l["valor"])}
        for l in _lancamentos_base
        if data_inicio <= l["data_vencimento"] <= data_fim
    ]


def buscar_fornecedores_bigquery() -> List[Dict[str, Any]]:
    vistos: Dict[str, str] = {}
    for l in _lancamentos_base:
        fid = l["fornecedor_cnpj"]  # UUID no mock
        if fid not in vistos:
            vistos[fid] = l["fornecedor_nome"]
    return [{"id_bigquery": fid, "nome": nome} for fid, nome in vistos.items()]


# Remessas
def criar_remessa(dados: Dict[str, Any]) -> str:
    remessa_id = str(uuid.uuid4())
    _remessas[remessa_id] = {"id": remessa_id, **dados}
    return remessa_id


def obter_remessa(remessa_id: str) -> Optional[Dict[str, Any]]:
    return _remessas.get(remessa_id)


def atualizar_remessa(remessa_id: str, dados: Dict[str, Any]) -> None:
    if remessa_id in _remessas:
        _remessas[remessa_id].update(dados)


def listar_remessas(status: Optional[str] = None) -> List[Dict[str, Any]]:
    remessas = list(_remessas.values())
    if status:
        remessas = [r for r in remessas if r.get("status") == status]
    return sorted(remessas, key=lambda r: r.get("criado_em", ""), reverse=True)


# Usuários
def listar_usuarios() -> List[Dict[str, Any]]:
    return list(_usuarios.values())


def obter_usuario(email: str) -> Optional[Dict[str, Any]]:
    return _usuarios.get(email)


def salvar_usuario(email: str, role: str, criado_por: str) -> None:
    _usuarios[email] = {
        "email": email,
        "role": role,
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "atualizado_por": criado_por,
    }


def remover_usuario(email: str) -> None:
    _usuarios.pop(email, None)


# Auditoria
def registrar_auditoria(acao: str, usuario: str, **kwargs) -> None:
    _auditoria.append({
        "acao": acao,
        "usuario": usuario,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **kwargs,
    })
