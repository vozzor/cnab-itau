import { useEffect, useState, useRef } from 'react'
import {
  getFornecedores,
  atualizarChavePix,
  importarCSV,
  sincronizarFornecedores,
} from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import type { Fornecedor, ChavePix } from '../types'
import { TIPO_CHAVE_LABEL } from '../types'

const TIPO_CHAVE_OPTIONS = [
  { value: '01', label: 'Telefone (+55XXXXXXXXXXX)' },
  { value: '02', label: 'E-mail' },
  { value: '03', label: 'CPF/CNPJ (somente numeros)' },
  { value: '04', label: 'Chave aleatoria (UUID)' },
]

function validateChavePix(tipo: string, valor: string): string {
  if (!valor) return 'Informe a chave Pix'
  if (tipo === '01' && !/^\+55\d{10,11}$/.test(valor))
    return 'Formato: +55XXXXXXXXXXX'
  if (tipo === '02' && (!valor.includes('@') || valor.length > 77))
    return 'E-mail invalido ou maior que 77 caracteres'
  if (tipo === '03' && !/^\d{11}$|^\d{14}$/.test(valor.replace(/\D/g, '')))
    return 'CPF (11 digitos) ou CNPJ (14 digitos), somente numeros'
  if (
    tipo === '04' &&
    !/^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(
      valor,
    )
  )
    return 'UUID no formato XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX'
  return ''
}

function BadgeChave({ chave }: { chave?: ChavePix | null }) {
  if (chave) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
        <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
        Cadastrada
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-orange-100 px-2.5 py-0.5 text-xs font-medium text-orange-800">
      <span className="h-1.5 w-1.5 rounded-full bg-orange-500" />
      Pendente
    </span>
  )
}

interface ModalProps {
  fornecedor: Fornecedor
  onClose: () => void
  onSave: (tipo: string, valor: string, cnpj: string) => Promise<void>
}

