# CNAB 240 — Integração Bancária Itaú (SISPAG)

Sistema full-stack para geração de remessas de pagamento em lote no padrão **CNAB 240 do Itaú (SISPAG)**. Implementa o ciclo completo: cadastro de fornecedores, lançamento de pagamentos, fluxo de aprovação, geração do arquivo e trilha de auditoria.

> CNAB 240 é o padrão técnico do Banco Central do Brasil para arquivos de transferência bancária em lote. A especificação do Itaú SISPAG define posições fixas de bytes, segmentos (A, B) e regras de validação para cada tipo de pagamento — tornando a implementação um exercício preciso de parsing e geração de texto estruturado.

## Funcionalidades

- Geração de arquivos CNAB 240 válidos para pagamento de fornecedores via Pix Transferência por chave (segmentos A e B)
- Cadastro de fornecedores com validação de CPF/CNPJ e dados bancários
- Fluxo de aprovação em duas etapas — lançamento precisa ser aprovado antes da remessa
- Trilha de auditoria completa de todas as operações com timestamp e usuário
- Autenticação Firebase com lista de e-mails autorizados
- Persistência em BigQuery (histórico/auditoria) e Firestore (dados operacionais)

## Arquitetura

```
Frontend (React + TypeScript + Tailwind)
        │  REST API
        ▼
Backend (FastAPI + Pydantic)
        │
        ├── Firestore         → fornecedores, lançamentos, remessas
        ├── BigQuery          → trilha de auditoria
        ├── Firebase Auth     → autenticação e autorização
        └── CNAB Generator    → montagem do arquivo posicional
```

## Fluxo de uso

```
1. Cadastrar fornecedor  →  validação CPF/CNPJ + dados bancários
2. Criar lançamento      →  valor, data, forma de pagamento
3. Aprovar lançamento    →  segundo usuário autorizado confirma
4. Gerar remessa         →  sistema monta o arquivo CNAB 240
5. Download do arquivo   →  enviado ao internet banking do Itaú
```

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python, FastAPI, Pydantic |
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Dados | Google BigQuery, Firestore |
| Auth | Firebase Authentication |
| Infra | Docker, Nginx, Google Cloud Run |
| Testes | pytest |

## Como rodar

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# preencha as variáveis nos dois arquivos .env

docker-compose up --build
```

- Frontend: http://localhost:3000
- API + Swagger: http://localhost:8000/docs

## Testes

```bash
cd backend && pytest
```

Os testes cobrem a geração do arquivo CNAB — verificam posições de campos, tamanho de registros e cálculo de totalizadores.

> Projeto desenvolvido para uso real em ambiente corporativo. Credenciais e dados da empresa foram removidos desta versão pública.
