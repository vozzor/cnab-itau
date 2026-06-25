import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import lancamentos, fornecedores, remessas, auth, usuarios

app = FastAPI(
    title="CNAB Pix API",
    description="Sistema de pagamentos via Pix com geração de CNAB 240 Itaú SISPAG (layout 080)",
    version="1.0.0",
)

# Origens permitidas no CORS: lidas de CORS_ORIGINS (separadas por vírgula),
# com fallback para os endereços de desenvolvimento local.
_default_origins = "http://localhost:5173,http://localhost:3000"
cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(lancamentos.router, prefix="/lancamentos", tags=["Lançamentos"])
app.include_router(fornecedores.router, prefix="/fornecedores", tags=["Fornecedores"])
app.include_router(remessas.router, prefix="/remessas", tags=["Remessas"])
app.include_router(usuarios.router, prefix="/usuarios", tags=["Usuários"])


@app.get("/health")
def health():
    return {"status": "ok"}
