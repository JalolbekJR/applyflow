import type {
  ApiLikeErrorShape,
  ApplicationDraft,
  ApplicationSubmissionResult,
  StatusLookupRequest,
  StatusLookupResult,
} from '~/types/domain'
import { cloneData } from '~/utils/clone-data'

const SIMULATED_REFERENCE = 'AF-9Q2K-M7P4'
const SIMULATED_SECRET = 'slk_9Wn6zQp4v2T8mR7cX5bL3kY1'
let saveFailuresRemaining = 0
let submitCallCount = 0

const delay = (milliseconds = 180) =>
  new Promise<void>((resolve) => globalThis.setTimeout(resolve, milliseconds))

export class ApiLikeError extends Error implements ApiLikeErrorShape {
  code: string
  status: number
  fields?: Record<string, string[]>

  constructor(shape: ApiLikeErrorShape) {
    super(shape.message)
    this.name = 'ApiLikeError'
    this.code = shape.code
    this.status = shape.status
    this.fields = shape.fields
  }
}

export interface ApplicationService {
  saveDraft(draft: ApplicationDraft): Promise<ApplicationDraft>
  submit(draft: ApplicationDraft, vacancyTitle: string): Promise<ApplicationSubmissionResult>
  lookupStatus(request: StatusLookupRequest): Promise<StatusLookupResult>
}

export const fixtureApplicationServiceControl = {
  failNextSave() {
    if (import.meta.env.DEV) saveFailuresRemaining += 1
  },
  reset() {
    if (!import.meta.env.DEV) return
    saveFailuresRemaining = 0
    submitCallCount = 0
  },
  getSubmitCallCount() {
    return submitCallCount
  },
}

export const fixtureApplicationService: ApplicationService = {
  async saveDraft(draft) {
    await delay()
    if (import.meta.env.DEV && saveFailuresRemaining > 0) {
      saveFailuresRemaining -= 1
      throw new ApiLikeError({
        code: 'simulated_save_failed',
        message: 'The simulated save did not finish.',
        status: 503,
      })
    }
    return cloneData(draft)
  },
  async submit(_draft, vacancyTitle) {
    if (import.meta.env.DEV) submitCallCount += 1
    await delay(260)
    return {
      vacancyTitle,
      applicationReference: SIMULATED_REFERENCE,
      statusLookupSecret: SIMULATED_SECRET,
      submittedAt: new Date().toISOString(),
    }
  },
  async lookupStatus(request) {
    await delay()
    const isValid =
      request.applicationReference.trim().toUpperCase() === SIMULATED_REFERENCE &&
      request.statusLookupSecret.trim() === SIMULATED_SECRET

    if (!isValid) {
      throw new ApiLikeError({
        code: 'status_lookup_failed',
        message: 'We could not verify those status details. Check both values and try again.',
        status: 404,
      })
    }

    return {
      vacancyTitle: 'Frontend Developer',
      submittedAt: '2026-06-20T09:00:00Z',
      status: 'Received',
      nextStep: 'Northline Studio has received the application. No action is needed right now.',
    }
  },
}

export const simulatedCredentials = {
  applicationReference: SIMULATED_REFERENCE,
  statusLookupSecret: SIMULATED_SECRET,
} as const
