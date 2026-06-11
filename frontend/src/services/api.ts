import axios from 'axios'
import { auth } from './firebase'

const DEV_MODE = import.meta.env.VITE_DEV_AUTH === 'true'
const DEV_SESSION_KEY = 'cnab_dev_session'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api',
})

api.interceptors.request.use(async (config) => {
  if (DEV_MODE) {
    const saved = sessionStorage.getItem(DEV_SESSION_KEY)
    if (saved) {
      const devUser = JSON.parse(saved) as { email: string }
      config.headers['X-Dev-Email'] = devUser.email
    }
    return config
  }

  const user = auth.currentUser
  if (user) {
    const token = await user.getIdToken()
    config.headers.Authorization = `Bearer ${token}`
    config.headers['X-Usuario'] = user.email ?? user.uid
  }
  return config
})

// ── LANCAMENTOS ───────────────────────────────────────────────────
export const getLancamentos = (dataInicio: string, dataFim: string) =>
  api.get('/lancamentos', { params: { data_inicio: dataInicio, data_fim: dataFim } })

export const sincronizarFornecedores = () =>
  api.post('/lancamentos/sincronizar-fornecedores')

// ── FORNECEDORES ──────────────────────────────────────────────────
export const getFornecedores = () => api.get('/fornecedores')

export const atualizarChavePix = (
  fornecedorId: string,
  tipo: string,
  valor: string,
  usuario: string,
  cnpj?: string,
) =>
  api.put(`/fornecedores/${fornecedorId}/chave-pix`, {
    chave_pix: { tipo, valor },
    atualizado_por: usuario,
    cnpj: cnpj || undefined,
  })

export const importarCSV = (file: File, usuario: string) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('usuario', usuario)
  return api.post('/fornecedores/importar', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// ── REMESSAS ──────────────────────────────────────────────────────
export const criarRemessa = (pagamentos: object[]) =>
  api.post('/remessas', { pagamentos })

export const getRemessas = (status?: string) =>
  api.get('/remessas', { params: status ? { status } : {} })

export const getRemessa = (id: string) => api.get(`/remessas/${id}`)

export const solicitarAprovacao = (id: string, usuario: string) =>
  api.post(`/remessas/${id}/solicitar-aprovacao`, { usuario })

export const aprovarRemessa = (id: string, usuario: string) =>
  api.post(`/remessas/${id}/aprovar`, { usuario })

export const devolverRemessa = (id: string, usuario: string, comentario: string) =>
  api.post(`/remessas/${id}/devolver`, { usuario, comentario })

export const downloadCnab = async (id: string) => {
  const response = await api.get(`/remessas/${id}/download`, { responseType: 'blob' })
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `remessa_${id}.rem`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

// ── USUÁRIOS ──────────────────────────────────────────────────────
export const getUsuarios = () => api.get('/usuarios/')

export const criarUsuario = (email: string, role: string) =>
  api.post('/usuarios/', { email, role })

export const atualizarUsuario = (email: string, role: string) =>
  api.put(`/usuarios/${encodeURIComponent(email)}`, { role })

export const removerUsuario = (email: string) =>
  api.delete(`/usuarios/${encodeURIComponent(email)}`)

export default api
