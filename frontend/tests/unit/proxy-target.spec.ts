import { describe, expect, it } from 'vitest'
import { nuxtDevProxyTarget, validateApiProxyTarget } from '../../proxy-target'

describe('NUXT_API_PROXY_TARGET validation', () => {
  it('defaults to a loopback Django origin', () => {
    expect(validateApiProxyTarget(undefined)).toBe('http://127.0.0.1:8000')
  })

  it('accepts only clean loopback HTTP origins', () => {
    expect(validateApiProxyTarget('http://localhost:8000')).toBe('http://localhost:8000')
    expect(validateApiProxyTarget('http://[::1]:8000')).toBe('http://[::1]:8000')
  })

  it.each([
    ' http://127.0.0.1:8000',
    'https://127.0.0.1:8000',
    'http://user@127.0.0.1:8000',
    'http://example.com:8000',
    'http://127.0.0.1:8000/api',
    'http://127.0.0.1:8000?target=/api',
    'http://127.0.0.1:8000#fragment',
  ])('rejects unsafe target %s', (target) => {
    expect(() => validateApiProxyTarget(target)).toThrow()
  })

  it('preserves the browser /api prefix through the Nuxt dev proxy target', () => {
    expect(nuxtDevProxyTarget(validateApiProxyTarget('http://127.0.0.1:8001'))).toBe(
      'http://127.0.0.1:8001/api/',
    )
  })
})
