import type {
  ApiDraftAggregate,
  ApplicationDraft,
  CandidateDetails,
  DraftEtag,
  ExperienceData,
  ExperienceEntry,
  ServerDraftState,
} from '~/types/domain'
import { apiRequest } from './client'
import { assertApiDraftAggregate, parseDraftEtag } from './runtime-guards'

const experienceFromApi = (value: string): ExperienceData['experienceLevel'] => {
  if (value === 'early_career') return 'early-career'
  if (value === 'mid_level') return 'mid-level'
  if (value === 'senior') return 'senior'
  return ''
}

const experienceToApi = (value: ExperienceData['experienceLevel']) => {
  if (value === 'early-career') return 'early_career'
  if (value === 'mid-level') return 'mid_level'
  return value
}

export const applicationDraftFromApi = (aggregate: ApiDraftAggregate): ApplicationDraft => ({
  vacancySlug: aggregate.draft.vacancy.slug,
  candidate: {
    fullName: aggregate.draft.candidate.full_name,
    email: aggregate.draft.candidate.email,
    phone: aggregate.draft.candidate.phone,
    profileUrl: aggregate.draft.candidate.portfolio_url,
    preferredContactMethod:
      aggregate.draft.candidate.preferred_contact_method === 'phone'
        ? 'phone'
        : aggregate.draft.candidate.preferred_contact_method === 'email'
          ? 'email'
          : '',
  },
  experience: {
    experienceLevel: experienceFromApi(aggregate.draft.experience.experience_level),
    skills: [...aggregate.draft.experience.skills],
    message: aggregate.draft.experience.optional_message,
    consentAcknowledged: aggregate.draft.experience.consent_acknowledged,
  },
  experienceEntries: aggregate.draft.experience_entries
    .map((entry) => ({
      id: entry.id,
      organization: entry.organization,
      roleTitle: entry.role_title,
      startMonth: entry.start_month,
      endMonth: entry.end_month ?? '',
      isCurrent: entry.is_current,
      summary: entry.summary,
      position: entry.position,
    }))
    .sort((left, right) => left.position - right.position),
  document: aggregate.draft.document
    ? {
        name: aggregate.draft.document.original_name_display,
        size: aggregate.draft.document.size,
        type: aggregate.draft.document.detected_content_type,
      }
    : null,
})

const stateFromResponse = (
  aggregate: ApiDraftAggregate,
  etag: string | null,
): ServerDraftState => ({
  id: aggregate.draft.id,
  version: aggregate.draft.version,
  etag: parseDraftEtag(etag),
  draft: applicationDraftFromApi(aggregate),
  expiresAt: aggregate.draft.expires_at,
})

const experienceEntryBody = (entry: ExperienceEntry) => ({
  organization: entry.organization,
  role_title: entry.roleTitle,
  start_month: entry.startMonth,
  end_month: entry.isCurrent ? null : entry.endMonth,
  is_current: entry.isCurrent,
  summary: entry.summary,
  position: entry.position,
})

export const draftApi = {
  async active(): Promise<ServerDraftState | null> {
    const response = await apiRequest('/api/v1/application-drafts/active/', {
      guard: (value) => (value === null ? null : assertApiDraftAggregate(value)),
    })
    if (response.status === 204 || response.data === null) return null
    return stateFromResponse(response.data, response.etag)
  },
  async create(vacancySlug: string): Promise<ServerDraftState> {
    const response = await apiRequest('/api/v1/application-drafts/', {
      method: 'POST',
      body: { vacancy_slug: vacancySlug },
      guard: assertApiDraftAggregate,
    })
    return stateFromResponse(response.data, response.etag)
  },
  async read(draftId: string): Promise<ServerDraftState> {
    const response = await apiRequest(`/api/v1/application-drafts/${draftId}/`, {
      guard: assertApiDraftAggregate,
    })
    return stateFromResponse(response.data, response.etag)
  },
  async patchCandidate(
    draftId: string,
    etag: DraftEtag,
    candidate: CandidateDetails,
  ): Promise<ServerDraftState> {
    const response = await apiRequest(`/api/v1/application-drafts/${draftId}/candidate/`, {
      method: 'PATCH',
      etag,
      body: {
        full_name: candidate.fullName,
        email: candidate.email,
        phone: candidate.phone,
        portfolio_url: candidate.profileUrl,
        preferred_contact_method: candidate.preferredContactMethod,
      },
      guard: assertApiDraftAggregate,
    })
    return stateFromResponse(response.data, response.etag)
  },
  async patchExperience(
    draftId: string,
    etag: DraftEtag,
    experience: ExperienceData,
  ): Promise<ServerDraftState> {
    const response = await apiRequest(`/api/v1/application-drafts/${draftId}/experience/`, {
      method: 'PATCH',
      etag,
      body: {
        experience_level: experienceToApi(experience.experienceLevel),
        skills: experience.skills,
        optional_message: experience.message,
        consent_acknowledged: experience.consentAcknowledged,
        consent_version: experience.consentAcknowledged ? 'privacy-v1' : '',
      },
      guard: assertApiDraftAggregate,
    })
    return stateFromResponse(response.data, response.etag)
  },
  async createExperienceEntry(
    draftId: string,
    etag: DraftEtag,
    entry: ExperienceEntry,
  ): Promise<ServerDraftState> {
    const response = await apiRequest(`/api/v1/application-drafts/${draftId}/experiences/`, {
      method: 'POST',
      etag,
      body: experienceEntryBody(entry),
      guard: assertApiDraftAggregate,
    })
    return stateFromResponse(response.data, response.etag)
  },
  async patchExperienceEntry(
    draftId: string,
    etag: DraftEtag,
    entry: ExperienceEntry,
  ): Promise<ServerDraftState> {
    const response = await apiRequest(
      `/api/v1/application-drafts/${draftId}/experiences/${entry.id}/`,
      {
        method: 'PATCH',
        etag,
        body: experienceEntryBody(entry),
        guard: assertApiDraftAggregate,
      },
    )
    return stateFromResponse(response.data, response.etag)
  },
  async deleteExperienceEntry(
    draftId: string,
    etag: DraftEtag,
    experienceId: string,
  ): Promise<DraftEtag> {
    const response = await apiRequest(
      `/api/v1/application-drafts/${draftId}/experiences/${experienceId}/`,
      {
        method: 'DELETE',
        etag,
        guard: (value) => value,
      },
    )
    return parseDraftEtag(response.etag)
  },
  async abandon(draftId: string, etag: DraftEtag): Promise<void> {
    await apiRequest(`/api/v1/application-drafts/${draftId}/`, {
      method: 'DELETE',
      etag,
      guard: (value) => value,
    })
  },
}
