import type { FieldErrors } from '~/utils/validation'

const candidateFieldMap: Record<string, string> = {
  full_name: 'fullName',
  portfolio_url: 'profileUrl',
  preferred_contact_method: 'preferredContactMethod',
}

const experienceFieldMap: Record<string, string> = {
  experience_level: 'experienceLevel',
  optional_message: 'message',
  consent_acknowledged: 'consentAcknowledged',
  non_field_errors: 'experienceEntries',
}

const experienceEntryFieldMap: Record<string, string> = {
  role_title: 'roleTitle',
  start_month: 'startMonth',
  end_month: 'endMonth',
  is_current: 'isCurrent',
  non_field_errors: 'experienceEntry',
}

const mapFields = (fields: Record<string, string[]>, map: Record<string, string>): FieldErrors =>
  Object.fromEntries(
    Object.entries(fields).map(([field, messages]) => [
      map[field] ?? field,
      messages[0] ?? 'Check this field.',
    ]),
  )

export const mapCandidateApiErrors = (fields: Record<string, string[]>): FieldErrors =>
  mapFields(fields, candidateFieldMap)

export const mapExperienceApiErrors = (fields: Record<string, string[]>): FieldErrors =>
  mapFields(fields, experienceFieldMap)

export const mapExperienceEntryApiErrors = (fields: Record<string, string[]>): FieldErrors =>
  mapFields(fields, experienceEntryFieldMap)
