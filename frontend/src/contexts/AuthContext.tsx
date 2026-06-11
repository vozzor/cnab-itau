import React, { createContext, useContext, useEffect, useState } from 'react'
import {
  signInWithPopup,
  signOut,
  onAuthStateChanged,
} from 'firebase/auth'
import { auth, googleProvider } from '../services/firebase'
import type { AuthUser, UserRole } from '../types'
import api from '../services/api'

const DEV_MODE = import.meta.env.VITE_DEV_AUTH === 'true'
const DEV_SESSION_KEY = 'cnab_dev_session'

interface AuthContextValue {
  user: AuthUser | null
  loading: boolean
  loginWithGoogle: (devEmail?: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

async function fetchRole(token: string): Promise<{ email: string; role: UserRole }> {
  const res = await api.get('/auth/me', {
    headers: { Authorization: `Bearer ${token}` },
  })
  return res.data
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (DEV_MODE) {
      const saved = sessionStorage.getItem(DEV_SESSION_KEY)
      if (saved) setUser(JSON.parse(saved))
      setLoading(false)
      return
    }

    const unsub = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        try {
          const token = await firebaseUser.getIdToken()
          const { email, role } = await fetchRole(token)
          setUser({ uid: firebaseUser.uid, email, role })
        } catch {
          // Email não autorizado ou token inválido — desloga silenciosamente
          await signOut(auth)
          setUser(null)
        }
      } else {
        setUser(null)
      }
      setLoading(false)
    })
    return unsub
  }, [])

  const loginWithGoogle = async (devEmail?: string) => {
    if (DEV_MODE) {
      if (!devEmail) throw new Error('Informe o email')
      const res = await api.post('/auth/dev-login', { email: devEmail })
      const { email, role } = res.data
      const devUser: AuthUser = { uid: email, email, role }
      sessionStorage.setItem(DEV_SESSION_KEY, JSON.stringify(devUser))
      setUser(devUser)
      return
    }

    const result = await signInWithPopup(auth, googleProvider)
    const token = await result.user.getIdToken()
    const { email, role } = await fetchRole(token)
    setUser({ uid: result.user.uid, email, role })
  }

  const logout = async () => {
    if (DEV_MODE) {
      sessionStorage.removeItem(DEV_SESSION_KEY)
      setUser(null)
      return
    }
    await signOut(auth)
  }

  return (
    <AuthContext.Provider value={{ user, loading, loginWithGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
