export type ApiErrorCode =
  | 'active_draft_conflict'
  | 'csrf_failed'
  | 'document_storage_unavailable'
  | 'draft_conflict'
  | 'draft_unavailable'
  | 'draft_version_required'
  | 'invalid_pdf'
  | 'malformed_response'
  | 'network_failure'
  | 'rate_limited'
  | 'unexpected_error'
  | 'unsupported_file_type'
  | 'upload_too_large'
  | 'vacancy_unavailable'
  | 'validation_error'

export interface NormalizedApiError {
  code: ApiErrorCode
  message: string
  status: number
  fields: Record<string, string[]>
  requestId: string | null
}

export class ApplyFlowApiError extends Error implements NormalizedApiError {
  code: ApiErrorCode
  status: number
  fields: Record<string, string[]>
  requestId: string | null

  constructor(error: NormalizedApiError) {
    super(error.message)
    this.name = 'ApplyFlowApiError'
    this.code = error.code
    this.status = error.status
    this.fields = error.fields
    this.requestId = error.requestId
  }
}

const KNOWN_CODES = new Set<ApiErrorCode>([
  'active_draft_conflict',
  'csrf_failed',
  'document_storage_unavailable',
  'draft_conflict',
  'draft_unavailable',
  'draft_version_required',
  'invalid_pdf',
  'rate_limited',
  'unsupported_file_type',
  'upload_too_large',
  'vacancy_unavailable',
  'validation_error',
])

const fallbackMessage = (status: number) => {
  if (status >= 500) return 'The service is temporarily unavailable. Try again later.'
  if (status === 0) return 'The network request did not finish. Your answers are still visible.'
  return 'The request could not be completed. Review the page and try again.'
}

const isStringArrayMap = (value: unknown): value is Record<string, string[]> => {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false
  return Object.values(value).every(
    (item) => Array.isArray(item) && item.every((message) => typeof message === 'string'),
  )
}

export const normalizeApiError = (payload: unknown, status: number): NormalizedApiError => {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return {
      code: status === 0 ? 'network_failure' : 'unexpected_error',
      message: fallbackMessage(status),
      status,
      fields: {},
      requestId: null,
    }
  }

  const envelope = (payload as { error?: unknown }).error
  if (!envelope || typeof envelope !== 'object' || Array.isArray(envelope)) {
    return {
      code: 'unexpected_error',
      message: fallbackMessage(status),
      status,
      fields: {},
      requestId: null,
    }
  }

  const error = envelope as {
    code?: unknown
    message?: unknown
    fields?: unknown
    request_id?: unknown
  }
  const code =
    typeof error.code === 'string' && KNOWN_CODES.has(error.code as ApiErrorCode)
      ? (error.code as ApiErrorCode)
      : 'unexpected_error'
  return {
    code,
    message: typeof error.message === 'string' ? error.message : fallbackMessage(status),
    status,
    fields: isStringArrayMap(error.fields) ? error.fields : {},
    requestId: typeof error.request_id === 'string' ? error.request_id : null,
  }
}
