# CNAB 240 — Integração Bancária Itaú (SISPAG)

Sistema completo para geração de remessas de pagamento em lote no padrão **CNAB 240 do Itaú (SISPAG)**, com fluxo de aprovação, auditoria e persistência em nuvem.

## Funcionalidades

- Geração de arquivos de remessa CNAB 240 (pagamentos a fornecedores)
- Cadastro de fornecedores com validação de CPF/CNPJ e dados bancários
- Fluxo de aprovação de lançamentos antes da geração da remessa
- Trilha de auditoria de todas as operações
- Autenticação via Firebase com lista de e-mails autorizados
- Dados em Google BigQuery e Firestore

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python, FastAPI, Pydantic |
| Frontend | React, TypeScript, Vite, Tailwind |
| Dados | Google BigQuery, Firestore |
| Auth | Firebase Authentication |
| Infra | Docker, Google Cloud Run, Nginx |
| Testes | pytest |

## Como rodar

```bash
# configurar variáveis (ver .env.example em backend/ e frontend/)
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

docker-compose up --build
# Frontend: http://localhost:3000 | API: http://localhost:8000/docs
```

## Testes

```bash
cd backend && pytest
```

> Projeto desenvolvido para uso real em ambiente corporativo; credenciais e dados da empresa foram removidos desta versão pública.
