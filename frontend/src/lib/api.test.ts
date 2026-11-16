import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { api, getToken, onUnauthorized, setToken } from './api'

function respond(status: number, body: unknown) {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(body), { status })))
}

describe('request on 401', () => {
  const loggedOut = vi.fn()

  beforeEach(() => {
    const store = new Map<string, string>()
    vi.stubGlobal('localStorage', {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => store.set(key, value),
      removeItem: (key: string) => store.delete(key),
    })
    loggedOut.mockReset()
    onUnauthorized(loggedOut)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('drops a rejected token and reports the logout', async () => {
    setToken('expired')
    respond(401, { detail: 'Authentification requise' })
    await expect(api.favorites()).rejects.toThrow('Authentification requise')
    expect(getToken()).toBeNull()
    expect(loggedOut).toHaveBeenCalledOnce()
  })

  it('keeps the session when a login fails with a token stored', async () => {
    setToken('valid')
    respond(401, { detail: 'Identifiants incorrects' })
    await expect(api.login('a@b.ch', 'wrong')).rejects.toThrow('Identifiants incorrects')
    expect(getToken()).toBe('valid')
    expect(loggedOut).not.toHaveBeenCalled()
  })

  it('does not send the token to login', async () => {
    setToken('valid')
    respond(200, { token: 'new', email: 'a@b.ch', expires_in_hours: 24 })
    await api.login('a@b.ch', 'right')
    const init = vi.mocked(fetch).mock.calls[0][1]
    expect(new Headers(init?.headers).has('Authorization')).toBe(false)
  })
})
