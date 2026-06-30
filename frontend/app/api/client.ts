import { ApplyFlowApiError, normalizeApiError } from './errors'
import { assertCsrfResponse, assertRelativeApiPath } from './runtime-guards'

type HttpMethod = 'DELETE' | 'GET' | 'PATCH' | 'POST' | 'PUT'

interface ApiRequestOptions<T> {
  method?: HttpMethod
  body?: BodyInit | object
  headers?: Record<string, string>
  etag?: string
  guard?: (value: unknown) => T
  retryCsrf?: boolean
}

export interface ApiResponse<T> {
  data: T
  etag: string | null
  status: number
  headers: Headers
}

let csrfToken: string | null = null
let csrfInFlight: Promise<string> | null = null

const unsafeMethods = new Set<HttpMethod>(['DELETE', 'PATCH', 'POST', 'PUT'])

const parseJsonSafely = async (response: Response): Promise<unknown> => {
  if (response.status === 204) return null
  const text = await response.text()
  if (!text) return null
  try {
    return JSON.parse(text) as unknown
  } catch {
    throw new ApplyFlowApiError({
      code: 'malformed_response',
      message: 'The service returned an unreadable response. Try again later.',
      status: response.status,
      fields: {},
      requestId: response.headers.get('X-Request-ID'),
    })
  }
}

export const clearCsrfTokenForTests = () => {
  csrfToken = null
  csrfInFlight = null
}

export const getCsrfToken = async (): Promise<string> => {
  if (csrfToken) return csrfToken
  if (csrfInFlight) return csrfInFlight

  csrfInFlight = apiRequest('/api/v1/csrf/', {
    method: 'GET',
    guard: assertCsrfResponse,
  })
    .then((response) => {
      csrfToken = response.data.csrf_token
      return csrfToken
    })
    .finally(() => {
      csrfInFlight = null
    })
  return csrfInFlight
}

const requestHeaders = async (
  method: HttpMethod,
  options: ApiRequestOptions<unknown>,
): Promise<Record<string, string>> => {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...options.headers,
  }
  if (options.etag) headers['If-Match'] = options.etag
  if (unsafeMethods.has(method)) headers['X-CSRFToken'] = await getCsrfToken()
  if (options.body && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }
  return headers
}

const requestBody = (body: BodyInit | object | undefined): BodyInit | undefined => {
  if (!body) return undefined
  if (
    body instanceof FormData ||
    body instanceof Blob ||
    body instanceof ArrayBuffer ||
    typeof body === 'string' ||
    body instanceof URLSearchParams
  ) {
    return body
  }
  return JSON.stringify(body)
}

export const apiRequest = async <T = unknown>(
  path: string,
  options: ApiRequestOptions<T> = {},
): Promise<ApiResponse<T>> => {
  assertRelativeApiPath(path)
  const method = options.method ?? 'GET'
  const headers = await requestHeaders(method, options)
  let response: Response
  try {
    response = await fetch(path, {
      method,
      headers,
      body: requestBody(options.body),
      credentials: 'include',
    })
  } catch (error) {
    throw new ApplyFlowApiError({
      code: 'network_failure',
      message: error instanceof Error ? 'The network request did not finish.' : 'Network failure.',
      status: 0,
      fields: {},
      requestId: null,
    })
  }

  const payload = await parseJsonSafely(response)
  if (!response.ok) {
    const normalized = normalizeApiError(payload, response.status)
    if (normalized.code === 'csrf_failed' && options.retryCsrf !== false && method !== 'PUT') {
      csrfToken = null
      const refreshed = await getCsrfToken()
      return apiRequest(path, {
        ...options,
        headers: { ...options.headers, 'X-CSRFToken': refreshed },
        retryCsrf: false,
      })
    }
    throw new ApplyFlowApiError(normalized)
  }

  return {
    data: options.guard ? options.guard(payload) : (payload as T),
    etag: response.headers.get('ETag'),
    status: response.status,
    headers: response.headers,
  }
}
