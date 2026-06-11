import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getRemessas, getRemessa, downloadCnab } from '../services/api'
import type { Remessa, StatusRemessa } from '../types'

function formatCurrency(value: number) {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function formatDate(iso: string) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleDateString('pt-BR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
    })
  } catch {
    return iso
  }
}

const STATUS_CONFIG: Record<StatusRemessa, { label: string; color: string }> = {
  RASCUNHO: { label: 'Rascunho', color: 'bg-gray-100 text-gray-700' },
  AGUARDANDO_APROVACAO: { label: 'Aguardando Aprovação', color: 'bg-yellow-100 text-yellow-800' },
  APROVADA: { label: 'Aprovada', color: 'bg-green-100 text-green-800' },
  DEVOLVIDA: { label: 'Devolvida', color: 'bg-red-100 text-red-800' },
}

function StatusBadge({ status }: { status: StatusRemessa }) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.RASCUNHO
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${config.color}`}>
      {config.label}
    </span>
  )
}

export default function Remessas() {
  const [remessas, setRemessas] = useState<Remessa[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [detalhe, setDetalhe] = useState<Remessa | null>(null)
  const [downloading, setDownloading] = useState(false)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const res = await getRemessas()
        setRemessas(res.data)
        // Abre automaticamente a mais recente devolvida, se houver
        const devolvida = res.data.find((r: Remessa) => r.status === 'DEVOLVIDA')
        if (devolvida) {
          setSelectedId(devolvida.id)
          const det = await getRemessa(devolvida.id)
          setDetalhe(det.data)
        }
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

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

  const handleDownload = async (id: string) => {
    setDownloading(true)
    try {
      await downloadCnab(id)
    } finally {
      setDownloading(false)
    }
  }

  const devolvidas = remessas.filter((r) => r.status === 'DEVOLVIDA')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Minhas Remessas</h1>
        <p className="text-sm text-gray-500 mt-1">
          Acompanhe o status das remessas que você enviou
        </p>
      </div>

      {/* Alerta de remessas devolvidas */}
      {devolvidas.length > 0 && (
        <div className="rounded-lg bg-red-50 border border-red-300 p-4">
          <div className="flex items-start gap-3">
            <span className="text-red-500 text-lg mt-0.5">&#9888;</span>
            <div>
              <p className="text-sm font-semibold text-red-800">
                {devolvidas.length} remessa(s) devolvida(s) pelo gestor
              </p>
              <p className="text-sm text-red-700 mt-1">
                Clique na remessa para ver o motivo e crie uma nova remessa corrigida.
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-5">
        {/* Lista */}
        <div className="lg:col-span-2 card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-700">Remessas</h2>
            <Link to="/nova-remessa" className="btn-primary text-xs py-1 px-3">
              + Nova remessa
            </Link>
          </div>

          {loading ? (
            <div className="py-8 text-center text-gray-400 text-sm">Carregando...</div>
          ) : remessas.length === 0 ? (
            <div className="py-12 text-center space-y-3">
              <p className="text-gray-400 text-sm">Nenhuma remessa criada ainda.</p>
              <Link to="/nova-remessa" className="btn-primary text-sm inline-block">
                Criar primeira remessa
              </Link>
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
                        : r.status === 'DEVOLVIDA'
                        ? 'border-red-200 bg-red-50 hover:border-red-300'
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
                      {r.total_pagamentos} pagamento(s) &bull; {formatDate(r.criado_em)}
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
                  <h2 className="text-lg font-semibold text-gray-900">Detalhes da Remessa</h2>
                  <p className="text-xs font-mono text-gray-400 mt-0.5">{detalhe.id}</p>
                </div>
                <StatusBadge status={detalhe.status} />
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-gray-500">Data de criação</span>
                  <p className="font-medium">{formatDate(detalhe.criado_em)}</p>
                </div>
                <div>
                  <span className="text-gray-500">Pagamentos</span>
                  <p className="font-medium">{detalhe.total_pagamentos}</p>
                </div>
                <div className="col-span-2">
                  <span className="text-gray-500">Valor total</span>
                  <p className="font-bold text-blue-700 text-lg">
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
                      <p className="font-medium">{formatDate(detalhe.aprovado_em ?? '')}</p>
                    </div>
                  </>
                )}
              </div>

              {/* Comentário de devolução em destaque */}
              {detalhe.comentario_devolucao && (
                <div className="rounded-lg bg-red-50 border border-red-300 p-4">
                  <p className="text-xs font-bold text-red-700 uppercase tracking-wide mb-2">
                    Motivo da devolução pelo gestor
                  </p>
                  <p className="text-sm text-red-800">{detalhe.comentario_devolucao}</p>
                  <div className="mt-3">
                    <Link
                      to="/nova-remessa"
                      className="inline-flex items-center gap-1 text-sm font-medium text-red-700 underline hover:text-red-900"
                    >
                      Criar nova remessa corrigida →
                    </Link>
                  </div>
                </div>
              )}

              {/* Tabela de pagamentos */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Pagamentos</h3>
                <div className="overflow-x-auto rounded-lg border border-gray-200">
                  <table className="min-w-full text-sm">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        <th className="table-header">Fornecedor</th>
                        <th className="table-header text-right">Valor</th>
                        <th className="table-header">Vencimento</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {detalhe.pagamentos.map((p, i) => (
                        <tr key={i} className="hover:bg-gray-50">
                          <td className="table-cell">
                            <div className="font-medium">{p.fornecedor_nome}</div>
                            <div className="text-xs font-mono text-gray-400">{p.fornecedor_cnpj}</div>
                          </td>
                          <td className="table-cell text-right font-mono font-medium">
                            {formatCurrency(p.valor)}
                          </td>
                          <td className="table-cell">{formatDate(p.data_vencimento)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Ação: download CNAB */}
              {detalhe.status === 'APROVADA' && (
                <div className="pt-2 border-t border-gray-100">
                  <div className="rounded-lg bg-green-50 border border-green-200 p-4 flex items-center justify-between gap-4">
                    <div>
                      <p className="text-sm font-semibold text-green-800">
                        Remessa aprovada!
                      </p>
                      <p className="text-xs text-green-700 mt-0.5">
                        Baixe o arquivo .rem e importe no Itaú internet banking.
                      </p>
                    </div>
                    <button
                      onClick={() => handleDownload(detalhe.id)}
                      disabled={downloading}
                      className="btn-primary whitespace-nowrap"
                    >
                      {downloading ? 'Baixando...' : 'Baixar .rem'}
                    </button>
                  </div>
                </div>
              )}

              {detalhe.status === 'AGUARDANDO_APROVACAO' && (
                <div className="pt-2 border-t border-gray-100">
                  <div className="rounded-lg bg-yellow-50 border border-yellow-200 p-3 text-sm text-yellow-800">
                    Aguardando aprovação do gestor. Você será notificado quando houver retorno.
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
