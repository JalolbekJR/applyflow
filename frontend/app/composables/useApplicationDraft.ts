import type {
  ApplicationDraft,
  CandidateDetails,
  DraftEtag,
  ExperienceData,
  ExperienceEntry,
  SaveState,
  ServerDraftState,
  UploadedDocumentMetadata,
} from '~/types/domain'
import { draftApi } from '~/api/drafts'
import { deleteCvDocument, uploadCvDocument } from '~/api/documents'
import { ApplyFlowApiError } from '~/api/errors'
import {
  enqueueDraftMutation,
  resetDraftMutationQueue,
  stopDraftMutationQueue,
} from '~/composables/useDraftMutations'
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

const versionFromEtag = (etag: DraftEtag) => Number(etag.match(/^"draft-([1-9][0-9]*)"$/)?.[1])

export const createEmptyDraft = (vacancySlug = ''): ApplicationDraft => ({
  vacancySlug,
  candidate: emptyCandidate(),
  experience: emptyExperience(),
  experienceEntries: [],
  document: null,
})

export const useApplicationDraft = () => {
  const draft = useState<ApplicationDraft>('application-draft', () => createEmptyDraft())
  const saveState = useState<SaveState>('application-save-state', () => 'idle')
  const serverDraft = useState<ServerDraftState | null>('application-server-draft', () => null)
  const lastError = useState<ApplyFlowApiError | null>('application-api-error', () => null)

  const applyServerDraft = (state: ServerDraftState) => {
    serverDraft.value = state
    draft.value = cloneData(state.draft)
    lastError.value = null
  }

  const selectVacancy = (vacancySlug: string) => {
    if (!draft.value.vacancySlug) draft.value.vacancySlug = vacancySlug
  }

  const enterApplicationStep = async (vacancySlug: string) => {
    if (serverDraft.value?.draft.vacancySlug === vacancySlug) return 'matching-draft' as const
    try {
      applyServerDraft(await draftApi.create(vacancySlug))
      resetDraftMutationQueue()
      return 'matching-draft' as const
    } catch (error) {
      if (error instanceof ApplyFlowApiError && error.code === 'active_draft_conflict') {
        const active = await draftApi.active()
        if (active) {
          applyServerDraft(active)
          resetDraftMutationQueue()
        }
        return 'conflicting-draft' as const
      }
      if (error instanceof ApplyFlowApiError) {
        lastError.value = error
        return error.code === 'vacancy_unavailable' ? 'vacancy-unavailable' : 'no-draft'
      }
      throw error
    }
  }

  const restoreActiveDraft = async () => {
    const active = await draftApi.active()
    if (!active) return null
    applyServerDraft(active)
    resetDraftMutationQueue()
    return active
  }

  const updateCandidate = (candidate: CandidateDetails) => {
    draft.value.candidate = cloneData(candidate)
    saveState.value = 'dirty'
  }

  const updateExperience = (experience: ExperienceData) => {
    draft.value.experience = cloneData(experience)
    saveState.value = 'dirty'
  }

  const updateExperienceEntries = (entries: ExperienceEntry[]) => {
    draft.value.experienceEntries = cloneData(entries).sort(
      (left, right) => left.position - right.position,
    )
    saveState.value = 'dirty'
  }

  const updateDocument = (document: UploadedDocumentMetadata | null) => {
    draft.value.document = document ? { ...document } : null
  }

  const requireServerDraft = (): { id: string; etag: DraftEtag } => {
    if (!serverDraft.value) {
      throw new ApplyFlowApiError({
        code: 'draft_version_required',
        message: 'Refresh the application draft before saving.',
        status: 428,
        fields: {},
        requestId: null,
      })
    }
    return { id: serverDraft.value.id, etag: serverDraft.value.etag }
  }

  const handleMutationError = async (error: unknown) => {
    if (error instanceof ApplyFlowApiError) {
      lastError.value = error
      if (
        error.code === 'draft_conflict' ||
        error.code === 'draft_version_required' ||
        error.code === 'network_failure'
      ) {
        stopDraftMutationQueue()
        saveState.value = error.code === 'network_failure' ? 'offline' : 'conflict'
        await restoreActiveDraft()
      } else {
        saveState.value = 'error'
      }
    }
  }

  const saveCandidate = async (candidate: CandidateDetails) => {
    updateCandidate(candidate)
    saveState.value = 'saving'
    try {
      await enqueueDraftMutation(async () => {
        const current = requireServerDraft()
        applyServerDraft(await draftApi.patchCandidate(current.id, current.etag, candidate))
      })
      saveState.value = 'saved'
    } catch (error) {
      await handleMutationError(error)
      throw error
    }
  }

  const saveExperience = async (experience: ExperienceData) => {
    updateExperience(experience)
    saveState.value = 'saving'
    try {
      await enqueueDraftMutation(async () => {
        const current = requireServerDraft()
        applyServerDraft(await draftApi.patchExperience(current.id, current.etag, experience))
      })
      saveState.value = 'saved'
    } catch (error) {
      await handleMutationError(error)
      throw error
    }
  }

  const saveExperienceEntry = async (entry: ExperienceEntry) => {
    saveState.value = 'saving'
    try {
      await enqueueDraftMutation(async () => {
        const current = requireServerDraft()
        const state =
          entry.id === 'new'
            ? await draftApi.createExperienceEntry(current.id, current.etag, entry)
            : await draftApi.patchExperienceEntry(current.id, current.etag, entry)
        applyServerDraft(state)
      })
      saveState.value = 'saved'
    } catch (error) {
      await handleMutationError(error)
      throw error
    }
  }

  const removeExperienceEntry = async (experienceId: string) => {
    saveState.value = 'saving'
    try {
      await enqueueDraftMutation(async () => {
        const current = requireServerDraft()
        await draftApi.deleteExperienceEntry(current.id, current.etag, experienceId)
        applyServerDraft(await draftApi.read(current.id))
      })
      saveState.value = 'saved'
    } catch (error) {
      await handleMutationError(error)
      throw error
    }
  }

  const uploadDocument = async (
    file: File,
    options: {
      onProgress?: (loaded: number, total: number | null) => void
      signal?: AbortSignal
    } = {},
  ) => {
    saveState.value = 'saving'
    try {
      await enqueueDraftMutation(async () => {
        const current = requireServerDraft()
        applyServerDraft(
          await uploadCvDocument({
            draftId: current.id,
            etag: current.etag,
            file,
            onProgress: options.onProgress,
            signal: options.signal,
          }),
        )
      })
      saveState.value = 'saved'
    } catch (error) {
      await handleMutationError(error)
      throw error
    }
  }

  const deleteDocument = async () => {
    saveState.value = 'saving'
    try {
      await enqueueDraftMutation(async () => {
        const current = requireServerDraft()
        const etag = await deleteCvDocument(current.id, current.etag)
        const nextDraft = cloneData(draft.value)
        nextDraft.document = null
        draft.value = nextDraft
        serverDraft.value = {
          id: current.id,
          version: versionFromEtag(etag),
          etag,
          draft: cloneData(nextDraft),
          expiresAt: serverDraft.value?.expiresAt ?? '',
        }
        lastError.value = null
      })
      saveState.value = 'saved'
    } catch (error) {
      await handleMutationError(error)
      throw error
    }
  }

  const abandonServerDraft = async () => {
    const current = requireServerDraft()
    await draftApi.abandon(current.id, current.etag)
    resetDraft()
  }

  const resetDraft = (vacancySlug = '') => {
    draft.value = createEmptyDraft(vacancySlug)
    serverDraft.value = null
    lastError.value = null
    saveState.value = 'idle'
    resetDraftMutationQueue()
  }

  return {
    draft,
    saveState,
    serverDraft,
    lastError,
    enterApplicationStep,
    restoreActiveDraft,
    selectVacancy,
    updateCandidate,
    updateExperience,
    updateExperienceEntries,
    updateDocument,
    saveCandidate,
    saveExperience,
    saveExperienceEntry,
    removeExperienceEntry,
    uploadDocument,
    deleteDocument,
    abandonServerDraft,
    resetDraft,
  }
}
