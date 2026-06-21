import { beforeEach, describe, expect, it } from 'vitest'
import {
  ApiLikeError,
  fixtureApplicationService,
  fixtureApplicationServiceControl,
} from '~/services/application-service'
import { createEmptyDraft } from '~/composables/useApplicationDraft'

describe('fixture application failure control', () => {
  beforeEach(() => {
    fixtureApplicationServiceControl.reset()
  })

  it('fails exactly one save and then permits a retry', async () => {
    const draft = createEmptyDraft('frontend-developer')
    fixtureApplicationServiceControl.failNextSave()

    await expect(fixtureApplicationService.saveDraft(draft)).rejects.toBeInstanceOf(ApiLikeError)
    await expect(fixtureApplicationService.saveDraft(draft)).resolves.toEqual(draft)
  })
})
