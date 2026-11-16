import { createContext, useContext } from 'react'
import type { User } from '../lib/types'

export interface AuthState {
  user: User | null
  ready: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthState | null>(null)

export function useAuth(): AuthState {
  const auth = useContext(AuthContext)
  if (auth === null) throw new Error('useAuth must be used inside AuthProvider')
  return auth
}
