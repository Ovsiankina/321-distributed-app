import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, getToken, onUnauthorized, setToken } from '../lib/api'
import type { User } from '../lib/types'
import { AuthContext, type AuthState } from './AuthContext'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [ready, setReady] = useState(getToken() === null)

  useEffect(() => onUnauthorized(() => setUser(null)), [])

  useEffect(() => {
    if (getToken() === null) return
    // Only a 401 (handled in request) drops the token: a 404/502 at boot must not end a valid session.
    api
      .me()
      .then(setUser)
      .catch(() => {})
      .finally(() => setReady(true))
  }, [])

  const value = useMemo<AuthState>(
    () => ({
      user,
      ready,
      login: async (email, password) => {
        setToken((await api.login(email, password)).token)
        setUser(await api.me())
      },
      register: async (email, password) => {
        setToken((await api.register(email, password)).token)
        setUser(await api.me())
      },
      logout: () => {
        setToken(null)
        setUser(null)
      },
    }),
    [user, ready],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
