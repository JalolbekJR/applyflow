import type { ApiDraftAggregate, ApiExperienceEntry, ApiVacancy, DraftEtag } from '~/types/domain'

const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const etagPattern = /^"draft-[1-9][0-9]*"$/

export const isRecord = (value: unknown): value is Record<string, unknown> =>
  Boolean(value) && typeof value === 'object' && !Array.isArray(value)

const isString = (value: unknown): value is string => typeof value === 'string'
const isNullableString = (value: unknown): value is string | null =>
  value === null || typeof value === 'string'
const isBoolean = (value: unknown): value is boolean => typeof value === 'boolean'
const isNumber = (value: unknown): value is number =>
  typeof value === 'number' && Number.isFinite(value)

const isStringArray = (value: unknown): value is string[] =>
  Array.isArray(value) && value.every(isString)

export const assertRelativeApiPath = (path: string): void => {
  if (!path.startsWith('/api/v1/') || path.startsWith('//') || /^[a-z][a-z0-9+.-]*:/i.test(path)) {
    throw new Error('API requests must use relative /api/v1/ paths.')
  }
}

export const parseDraftEtag = (value: string | null): DraftEtag => {
  if (!value || !etagPattern.test(value)) {
    throw new Error('Authorized draft response did not include a valid ETag.')
  }
  return value as DraftEtag
}

export const isApiVacancy = (value: unknown): value is ApiVacancy => {
  if (!isRecord(value)) return false
  return (
    isString(value.slug) &&
    isString(value.title) &&
    isString(value.summary) &&
    isString(value.description) &&
    isStringArray(value.responsibilities) &&
    isStringArray(value.requirements) &&
    isStringArray(value.benefits) &&
    isString(value.location) &&
    isString(value.work_format) &&
    isString(value.employment_type) &&
    isString(value.status) &&
    isNullableString(value.published_at) &&
    isNullableString(value.closing_at)
  )
}

export const assertApiVacancy = (value: unknown): ApiVacancy => {
  if (!isApiVacancy(value)) throw new Error('Vacancy response was malformed.')
  return value
}

export const assertApiVacancyList = (value: unknown): ApiVacancy[] => {
  if (!Array.isArray(value) || !value.every(isApiVacancy)) {
    throw new Error('Vacancy list response was malformed.')
  }
  return value
}

const isApiExperienceEntry = (value: unknown): value is ApiExperienceEntry => {
  if (!isRecord(value)) return false
  return (
    isString(value.id) &&
    uuidPattern.test(value.id) &&
    isString(value.organization) &&
    isString(value.role_title) &&
    isString(value.start_month) &&
    isNullableString(value.end_month) &&
    isBoolean(value.is_current) &&
    isString(value.summary) &&
    isNumber(value.position)
  )
}

export const assertApiDraftAggregate = (value: unknown): ApiDraftAggregate => {
  if (!isRecord(value) || !isRecord(value.draft)) {
    throw new Error('Draft response was malformed.')
  }
  const draft = value.draft
  if (
    !isString(draft.id) ||
    !uuidPattern.test(draft.id) ||
    draft.status !== 'active' ||
    !isNumber(draft.version) ||
    !isRecord(draft.vacancy) ||
    !isString(draft.vacancy.slug) ||
    !isString(draft.vacancy.title) ||
    !isRecord(draft.candidate) ||
    !isString(draft.candidate.full_name) ||
    !isString(draft.candidate.email) ||
    !isString(draft.candidate.phone) ||
    !isString(draft.candidate.portfolio_url) ||
    !isString(draft.candidate.preferred_contact_method) ||
    !isRecord(draft.experience) ||
    !isString(draft.experience.experience_level) ||
    !isStringArray(draft.experience.skills) ||
    !isString(draft.experience.optional_message) ||
    !isBoolean(draft.experience.consent_acknowledged) ||
    !isString(draft.experience.consent_version) ||
    !Array.isArray(draft.experience_entries) ||
    !draft.experience_entries.every(isApiExperienceEntry) ||
    !isString(draft.last_activity_at) ||
    !isString(draft.expires_at)
  ) {
    throw new Error('Draft response was malformed.')
  }
  if (draft.document !== null) {
    if (
      !isRecord(draft.document) ||
      !isString(draft.document.original_name_display) ||
      !isString(draft.document.detected_content_type) ||
      !isNumber(draft.document.size) ||
      !isString(draft.document.uploaded_at)
    ) {
      throw new Error('Draft document response was malformed.')
    }
  }
  return value as unknown as ApiDraftAggregate
}

export const assertCsrfResponse = (value: unknown): { csrf_token: string } => {
  if (!isRecord(value) || !isString(value.csrf_token) || value.csrf_token.length < 16) {
    throw new Error('CSRF response was malformed.')
  }
  return { csrf_token: value.csrf_token }
}
