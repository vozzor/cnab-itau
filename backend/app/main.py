from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import lancamentos, fornecedores, remessas, auth, usuarios

app = FastAPI(
    title="CNAB Pix API",
    description="Sistema de pagamentos via Pix com geração de CNAB 240 Itaú SISPAG v085",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://SEU-FRONTEND.run.app",
    ],
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
