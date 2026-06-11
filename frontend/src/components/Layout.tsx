import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const navClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
      isActive
        ? 'bg-blue-900 text-white'
        : 'text-blue-100 hover:bg-blue-700'
    }`

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-blue-800 text-white shadow-lg">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-orange-500 text-white font-bold text-xs">
                Itaú
              </div>
              <span className="font-semibold text-lg tracking-tight">CNAB Pix</span>
            </div>

            <nav className="hidden md:flex items-center gap-1">
              {(user?.role === 'financeiro' || user?.role === 'gestor') && (
                <>
                  <NavLink to="/fornecedores" className={navClass}>
                    Fornecedores
                  </NavLink>
                  <NavLink to="/nova-remessa" className={navClass}>
                    Nova Remessa
                  </NavLink>
                  <NavLink to="/remessas" className={navClass}>
                    Minhas Remessas
                  </NavLink>
                </>
              )}
              {user?.role === 'gestor' && (
                <>
                  <NavLink to="/aprovacao" className={navClass}>
                    Aprovação
                  </NavLink>
                  <NavLink to="/usuarios" className={navClass}>
                    Usuários
                  </NavLink>
                </>
              )}
            </nav>

            <div className="flex items-center gap-3">
              <div className="text-right hidden sm:block">
                <p className="text-xs text-blue-200">{user?.email}</p>
                <p className="text-xs font-medium text-orange-300 capitalize">
                  {user?.role}
                </p>
              </div>
              <button
                onClick={handleLogout}
                className="rounded-md px-3 py-1.5 text-sm text-blue-100 hover:bg-blue-700 transition-colors"
              >
                Sair
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}