function ModalChavePix({ fornecedor, onClose, onSave }: ModalProps) {
  const [tipo, setTipo] = useState<string>(fornecedor.chave_pix?.tipo ?? '03')
  const [valor, setValor] = useState(fornecedor.chave_pix?.valor ?? fornecedor.cnpj ?? '')
  const [cnpj, setCnpj] = useState(fornecedor.cnpj ?? '')
  const [erro, setErro] = useState('')
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    const validationError = validateChavePix(tipo, valor)
    if (validationError) {
      setErro(validationError)
      return
    }
    setSaving(true)
    try {
      await onSave(tipo, valor, cnpj.trim())
      onClose()
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      setErro(err?.response?.data?.detail ?? 'Erro ao salvar')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white shadow-2xl">
        <div className="p-6 border-b border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900">Chave Pix</h3>
          <p className="text-sm text-gray-500 mt-1">{fornecedor.nome}</p>
        </div>

        <div className="p-6 space-y-4">
          <div>
            <label className="label">CNPJ do fornecedor</label>
            <input
              type="text"
              className="input font-mono"
              value={cnpj}
              onChange={(e) => {
                const novo = e.target.value.replace(/\D/g, '').slice(0, 14)
                setCnpj(novo)
                // Auto-preenche chave Pix se ainda está no padrão CNPJ
                if (tipo === '03' && (valor === cnpj || valor === '')) {
                  setValor(novo)
                  setErro('')
                }
              }}
              placeholder="00000000000000 (somente numeros)"
            />
            {!fornecedor.cnpj && (
              <p className="mt-1 text-xs text-amber-600">Preencha o CNPJ para uso no arquivo CNAB</p>
            )}
          </div>

          <div>
            <label className="label">Tipo de chave</label>
            <select
              className="input"
              value={tipo}
              onChange={(e) => {
                setTipo(e.target.value)
                setErro('')
              }}
            >
              {TIPO_CHAVE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">Valor da chave</label>
            <input
              type="text"
              className={`input ${erro ? 'border-red-400 focus:ring-red-400' : ''}`}
              value={valor}
              onChange={(e) => {
                setValor(e.target.value)
                setErro('')
              }}
              placeholder={
                tipo === '01'
                  ? '+5511999999999'
                  : tipo === '02'
                    ? 'email@exemplo.com'
                    : tipo === '03'
                      ? '12345678000190'
                      : 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
              }
            />
            {erro && <p className="mt-1 text-xs text-red-600">{erro}</p>}
          </div>
        </div>

        <div className="flex justify-end gap-3 p-6 border-t border-gray-100">
          <button onClick={onClose} className="btn-secondary">
            Cancelar
          </button>
          <button onClick={handleSave} disabled={saving} className="btn-primary">
            {saving ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Fornecedores() {
  const { user } = useAuth()
  const [fornecedores, setFornecedores] = useState<Fornecedor[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [modalFornecedor, setModalFornecedor] = useState<Fornecedor | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [syncResult, setSyncResult] = useState<{ criados: number; atualizados: number } | null>(null)
  const [importResult, setImportResult] = useState<{
    atualizados?: number
    total_erros?: number
    erros?: { linha: number; nome?: string; erro: string }[]
    error?: string
  } | null>(null)
  const [importing, setImporting] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  type SortKey = 'nome' | 'cnpj' | 'tipo' | 'chave' | 'status'
  const [sortKey, setSortKey] = useState<SortKey | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      if (sortDir === 'asc') setSortDir('desc')
      else {
        setSortKey(null)
        setSortDir('asc')
      }
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  const load = async () => {
    setLoading(true)
    try {
      const res = await getFornecedores()
      setFornecedores(res.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const handleSync = async () => {
    setSyncing(true)
    setSyncResult(null)
    try {
      const res = await sincronizarFornecedores()
      setSyncResult(res.data)
      await load()
    } finally {
      setSyncing(false)
    }
  }

  const handleSaveChave = async (fornecedorId: string, tipo: string, valor: string, cnpj: string) => {
    await atualizarChavePix(fornecedorId, tipo, valor, user?.email ?? 'sistema', cnpj || undefined)
    await load()
  }

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setImporting(true)
    setImportResult(null)
    try {
      const res = await importarCSV(file, user?.email ?? 'sistema')
      setImportResult(res.data)
      await load()
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      setImportResult({ error: e?.response?.data?.detail ?? 'Erro na importacao' })
    } finally {
      setImporting(false)
    }
    e.target.value = ''
  }

  const filtered = fornecedores.filter(
    (f) =>
      f.nome.toLowerCase().includes(search.toLowerCase()) ||
      (f.cnpj ?? '').includes(search),
  )

  const sorted = (() => {
    if (!sortKey) return filtered
    const dir = sortDir === 'asc' ? 1 : -1
    const cmpStr = (a: string, b: string) =>
      a.localeCompare(b, 'pt-BR', { sensitivity: 'base' }) * dir
    const hasFirst = (hasA: boolean, hasB: boolean, fallback: () => number) => {
      if (hasA === hasB) return fallback()
      return (hasA ? -1 : 1) * dir
    }
    const arr = [...filtered]
    arr.sort((a, b) => {
      switch (sortKey) {
        case 'nome':
          return cmpStr(a.nome ?? '', b.nome ?? '')
        case 'cnpj':
          return hasFirst(!!a.cnpj, !!b.cnpj, () => cmpStr(a.cnpj ?? '', b.cnpj ?? ''))
        case 'tipo':
          return hasFirst(!!a.chave_pix, !!b.chave_pix, () =>
            cmpStr(a.chave_pix?.tipo ?? '', b.chave_pix?.tipo ?? ''),
          )
        case 'chave':
          return hasFirst(!!a.chave_pix, !!b.chave_pix, () =>
            cmpStr(a.chave_pix?.valor ?? '', b.chave_pix?.valor ?? ''),
          )
        case 'status':
          return hasFirst(!!a.chave_pix, !!b.chave_pix, () => 0)
        default:
          return 0
      }
    })
    return arr
  })()

  const sortIndicator = (key: SortKey) =>
    sortKey !== key ? '' : sortDir === 'asc' ? ' ↑' : ' ↓'

  const comChave = fornecedores.filter((f) => f.chave_pix).length
  const semChave = fornecedores.length - comChave
  const cobertura = fornecedores.length
    ? Math.round((comChave / fornecedores.length) * 100)
    : 0

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Fornecedores</h1>
          <p className="text-sm text-gray-500 mt-1">
            {comChave} de {fornecedores.length} fornecedores com chave Pix
            cadastrada
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={handleSync}
            disabled={syncing}
            className="btn-secondary"
          >
            {syncing ? 'Sincronizando...' : 'Sincronizar BigQuery'}
          </button>
          <button
            onClick={() => fileRef.current?.click()}
            disabled={importing}
            className="btn-secondary inline-flex items-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
            title="CSV com colunas: nome, razao_social (opcional), cnpj, cpf. O CNPJ ou CPF vira a chave Pix automaticamente."
          >
            {importing && (
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-25" />
                <path d="M4 12a8 8 0 018-8" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
              </svg>
            )}
            {importing ? 'Importando...' : 'Importar CSV'}
          </button>
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleImport}
            disabled={importing}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="rounded-lg border border-gray-200 bg-white px-4 py-3">
          <p className="text-xs uppercase tracking-wide text-gray-500">Total</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{fornecedores.length}</p>
        </div>
        <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3">
          <p className="text-xs uppercase tracking-wide text-green-700">Com chave Pix</p>
          <p className="text-2xl font-bold text-green-800 mt-1">
            {comChave}
            <span className="text-sm font-medium text-green-700 ml-2">({cobertura}%)</span>
          </p>
          <div className="h-1.5 bg-green-200 rounded-full mt-2 overflow-hidden">
            <div
              className="h-full bg-green-600 transition-all"
              style={{ width: `${cobertura}%` }}
            />
          </div>
        </div>
        <div className="rounded-lg border border-orange-200 bg-orange-50 px-4 py-3">
          <p className="text-xs uppercase tracking-wide text-orange-700">Pendentes</p>
          <p className="text-2xl font-bold text-orange-800 mt-1">{semChave}</p>
        </div>
      </div>

      {syncResult && (
        <div className="rounded-lg bg-green-50 border border-green-200 p-3 text-sm text-green-800 flex items-center justify-between">
          <span>
            Sincronização concluída —{' '}
            <strong>{syncResult.criados}</strong> novo(s),{' '}
            <strong>{syncResult.atualizados}</strong> atualizado(s).
          </span>
          <button onClick={() => setSyncResult(null)} className="text-xs underline ml-4">Fechar</button>
        </div>
      )}

      {importResult && (
        <div
          className={`rounded-lg p-4 text-sm ${
            importResult.error
              ? 'bg-red-50 text-red-700 border border-red-200'
              : 'bg-green-50 text-green-800 border border-green-200'
          }`}
        >
          {importResult.error ? (
            <p>{importResult.error}</p>
          ) : (
            <div>
              <p className="font-medium">
                {importResult.atualizados} chave(s) importada(s) com sucesso.
              </p>
              {(importResult.total_erros ?? 0) > 0 && (
                <details className="mt-2">
                  <summary className="cursor-pointer text-red-700">
                    {importResult.total_erros} erro(s)
                  </summary>
                  <ul className="mt-1 list-disc list-inside space-y-0.5">
                    {importResult.erros?.map((e, i) => (
                      <li key={i}>
                        Linha {e.linha} {e.nome ? `(${e.nome})` : ''}: {e.erro}
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          )}
          <button
            onClick={() => setImportResult(null)}
            className="mt-2 text-xs underline"
          >
            Fechar
          </button>
        </div>
      )}

      <div className="card">
        <div className="mb-4">
          <input
            type="text"
            className="input max-w-sm"
            placeholder="Buscar por nome ou CNPJ..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {loading ? (
          <div className="py-16 text-center text-gray-400">Carregando...</div>
        ) : filtered.length === 0 ? (
          <div className="py-16 text-center text-gray-400">
            {fornecedores.length === 0
              ? 'Nenhum fornecedor. Clique em "Sincronizar BigQuery" para importar.'
              : 'Nenhum fornecedor encontrado.'}
          </div>
        ) : (
          <div className="overflow-x-auto -mx-6">
            <table className="min-w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="table-header">
                    <button onClick={() => toggleSort('nome')} className="hover:text-gray-900">
                      Nome{sortIndicator('nome')}
                    </button>
                  </th>
                  <th className="table-header">
                    <button onClick={() => toggleSort('cnpj')} className="hover:text-gray-900">
                      CNPJ{sortIndicator('cnpj')}
                    </button>
                  </th>
                  <th className="table-header">
                    <button onClick={() => toggleSort('tipo')} className="hover:text-gray-900">
                      Tipo chave{sortIndicator('tipo')}
                    </button>
                  </th>
                  <th className="table-header">
                    <button onClick={() => toggleSort('chave')} className="hover:text-gray-900">
                      Chave Pix{sortIndicator('chave')}
                    </button>
                  </th>
                  <th className="table-header">
                    <button onClick={() => toggleSort('status')} className="hover:text-gray-900">
                      Status{sortIndicator('status')}
                    </button>
                  </th>
                  <th className="table-header">Acoes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {sorted.map((f) => (
                  <tr key={f.id} className="hover:bg-gray-50">
                    <td className="table-cell font-medium">{f.nome}</td>
                    <td className="table-cell font-mono text-xs">{f.cnpj}</td>
                    <td className="table-cell text-gray-500">
                      {f.chave_pix ? TIPO_CHAVE_LABEL[f.chave_pix.tipo] : '—'}
                    </td>
                    <td className="table-cell font-mono text-xs max-w-xs truncate">
                      {f.chave_pix?.valor ?? '—'}
                    </td>
                    <td className="table-cell">
                      <BadgeChave chave={f.chave_pix} />
                    </td>
                    <td className="table-cell">
                      <button
                        onClick={() => setModalFornecedor(f)}
                        className="text-blue-700 hover:text-blue-900 text-sm font-medium"
                      >
                        Editar chave
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {modalFornecedor && (
        <ModalChavePix
          fornecedor={modalFornecedor}
          onClose={() => setModalFornecedor(null)}
          onSave={(tipo, valor, cnpj) =>
            handleSaveChave(modalFornecedor.id, tipo, valor, cnpj)
          }
        />
      )}
    </div>
  )
}
