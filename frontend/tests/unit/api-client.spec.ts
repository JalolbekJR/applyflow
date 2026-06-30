import { afterEach, describe, expect, it, vi } from 'vitest'
import { apiRequest, clearCsrfTokenForTests, getCsrfToken } from '~/api/client'
import type { ApplyFlowApiError } from '~/api/errors'

const jsonResponse = (payload: unknown, init: ResponseInit = {}) =>
  new Response(payload === null ? null : JSON.stringify(payload), {
    headers: { 'Content-Type': 'application/json', ...(init.headers ?? {}) },
    status: init.status ?? 200,
  })

describe('API client', () => {
  afterEach(() => {
    clearCsrfTokenForTests()
    vi.restoreAllMocks()
  })

  it('uses relative API URLs and same-origin credentials', async () => {
    const fetch = vi.fn().mockResolvedValue(jsonResponse({ ok: true }))
    vi.stubGlobal('fetch', fetch)

    await apiRequest('/api/v1/health/')

    expect(fetch).toHaveBeenCalledWith(
      '/api/v1/health/',
      expect.objectContaining({ credentials: 'include', method: 'GET' }),
    )
    await expect(apiRequest('https://api.example.test/api/v1/health/')).rejects.toThrow(/relative/)
  })

  it('deduplicates CSRF bootstrap and keeps the token in module memory', async () => {
    const fetch = vi.fn().mockResolvedValue(jsonResponse({ csrf_token: 'masked-token-value' }))
    vi.stubGlobal('fetch', fetch)

    await Promise.all([getCsrfToken(), getCsrfToken()])

    expect(fetch).toHaveBeenCalledTimes(1)
    expect(localStorage.getItem('csrf_token')).toBeNull()
    expect(sessionStorage.getItem('csrf_token')).toBeNull()
  })

  it('handles 204 responses without parsing JSON', async () => {
    const fetch = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetch)

    const response = await apiRequest('/api/v1/application-drafts/active/')

    expect(response.status).toBe(204)
    expect(response.data).toBeNull()
  })

  it('normalizes API errors without leaking server details', async () => {
    const fetch = vi.fn().mockResolvedValue(
      jsonResponse(
        {
          error: {
            code: 'draft_conflict',
            message: 'The application draft changed. Refresh and try again.',
            fields: {},
            request_id: 'req_example',
          },
        },
        { status: 409 },
      ),
    )
    vi.stubGlobal('fetch', fetch)

    await expect(apiRequest('/api/v1/application-drafts/example/')).rejects.toMatchObject({
      code: 'draft_conflict',
      requestId: 'req_example',
    } satisfies Partial<ApplyFlowApiError>)
  })
})
