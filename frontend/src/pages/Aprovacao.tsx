import { useEffect, useState } from 'react'
import {
  getRemessas,
  getRemessa,
  aprovarRemessa,
  devolverRemessa,
  downloadCnab,
} from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import type { Remessa, StatusRemessa } from '../types'
import { TIPO_CHAVE_LABEL } from '../types'

function formatCurrency(value: number) {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function formatDate(iso: string) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    })
  } catch {
    return iso
  }
}

const STATUS_CONFIG: Record<
  StatusRemessa,
  { label: string; color: string }
> = {
  RASCUNHO: { label: 'Rascunho', color: 'bg-gray-100 text-gray-700' },
  AGUARDANDO_APROVACAO: {
    label: 'Aguardando Aprovação',
    color: 'bg-yellow-100 text-yellow-800',
  },
  APROVADA: { label: 'Aprovada', color: 'bg-green-100 text-green-800' },
  DEVOLVIDA: { label: 'Devolvida', color: 'bg-red-100 text-red-800' },
}

function StatusBadge({ status }: { status: StatusRemessa }) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.RASCUNHO
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${config.color}`}
    >
      {config.label}
    </span>
  )
}

interface DevolverModalProps {
  remessaId: string
  onClose: () => void
  onConfirm: (comentario: string) => Promise<void>
}

function DevolverModal({ remessaId, onClose, onConfirm }: DevolverModalProps) {
  const [comentario, setComentario] = useState('')
  const [loading, setLoading] = useState(false)

  const handleConfirm = async () => {
    if (!comentario.trim()) return
    setLoading(true)
    try {
      await onConfirm(comentario)
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white shadow-2xl">
        <div className="p-6 border-b border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900">
            Devolver remessa
          </h3>
          <p className="text-sm text-gray-500 mt-1">ID: {remessaId}</p>
        </div>
        <div className="p-6">
          <label className="label">Comentário / motivo da devolução</label>
          <textarea
            className="input min-h-[100px] resize-none"
            value={comentario}
            onChange={(e) => setComentario(e.target.value)}
            placeholder="Descreva o motivo da devolução..."
            autoFocus
          />
        </div>
        <div className="flex justify-end gap-3 p-6 border-t border-gray-100">
          <button onClick={onClose} className="btn-secondary">
            Cancelar
          </button>
          <button
            onClick={handleConfirm}
            disabled={!comentario.trim() || loading}
            className="btn-danger"
          >
            {loading ? 'Devolvendo...' : 'Devolver'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Aprovacao() {
  const { user } = useAuth()
  const [remessas, setRemessas] = useState<Remessa[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [detalhe, setDetalhe] = useState<Remessa | null>(null)
  const [devolverModal, setDevolverModal] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState(false)

  const [filtroStatus, setFiltroStatus] = useState<string>('AGUARDANDO_APROVACAO')

  const loadRemessas = async (status: string) => {
    setLoading(true)
    try {
      const res = await getRemessas(status || undefined)
      setRemessas(res.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadRemessas(filtroStatus)
  }, [filtroStatus])

  const handleSelect = async (id: string) => {
    if (selectedId === id) {
      setSelectedId(null)
      setDetalhe(null)
      return
    }
    setSelectedId(id)
    const res = await getRemessa(id)
    setDetalhe(res.data)
  }

  const handleAprovar = async (id: string) => {
    setActionLoading(true)
    try {
      await aprovarRemessa(id, user?.email ?? 'gestor')
      await loadRemessas(filtroStatus)
      const res = await getRemessa(id)
      setDetalhe(res.data)
    } finally {
      setActionLoading(false)
    }
  }

  const handleDevolver = async (id: string, comentario: string) => {
    await devolverRemessa(id, user?.email ?? 'gestor', comentario)
    await loadRemessas(filtroStatus)
    const res = await getRemessa(id)
    setDetalhe(res.data)
  }

  const handleDownload = async (id: string) => {
    await downloadCnab(id)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Aprovação de Remessas
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Revise e aprove as remessas Pix enviadas pelo financeiro.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        {/* Lista de remessas */}
        <div className="lg:col-span-2 card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-700">Remessas</h2>
            <select
              className="text-xs border border-gray-200 rounded-md px-2 py-1 text-gray-600"
              value={filtroStatus}
              onChange={(e) => {
                setSelectedId(null)
                setDetalhe(null)
                setFiltroStatus(e.target.value)
              }}
            >
              <option value="AGUARDANDO_APROVACAO">Aguardando Aprovação</option>
              <option value="APROVADA">Aprovadas</option>
              <option value="DEVOLVIDA">Devolvidas</option>
              <option value="">Todas</option>
            </select>
          </div>
          {loading ? (
            <div className="py-8 text-center text-gray-400 text-sm">
              Carregando...
            </div>
          ) : remessas.length === 0 ? (
            <div className="py-8 text-center text-gray-400 text-sm">
              Nenhuma remessa encontrada.
            </div>
          ) : (
            <ul className="space-y-2">
              {remessas.map((r) => (
                <li key={r.id}>
                  <button
                    onClick={() => handleSelect(r.id)}
                    className={`w-full text-left rounded-lg p-3 border transition-colors ${
                      selectedId === r.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-mono text-gray-500">
                        {r.id.slice(0, 8)}...
                      </span>
                      <StatusBadge status={r.status} />
                    </div>
                    <div className="text-sm font-medium text-gray-800">
                      {formatCurrency(r.valor_total)}
                    </div>
                    <div className="text-xs text-gray-500">
                      {r.total_pagamentos} pagamento(s) &bull;{' '}
                      {formatDate(r.criado_em)}
                    </div>
                    <div className="text-xs text-gray-400 mt-0.5">
                      por {r.criado_por}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Detalhe */}
        <div className="lg:col-span-3">
          {!detalhe ? (
            <div className="card h-full flex items-center justify-center min-h-[300px]">
              <p className="text-gray-400 text-sm">
                Selecione uma remessa para ver os detalhes
              </p>
            </div>
          ) : (
            <div className="card space-y-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">
                    Detalhes da Remessa
                  </h2>
                  <p className="text-xs font-mono text-gray-400 mt-0.5">
                    {detalhe.id}
                  </p>
                </div>
                <StatusBadge status={detalhe.status} />
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-gray-500">Preparada por</span>
                  <p className="font-medium">{detalhe.criado_por}</p>
                </div>
                <div>
                  <span className="text-gray-500">Data</span>
                  <p className="font-medium">{formatDate(detalhe.criado_em)}</p>
                </div>
                <div>
                  <span className="text-gray-500">Pagamentos</span>
                  <p className="font-medium">{detalhe.total_pagamentos}</p>
                </div>
                <div>
                  <span className="text-gray-500">Valor total</span>
                  <p className="font-bold text-blue-700 text-base">
                    {formatCurrency(detalhe.valor_total)}
                  </p>
                </div>
                {detalhe.aprovado_por && (
                  <>
                    <div>
                      <span className="text-gray-500">Aprovada por</span>
                      <p className="font-medium">{detalhe.aprovado_por}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Aprovada em</span>
                      <p className="font-medium">
                        {formatDate(detalhe.aprovado_em ?? '')}
                      </p>
                    </div>
                  </>
                )}
              </div>

              {detalhe.comentario_devolucao && (
                <div className="rounded-lg bg-red-50 border border-red-200 p-3">
                  <p className="text-xs font-semibold text-red-700 mb-1">
                    Motivo da devolução
                  </p>
                  <p className="text-sm text-red-700">
                    {detalhe.comentario_devolucao}
                  </p>
                </div>
              )}

              {/* Tabela de pagamentos */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-2">
                  Pagamentos
                </h3>
                <div className="overflow-x-auto rounded-lg border border-gray-200">
                  <table className="min-w-full text-sm">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        <th className="table-header">Fornecedor</th>
                        <th className="table-header text-right">Valor</th>
                        <th className="table-header">Vencimento</th>
                        <th className="table-header">Chave Pix</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {detalhe.pagamentos.map((p, i) => (
                        <tr key={i} className="hover:bg-gray-50">
                          <td className="table-cell">
                            <div className="font-medium">
                              {p.fornecedor_nome}
                            </div>
                            <div className="text-xs font-mono text-gray-400">
                              {p.fornecedor_cnpj}
                            </div>
                          </td>
                          <td className="table-cell text-right font-mono font-medium">
                            {formatCurrency(p.valor)}
                          </td>
                          <td className="table-cell">
                            {formatDate(p.data_vencimento)}
                          </td>
                          <td className="table-cell">
                            <div className="text-xs text-gray-500">
                              {TIPO_CHAVE_LABEL[p.chave_pix_tipo]}
                            </div>
                            <div className="text-xs font-mono text-gray-700 truncate max-w-[160px]">
                              {p.chave_pix_valor}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Acoes */}
              <div className="flex flex-wrap gap-3 pt-2 border-t border-gray-100">
                {detalhe.status === 'AGUARDANDO_APROVACAO' && (
                  <>
                    <button
                      onClick={() => handleAprovar(detalhe.id)}
                      disabled={actionLoading}
                      className="btn-success"
                    >
                      {actionLoading ? 'Aprovando...' : 'Aprovar'}
                    </button>
                    <button
                      onClick={() => setDevolverModal(detalhe.id)}
                      disabled={actionLoading}
                      className="btn-danger"
                    >
                      Devolver com comentário
                    </button>
                  </>
                )}
                {detalhe.status === 'APROVADA' && (
                  <button
                    onClick={() => handleDownload(detalhe.id)}
                    className="btn-primary"
                  >
                    Baixar arquivo .rem
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {devolverModal && (
        <DevolverModal
          remessaId={devolverModal}
          onClose={() => setDevolverModal(null)}
          onConfirm={(comentario) =>
            handleDevolver(devolverModal, comentario)
          }
        />
      )}
    </div>
  )
}
