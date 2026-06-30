const LOOPBACK_HOSTS = new Set(['localhost', '127.0.0.1', '[::1]'])
const DEFAULT_PROXY_TARGET = 'http://127.0.0.1:8000'

export const validateApiProxyTarget = (rawValue: string | undefined): string => {
  const value = rawValue ?? DEFAULT_PROXY_TARGET
  if (value !== value.trim()) {
    throw new Error('NUXT_API_PROXY_TARGET must not contain leading or trailing whitespace.')
  }

  let url: URL
  try {
    url = new URL(value)
  } catch (error) {
    throw new Error('NUXT_API_PROXY_TARGET must be a valid loopback HTTP URL.', {
      cause: error,
    })
  }

  if (url.protocol !== 'http:') {
    throw new Error('NUXT_API_PROXY_TARGET must use the http scheme for local development.')
  }
  if (url.username || url.password) {
    throw new Error('NUXT_API_PROXY_TARGET must not include credentials.')
  }
  if (url.search || url.hash) {
    throw new Error('NUXT_API_PROXY_TARGET must not include query strings or fragments.')
  }
  if (!LOOPBACK_HOSTS.has(url.host.startsWith('[') ? url.hostname : url.hostname)) {
    throw new Error('NUXT_API_PROXY_TARGET must use a loopback host.')
  }
  if (url.port) {
    const port = Number(url.port)
    if (!Number.isInteger(port) || port < 1 || port > 65535) {
      throw new Error('NUXT_API_PROXY_TARGET must use a valid TCP port.')
    }
  }
  if (url.pathname !== '/') {
    throw new Error('NUXT_API_PROXY_TARGET must be an origin without a path.')
  }

  return url.origin
}

export const nuxtDevProxyTarget = (origin: string): string => `${origin}/api/`
