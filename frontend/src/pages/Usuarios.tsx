import { useEffect, useState } from 'react'
import { getUsuarios, criarUsuario, atualizarUsuario, removerUsuario } from '../services/api'
import { useAuth } from '../contexts/AuthContext'

interface Usuario {
  email: string
  role: string
  atualizado_em?: string
  atualizado_por?: string
}

const ROLE_LABEL: Record<string, string> = {
  gestor: 'Gestor',
  financeiro: 'Financeiro',
}

const ROLE_BADGE: Record<string, string> = {
  gestor: 'bg-purple-100 text-purple-800',
  financeiro: 'bg-blue-100 text-blue-800',
}

export default function Usuarios() {
  const { user } = useAuth()
  const [usuarios, setUsuarios] = useState<Usuario[]>([])
  const [loading, setLoading] = useState(true)
  const [novoEmail, setNovoEmail] = useState('')
  const [novoRole, setNovoRole] = useState('financeiro')
  const [adicionando, setAdicionando] = useState(false)
  const [erro, setErro] = useState('')
  const [editando, setEditando] = useState<string | null>(null)
  const [editRole, setEditRole] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const res = await getUsuarios()
      setUsuarios(res.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const handleAdicionar = async () => {
    setErro('')
    if (!novoEmail || !novoEmail.includes('@')) {
      setErro('Informe um email válido')
      return
    }
    setAdicionando(true)
    try {
      await criarUsuario(novoEmail.trim().toLowerCase(), novoRole)
      setNovoEmail('')
      setNovoRole('financeiro')
      await load()
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      setErro(err?.response?.data?.detail ?? 'Erro ao adicionar usuário')
    } finally {
      setAdicionando(false)
    }
  }

  const handleEditar = async (email: string) => {
    try {
      await atualizarUsuario(email, editRole)
      setEditando(null)
      await load()
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      setErro(err?.response?.data?.detail ?? 'Erro ao atualizar')
    }
  }

  const handleRemover = async (email: string) => {
    if (!confirm(`Remover ${email}?`)) return
    try {
      await removerUsuario(email)
      await load()
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      setErro(err?.response?.data?.detail ?? 'Erro ao remover')
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Usuários</h1>
        <p className="text-sm text-gray-500 mt-1">Gerencie quem pode acessar o sistema e com qual perfil</p>
      </div>

      {/* Formulário de adição */}
      <div className="card">
        <h2 className="text-base font-semibold text-gray-800 mb-4">Adicionar usuário</h2>
        <div className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-48">
            <label className="label">Email</label>
            <input
              type="email"
              className={`input ${erro ? 'border-red-400' : ''}`}
              placeholder="usuario@empresa.com"
              value={novoEmail}
              onChange={(e) => { setNovoEmail(e.target.value); setErro('') }}
              onKeyDown={(e) => e.key === 'Enter' && handleAdicionar()}
            />
          </div>
          <div>
            <label className="label">Perfil</label>
            <select
              className="input"
              value={novoRole}
              onChange={(e) => setNovoRole(e.target.value)}
            >
              <option value="financeiro">Financeiro</option>
              <option value="gestor">Gestor</option>
            </select>
          </div>
          <button
            onClick={handleAdicionar}
            disabled={adicionando}
            className="btn-primary"
          >
            {adicionando ? 'Adicionando...' : 'Adicionar'}
          </button>
        </div>
        {erro && <p className="mt-2 text-sm text-red-600">{erro}</p>}
      </div>

      {/* Lista */}
      <div className="card">
        {loading ? (
          <div className="py-16 text-center text-gray-400">Carregando...</div>
        ) : usuarios.length === 0 ? (
          <div className="py-16 text-center text-gray-400">Nenhum usuário cadastrado.</div>
        ) : (
          <div className="overflow-x-auto -mx-6">
            <table className="min-w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="table-header">Email</th>
                  <th className="table-header">Perfil</th>
                  <th className="table-header">Atualizado por</th>
                  <th className="table-header">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {usuarios.map((u) => (
                  <tr key={u.email} className="hover:bg-gray-50">
                    <td className="table-cell font-medium">
                      {u.email}
                      {u.email === user?.email && (
                        <span className="ml-2 text-xs text-gray-400">(você)</span>
                      )}
                    </td>
                    <td className="table-cell">
                      {editando === u.email ? (
                        <select
                          className="input py-1 text-sm"
                          value={editRole}
                          onChange={(e) => setEditRole(e.target.value)}
                        >
                          <option value="financeiro">Financeiro</option>
                          <option value="gestor">Gestor</option>
                        </select>
                      ) : (
                        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${ROLE_BADGE[u.role] ?? 'bg-gray-100 text-gray-800'}`}>
                          {ROLE_LABEL[u.role] ?? u.role}
                        </span>
                      )}
                    </td>
                    <td className="table-cell text-xs text-gray-500">{u.atualizado_por ?? '—'}</td>
                    <td className="table-cell">
                      <div className="flex gap-3">
                        {editando === u.email ? (
                          <>
                            <button
                              onClick={() => handleEditar(u.email)}
                              className="text-green-700 hover:text-green-900 text-sm font-medium"
                            >
                              Salvar
                            </button>
                            <button
                              onClick={() => setEditando(null)}
                              className="text-gray-500 hover:text-gray-700 text-sm"
                            >
                              Cancelar
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              onClick={() => { setEditando(u.email); setEditRole(u.role) }}
                              className="text-blue-700 hover:text-blue-900 text-sm font-medium"
                            >
                              Editar
                            </button>
                            {u.email !== user?.email && (
                              <button
                                onClick={() => handleRemover(u.email)}
                                className="text-red-600 hover:text-red-800 text-sm font-medium"
                              >
                                Remover
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
