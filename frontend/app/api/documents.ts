import type { ApiDraftAggregate, DraftEtag, ServerDraftState } from '~/types/domain'
import { apiRequest, getCsrfToken } from './client'
import { applicationDraftFromApi } from './drafts'
import { ApplyFlowApiError, normalizeApiError } from './errors'
import { assertApiDraftAggregate, assertRelativeApiPath, parseDraftEtag } from './runtime-guards'

interface UploadOptions {
  draftId: string
  etag: DraftEtag
  file: File
  onProgress?: (loaded: number, total: number | null) => void
  signal?: AbortSignal
}

const stateFromUpload = (aggregate: ApiDraftAggregate, etag: string | null): ServerDraftState => ({
  id: aggregate.draft.id,
  version: aggregate.draft.version,
  etag: parseDraftEtag(etag),
  draft: applicationDraftFromApi(aggregate),
  expiresAt: aggregate.draft.expires_at,
})

const parseUploadResponse = (text: string, status: number): unknown => {
  if (!text) return null
  try {
    return JSON.parse(text) as unknown
  } catch {
    throw new ApplyFlowApiError({
      code: 'malformed_response',
      message: 'The service returned an unreadable upload response.',
      status,
      fields: {},
      requestId: null,
    })
  }
}

export const uploadCvDocument = async (options: UploadOptions): Promise<ServerDraftState> => {
  const path = `/api/v1/application-drafts/${options.draftId}/documents/cv/`
  assertRelativeApiPath(path)
  const csrfToken = await getCsrfToken()
  const form = new FormData()
  form.append('file', options.file)

  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest()
    const abort = () => request.abort()
    options.signal?.addEventListener('abort', abort, { once: true })

    request.open('PUT', path)
    request.withCredentials = true
    request.setRequestHeader('Accept', 'application/json')
    request.setRequestHeader('X-CSRFToken', csrfToken)
    request.setRequestHeader('If-Match', options.etag)

    request.upload.addEventListener('progress', (event) => {
      options.onProgress?.(event.loaded, event.lengthComputable ? event.total : null)
    })
    request.addEventListener('abort', () => {
      reject(
        new ApplyFlowApiError({
          code: 'network_failure',
          message: 'The upload was cancelled. The previous CV, if any, is still shown.',
          status: 0,
          fields: {},
          requestId: null,
        }),
      )
    })
    request.addEventListener('error', () => {
      reject(
        new ApplyFlowApiError({
          code: 'network_failure',
          message: 'The upload did not finish. Check your connection and review the draft.',
          status: 0,
          fields: {},
          requestId: null,
        }),
      )
    })
    request.addEventListener('load', () => {
      try {
        const payload = parseUploadResponse(request.responseText, request.status)
        if (request.status < 200 || request.status >= 300) {
          reject(new ApplyFlowApiError(normalizeApiError(payload, request.status)))
          return
        }
        resolve(
          stateFromUpload(assertApiDraftAggregate(payload), request.getResponseHeader('ETag')),
        )
      } catch (error) {
        reject(error)
      }
    })
    request.addEventListener('loadend', () => {
      options.signal?.removeEventListener('abort', abort)
    })
    request.send(form)
  })
}

export const deleteCvDocument = async (draftId: string, etag: DraftEtag): Promise<DraftEtag> => {
  const response = await apiRequest(`/api/v1/application-drafts/${draftId}/documents/cv/`, {
    method: 'DELETE',
    etag,
    guard: (value) => value,
  })
  return parseDraftEtag(response.etag)
}
