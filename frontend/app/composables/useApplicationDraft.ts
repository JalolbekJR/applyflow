import type {
  ApplicationDraft,
  ApplicationSubmissionResult,
  CandidateDetails,
  ExperienceData,
  SaveState,
  UploadedDocumentMetadata,
} from '~/types/domain'
import { cloneData } from '~/utils/clone-data'

export type ApplicationDraftOwnership =
  | 'vacancy-unavailable'
  | 'no-draft'
  | 'matching-draft'
  | 'conflicting-draft'

export const getApplicationDraftOwnership = (
  draftVacancySlug: string,
  routeVacancySlug: string | null,
): ApplicationDraftOwnership => {
  if (!routeVacancySlug) return 'vacancy-unavailable'
  if (!draftVacancySlug) return 'no-draft'
  return draftVacancySlug === routeVacancySlug ? 'matching-draft' : 'conflicting-draft'
}

const emptyCandidate = (): CandidateDetails => ({
  fullName: '',
  email: '',
  phone: '',
  profileUrl: '',
  preferredContactMethod: '',
})

const emptyExperience = (): ExperienceData => ({
  experienceLevel: '',
  skills: [],
  message: '',
  consentAcknowledged: false,
})

export const createEmptyDraft = (vacancySlug = ''): ApplicationDraft => ({
  vacancySlug,
  candidate: emptyCandidate(),
  experience: emptyExperience(),
  document: null,
})

export const useApplicationDraft = () => {
  const draft = useState<ApplicationDraft>('application-draft', () => createEmptyDraft())
  const saveState = useState<SaveState>('application-save-state', () => 'idle')
  const submission = useState<ApplicationSubmissionResult | null>(
    'application-submission',
    () => null,
  )

  const selectVacancy = (vacancySlug: string) => {
    if (!draft.value.vacancySlug) draft.value.vacancySlug = vacancySlug
  }

  const enterApplicationStep = async (vacancySlug: string) => {
    const ownership = getApplicationDraftOwnership(draft.value.vacancySlug, vacancySlug)
    if (ownership === 'no-draft') {
      selectVacancy(vacancySlug)
      return 'matching-draft' as const
    }
    if (ownership === 'conflicting-draft') {
      await navigateTo(`/apply/${vacancySlug}`, { replace: true })
    }
    return ownership
  }

  const updateCandidate = (candidate: CandidateDetails) => {
    draft.value.candidate = cloneData(candidate)
  }

  const updateExperience = (experience: ExperienceData) => {
    draft.value.experience = cloneData(experience)
  }

  const updateDocument = (document: UploadedDocumentMetadata | null) => {
    draft.value.document = document ? { ...document } : null
  }

  const resetDraft = (vacancySlug = '') => {
    draft.value = createEmptyDraft(vacancySlug)
    saveState.value = 'idle'
    submission.value = null
  }

  return {
    draft,
    saveState,
    submission,
    enterApplicationStep,
    selectVacancy,
    updateCandidate,
    updateExperience,
    updateDocument,
    resetDraft,
  }
}
