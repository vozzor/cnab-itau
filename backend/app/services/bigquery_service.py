import os
from typing import List
from google.cloud import bigquery
from app.config import get_settings


def get_bigquery_client() -> bigquery.Client:
    settings = get_settings()
    if settings.google_application_credentials:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials
    return bigquery.Client(project=settings.bigquery_project_id)


def buscar_lancamentos(data_inicio: str, data_fim: str) -> List[dict]:
    """
    Busca parcelas de despesas em aberto (PENDENTE ou ATRASADO) no período.
    Retorna lista de dicts compatível com o model Lancamento.

    Nota: fornecedor_cnpj usa o UUID do fornecedor no sistema como chave de
    lookup no Firestore — o CNPJ real é cadastrado manualmente via tela de
    Fornecedores.
    """
    settings = get_settings()
    client = get_bigquery_client()
    dataset = f"{settings.bigquery_project_id}.{settings.bigquery_dataset}"

    query = f"""
        SELECT
            p.id                                            AS id,
            COALESCE(p.descricao, d.descricao, '(sem descricao)') AS descricao,
            CAST(COALESCE(
                NULLIF(p.valor_total_liquido, ''),
                NULLIF(p.valor_composicao__valor_liquido, ''),
                NULLIF(p.valor_composicao__valor_bruto, ''),
                '0'
            ) AS FLOAT64)                                   AS valor,
            CAST(p.data_vencimento AS DATE)                 AS data_vencimento,
            COALESCE(d.fornecedor__nome, '(sem fornecedor)') AS fornecedor_nome,
            COALESCE(d.fornecedor__id, p._pk_despesas) AS fornecedor_id
        FROM `{dataset}.parcelas_despesas` p
        JOIN `{dataset}.despesas` d
          ON p._pk_despesas = d._pk
        WHERE p.status IN ('PENDENTE', 'ATRASADO')
          AND p._deleted_at IS NULL
          AND d._deleted_at IS NULL
          AND CAST(p.data_vencimento AS DATE) BETWEEN @data_inicio AND @data_fim
        ORDER BY data_vencimento ASC
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("data_inicio", "DATE", data_inicio),
            bigquery.ScalarQueryParameter("data_fim", "DATE", data_fim),
        ]
    )

    results = client.query(query, job_config=job_config).result()

    lancamentos = []
    for row in results:
        lancamentos.append({
            "id": row.id,
            "descricao": row.descricao,
            "valor": row.valor or 0.0,
            "data_vencimento": str(row.data_vencimento),
            "fornecedor_nome": row.fornecedor_nome,
            # Usamos o UUID do fornecedor como chave de lookup no Firestore.
            # O CNPJ real fica armazenado no documento Firestore pelo usuário.
            "fornecedor_cnpj": row.fornecedor_id or "",
            "status": "ABERTO",
        })
    return lancamentos


def buscar_fornecedores_bigquery() -> List[dict]:
    """
    Busca fornecedores distintos das despesas para sincronizar com Firestore.
    Usa o UUID do fornecedor como id_bigquery (chave de lookup).
    """
    settings = get_settings()
    client = get_bigquery_client()
    dataset = f"{settings.bigquery_project_id}.{settings.bigquery_dataset}"

    query = f"""
        SELECT
            d.fornecedor__id   AS id_bigquery,
            MAX(COALESCE(d.fornecedor__nome, '(sem nome)')) AS nome
        FROM `{dataset}.despesas` d
        WHERE d._deleted_at IS NULL
          AND d.fornecedor__id IS NOT NULL
          AND d.fornecedor__id != ''
        GROUP BY d.fornecedor__id
        ORDER BY nome
    """

    results = client.query(query).result()
    return [
        {"id_bigquery": row.id_bigquery, "nome": row.nome}
        for row in results
    ]
