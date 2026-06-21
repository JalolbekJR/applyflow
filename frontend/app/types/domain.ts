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

export interface UploadedDocumentMetadata {
  name: string
  size: number
  type: string
}

export interface ApplicationDraft {
  vacancySlug: string
  candidate: CandidateDetails
  experience: ExperienceData
  document: UploadedDocumentMetadata | null
}

export type SaveState = 'idle' | 'saving' | 'saved' | 'error'

export interface ApplicationSubmissionResult {
  vacancyTitle: string
  applicationReference: string
  statusLookupSecret: string
  submittedAt: string
}

export interface StatusLookupRequest {
  applicationReference: string
  statusLookupSecret: string
}

export interface StatusLookupResult {
  vacancyTitle: string
  submittedAt: string
  status: 'Received' | 'Under review' | 'Closed'
  nextStep: string
}

export interface ApiLikeErrorShape {
  code: string
  message: string
  fields?: Record<string, string[]>
  status: number
}
