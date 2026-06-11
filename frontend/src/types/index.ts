export interface ChavePix {
  tipo: '01' | '02' | '03' | '04'
  valor: string
}

export const TIPO_CHAVE_LABEL: Record<string, string> = {
  '01': 'Telefone',
  '02': 'E-mail',
  '03': 'CPF/CNPJ',
  '04': 'Chave aleatoria',
}

export interface Fornecedor {
  id: string
  nome: string
  cnpj: string
  id_bigquery?: string
  chave_pix?: ChavePix | null
  ativo: boolean
  atualizado_em?: string
  atualizado_por?: string
}

export interface Lancamento {
  id: string
  descricao: string
  valor: number
  data_vencimento: string
  fornecedor_nome: string
  fornecedor_cnpj: string
  status: string
  chave_pix_tipo?: string
  chave_pix_valor?: string
  tem_chave_pix: boolean
}

export interface PagamentoRemessa {
  lancamento_id: string
  descricao: string
  fornecedor_nome: string
  fornecedor_cnpj: string
  valor: number
  data_vencimento: string
  chave_pix_tipo: string
  chave_pix_valor: string
}

export type StatusRemessa =
  | 'RASCUNHO'
  | 'AGUARDANDO_APROVACAO'
  | 'APROVADA'
  | 'DEVOLVIDA'

export interface Remessa {
  id: string
  status: StatusRemessa
  criado_por: string
  criado_em: string
  total_pagamentos: number
  valor_total: number
  pagamentos: PagamentoRemessa[]
  comentario_devolucao?: string
  aprovado_por?: string
  aprovado_em?: string
}

export type UserRole = 'financeiro' | 'gestor'

export interface AuthUser {
  uid: string
  email: string | null
  role: UserRole
}
