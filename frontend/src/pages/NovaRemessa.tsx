import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { getLancamentos, criarRemessa, solicitarAprovacao } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import type { Lancamento, PagamentoRemessa } from '../types'
import { TIPO_CHAVE_LABEL } from '../types'

function formatCurrency(value: number) {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function formatDate(iso: string) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

export default function NovaRemessa() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const [dataInicio, setDataInicio] = useState('')
  const [dataFim, setDataFim] = useState('')
  const [lancamentos, setLancamentos] = useState<Lancamento[]>([])
  const [selecionados, setSelecionados] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const buscarLancamentos = async () => {
    if (!dataInicio || !dataFim) {
      setError('Selecione o período')
      return
    }
    setError('')
    setLoading(true)
    setSelecionados(new Set())
    try {
      const res = await getLancamentos(dataInicio, dataFim)
      setLancamentos(res.data)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      setError(err?.response?.data?.detail ?? 'Erro ao buscar lançamentos')
    } finally {
      setLoading(false)
    }
  }

  const toggleSelecionado = (id: string, temChave: boolean) => {
    if (!temChave) return
    setSelecionados((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleTodos = () => {
    const comChave = lancamentos
      .filter((l) => l.tem_chave_pix)
      .map((l) => l.id)
    if (selecionados.size === comChave.length) {
      setSelecionados(new Set())
    } else {
      setSelecionados(new Set(comChave))
    }
  }

  const lancamentosSelecionados = lancamentos.filter((l) =>
    selecionados.has(l.id),
  )
  const valorTotal = lancamentosSelecionados.reduce(
    (sum, l) => sum + l.valor,
    0,
  )
  const semChave = lancamentos.filter((l) => !l.tem_chave_pix)
  const comChave = lancamentos.filter((l) => l.tem_chave_pix)

  // Fornecedores únicos sem chave (deduplificado por id, ignorando sem nome)
  const fornecedoresSemChave = Array.from(
    new Map(
      semChave
        .filter((l) => l.fornecedor_nome && l.fornecedor_cnpj)
        .map((l) => [l.fornecedor_cnpj, l.fornecedor_nome])
    ).entries()
  )

  const handleCriarESolicitar = async () => {
    if (selecionados.size === 0) {
      setError('Selecione ao menos um lançamento')
      return
    }
    setSaving(true)
    setError('')
    try {
      const pagamentos: PagamentoRemessa[] = lancamentosSelecionados.map(
        (l) => ({
          lancamento_id: l.id,
          descricao: l.descricao,
          fornecedor_nome: l.fornecedor_nome,
          fornecedor_cnpj: l.fornecedor_cnpj,
          valor: l.valor,
          data_vencimento: l.data_vencimento,
          chave_pix_tipo: l.chave_pix_tipo!,
          chave_pix_valor: l.chave_pix_valor!,
        }),
      )

      const res = await criarRemessa(pagamentos)
      const remessaId: string = res.data.id
      await solicitarAprovacao(remessaId, user?.email ?? 'sistema')
      navigate('/remessas')
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      setError(err?.response?.data?.detail ?? 'Erro ao criar remessa')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Nova Remessa Pix</h1>
        <p className="text-sm text-gray-500 mt-1">
          Selecione o período e os lançamentos para pagamento
        </p>
      </div>

      {/* Filtro período */}
      <div className="card">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">
          Periodo de vencimento
        </h2>
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="label">Data inicial</label>
            <input
              type="date"
              className="input"
              value={dataInicio}
              onChange={(e) => setDataInicio(e.target.value)}
            />
          </div>
          <div>
            <label className="label">Data final</label>
            <input
              type="date"
              className="input"
              value={dataFim}
              onChange={(e) => setDataFim(e.target.value)}
            />
          </div>
          <button
            onClick={buscarLancamentos}
            disabled={loading}
            className="btn-primary"
          >
            {loading ? 'Buscando...' : 'Buscar lançamentos'}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Alerta fornecedores sem chave */}
      {fornecedoresSemChave.length > 0 && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 p-4">
          <div className="flex items-start gap-3">
            <span className="text-amber-500 text-lg mt-0.5">&#9888;</span>
            <div>
              <p className="text-sm font-medium text-amber-800">
                {fornecedoresSemChave.length} fornecedor(es) sem chave Pix — não podem ser
                incluídos na remessa.
              </p>
              <ul className="mt-2 space-y-1">
                {fornecedoresSemChave.map(([id, nome]) => (
                  <li
                    key={id}
                    className="text-sm text-amber-700 flex items-center gap-2"
                  >
                    <span>{nome}</span>
                    <Link
                      to="/fornecedores"
                      className="text-xs underline text-amber-900 hover:text-amber-700"
                    >
                      Cadastrar chave
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Tabela de lançamentos */}
      {lancamentos.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-700">
              Lançamentos ({lancamentos.length} encontrados,{' '}
              {comChave.length} disponíveis)
            </h2>
            {comChave.length > 0 && (
              <button
                onClick={toggleTodos}
                className="text-sm text-blue-700 hover:underline"
              >
                {selecionados.size === comChave.length
                  ? 'Desmarcar todos'
                  : 'Selecionar todos disponíveis'}
              </button>
            )}
          </div>

          <div className="overflow-x-auto -mx-6">
            <table className="min-w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="table-header w-10"></th>
                  <th className="table-header">Fornecedor</th>
                  <th className="table-header">Descricao</th>
                  <th className="table-header">Vencimento</th>
                  <th className="table-header text-right">Valor</th>
                  <th className="table-header">Chave Pix</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {lancamentos.map((l) => (
                  <tr
                    key={l.id}
                    onClick={() => toggleSelecionado(l.id, l.tem_chave_pix)}
                    className={`transition-colors ${
                      l.tem_chave_pix
                        ? 'cursor-pointer hover:bg-blue-50'
                        : 'opacity-50 cursor-not-allowed bg-gray-50'
                    } ${selecionados.has(l.id) ? 'bg-blue-50' : ''}`}
                  >
                    <td className="table-cell">
                      <input
                        type="checkbox"
                        checked={selecionados.has(l.id)}
                        disabled={!l.tem_chave_pix}
                        readOnly
                        className="rounded border-gray-300 text-blue-600"
                      />
                    </td>
                    <td className="table-cell">
                      <div className="font-medium">{l.fornecedor_nome}</div>
                      <div className="text-xs text-gray-400 font-mono">
                        {l.fornecedor_cnpj}
                      </div>
                    </td>
                    <td className="table-cell text-gray-500">{l.descricao}</td>
                    <td className="table-cell">
                      {formatDate(l.data_vencimento)}
                    </td>
                    <td className="table-cell text-right font-mono font-medium">
                      {formatCurrency(l.valor)}
                    </td>
                    <td className="table-cell">
                      {l.tem_chave_pix ? (
                        <div>
                          <span className="text-xs text-gray-500">
                            {TIPO_CHAVE_LABEL[l.chave_pix_tipo!]}
                          </span>
                          <div className="text-xs font-mono text-gray-700 truncate max-w-[180px]">
                            {l.chave_pix_valor}
                          </div>
                        </div>
                      ) : (
                        <span className="text-xs text-red-500">Sem chave</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Totalizador */}
          {selecionados.size > 0 && (
            <div className="mt-6 pt-6 border-t border-gray-100 flex flex-wrap items-center justify-between gap-4">
              <div className="text-sm text-gray-700">
                <span className="font-semibold">{selecionados.size}</span>{' '}
                pagamento(s) selecionado(s) &bull; Total:{' '}
                <span className="font-bold text-blue-700">
                  {formatCurrency(valorTotal)}
                </span>
              </div>
              <button
                onClick={handleCriarESolicitar}
                disabled={saving}
                className="btn-primary"
              >
                {saving ? 'Enviando...' : 'Solicitar Aprovação'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
