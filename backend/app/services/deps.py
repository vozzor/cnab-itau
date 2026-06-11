"""
Provedor de serviços: entrega implementação real ou mock
conforme MOCK_MODE no .env.
"""
from app.config import get_settings
from app.services import mock_service


def _real_firestore():
    from app.services import firestore_service
    return firestore_service


def _real_bigquery():
    from app.services import bigquery_service
    return bigquery_service


def _real_audit():
    from app.services import audit_service
    return audit_service


def get_store():
    """Firestore ou mock — CRUD de fornecedores e remessas."""
    if get_settings().mock_mode:
        return mock_service
    return _real_firestore()


def get_bq():
    """BigQuery ou mock — lançamentos."""
    if get_settings().mock_mode:
        return mock_service
    return _real_bigquery()


def get_audit():
    """Auditoria: Firestore ou mock (silencioso)."""
    if get_settings().mock_mode:
        return mock_service
    return _real_audit()
