import { ApplyFlowApiError } from '~/api/errors'

let mutationTail: Promise<unknown> = Promise.resolve()
let stoppedForConflict = false

export const resetDraftMutationQueue = () => {
  stoppedForConflict = false
  mutationTail = Promise.resolve()
}

export const stopDraftMutationQueue = () => {
  stoppedForConflict = true
}

export const enqueueDraftMutation = async <T>(operation: () => Promise<T>): Promise<T> => {
  const run = mutationTail
    .catch(() => undefined)
    .then(async () => {
      if (stoppedForConflict) {
        throw new ApplyFlowApiError({
          code: 'draft_conflict',
          message: 'Review the refreshed draft before saving again.',
          status: 409,
          fields: {},
          requestId: null,
        })
      }
      return operation()
    })
  mutationTail = run.catch(() => undefined)
  return run
}
