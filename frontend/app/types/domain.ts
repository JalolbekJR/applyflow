export type VacancyStatus = 'active' | 'closed'
export type WorkFormat = 'Hybrid' | 'Remote-friendly' | 'On-site'
export type EmploymentType = 'Full-time'

export interface Vacancy {
  id: string
  slug: string
  title: string
  discipline: 'Engineering' | 'Product design'
  location: string
  workFormat: WorkFormat
  employmentType: EmploymentType
  summary: string
  responsibilities: string[]
  essentialRequirements: string[]
  niceToHave: string[]
  status: VacancyStatus
}

export interface ApiVacancy {
  slug: string
  title: string
  summary: string
  description: string
  responsibilities: string[]
  requirements: string[]
  benefits: string[]
  location: string
  work_format: string
  employment_type: string
  status: string
  published_at: string | null
  closing_at: string | null
}

export interface CandidateDetails {
  fullName: string
  email: string
  phone: string
  profileUrl: string
  preferredContactMethod: '' | 'email' | 'phone'
}

export interface ExperienceData {
  experienceLevel: '' | 'early-career' | 'mid-level' | 'senior'
  skills: string[]
  message: string
  consentAcknowledged: boolean
}

export interface ExperienceEntry {
  id: string
  organization: string
  roleTitle: string
  startMonth: string
  endMonth: string
  isCurrent: boolean
  summary: string
  position: number
}

export interface UploadedDocumentMetadata {
  name: string
  size: number
  type: string
}

export interface ApplicationDraft {
  vacancySlug: string
  candidate: CandidateDetails
  experience: ExperienceData
  experienceEntries: ExperienceEntry[]
  document: UploadedDocumentMetadata | null
}

export type SaveState =
  | 'idle'
  | 'dirty'
  | 'waiting'
  | 'saving'
  | 'saved'
  | 'error'
  | 'conflict'
  | 'offline'

export type DraftEtag = `"draft-${number}"`

export interface ApiDocumentMetadata {
  original_name_display: string
  detected_content_type: string
  size: number
  uploaded_at: string
}

export interface ApiExperienceEntry {
  id: string
  organization: string
  role_title: string
  start_month: string
  end_month: string | null
  is_current: boolean
  summary: string
  position: number
}

export interface ApiDraftAggregate {
  draft: {
    id: string
    status: 'active'
    version: number
    vacancy: {
      slug: string
      title: string
    }
    candidate: {
      full_name: string
      email: string
      phone: string
      portfolio_url: string
      preferred_contact_method: string
    }
    experience: {
      experience_level: string
      skills: string[]
      optional_message: string
      consent_acknowledged: boolean
      consent_version: string
    }
    experience_entries: ApiExperienceEntry[]
    document: ApiDocumentMetadata | null
    last_activity_at: string
    expires_at: string
  }
}

export interface ServerDraftState {
  id: string
  version: number
  etag: DraftEtag
  draft: ApplicationDraft
  expiresAt: string
}
