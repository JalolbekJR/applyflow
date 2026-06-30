import { afterEach, describe, expect, it } from 'vitest'
import type { ApplyFlowApiError } from '~/api/errors'
import {
  enqueueDraftMutation,
  resetDraftMutationQueue,
  stopDraftMutationQueue,
} from '~/composables/useDraftMutations'

describe('draft mutation queue', () => {
  afterEach(() => {
    resetDraftMutationQueue()
  })

  it('serializes mutations so later operations see state written by earlier operations', async () => {
    let etag = '"draft-1"'
    const seen: string[] = []

    await Promise.all([
      enqueueDraftMutation(async () => {
        seen.push(etag)
        await Promise.resolve()
        etag = '"draft-2"'
      }),
      enqueueDraftMutation(async () => {
        seen.push(etag)
      }),
    ])

    expect(seen).toEqual(['"draft-1"', '"draft-2"'])
  })

  it('stops later mutations after a conflict until the queue is reset', async () => {
    stopDraftMutationQueue()

    await expect(enqueueDraftMutation(async () => undefined)).rejects.toMatchObject({
      code: 'draft_conflict',
    } satisfies Partial<ApplyFlowApiError>)

    resetDraftMutationQueue()

    await expect(enqueueDraftMutation(async () => 'saved')).resolves.toBe('saved')
  })
})
