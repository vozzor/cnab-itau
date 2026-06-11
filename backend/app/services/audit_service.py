from datetime import datetime, timezone
from typing import Optional
from app.services.firestore_service import get_firestore_client


def registrar_auditoria(
    acao: str,
    usuario: str,
    remessa_id: Optional[str] = None,
    valor_total: Optional[float] = None,
    qtd_pagamentos: Optional[int] = None,
    detalhes: Optional[dict] = None,
) -> None:
    db = get_firestore_client()
    log = {
        "acao": acao,
        "usuario": usuario,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if remessa_id:
        log["remessa_id"] = remessa_id
    if valor_total is not None:
        log["valor_total"] = valor_total
    if qtd_pagamentos is not None:
        log["qtd_pagamentos"] = qtd_pagamentos
    if detalhes:
        log["detalhes"] = detalhes

    db.collection("auditoria").add(log)
