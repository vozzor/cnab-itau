import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Login from './pages/Login'
import Fornecedores from './pages/Fornecedores'
import NovaRemessa from './pages/NovaRemessa'
import Remessas from './pages/Remessas'
import Aprovacao from './pages/Aprovacao'
import Usuarios from './pages/Usuarios'
import Layout from './components/Layout'

function PrivateRoute({
  children,
  role,
}: {
  children: React.ReactNode
  role?: string
}) {
  const { user, loading } = useAuth()
  if (loading)
    return (
      <div className="flex h-screen items-center justify-center text-gray-500">
        Carregando...
      </div>
    )
  if (!user) return <Navigate to="/login" replace />
  if (role && user.role !== role && user.role !== 'gestor') return <Navigate to="/" replace />
  return <>{children}</>
}

function AppRoutes() {
  const { user, loading } = useAuth()
  if (loading)
    return (
      <div className="flex h-screen items-center justify-center text-gray-500">
        Carregando...
      </div>
    )

  return (
    <Routes>
      <Route
        path="/login"
        element={user ? <Navigate to="/" replace /> : <Login />}
      />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route
          index
          element={
            user?.role === 'gestor' ? (
              <Navigate to="/aprovacao" replace />
            ) : (
              <Navigate to="/fornecedores" replace />
            )
          }
        />
        <Route
          path="fornecedores"
          element={
            <PrivateRoute role="financeiro">
              <Fornecedores />
            </PrivateRoute>
          }
        />
        <Route
          path="nova-remessa"
          element={
            <PrivateRoute role="financeiro">
              <NovaRemessa />
            </PrivateRoute>
          }
        />
        <Route
          path="remessas"
          element={
            <PrivateRoute role="financeiro">
              <Remessas />
            </PrivateRoute>
          }
        />
        <Route
          path="aprovacao"
          element={
            <PrivateRoute role="gestor">
              <Aprovacao />
            </PrivateRoute>
          }
        />
        <Route
          path="usuarios"
          element={
            <PrivateRoute role="gestor">
              <Usuarios />
            </PrivateRoute>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  )
}
