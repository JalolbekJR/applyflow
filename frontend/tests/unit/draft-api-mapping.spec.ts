import { afterEach, describe, expect, it, vi } from 'vitest'
import { applicationDraftFromApi, draftApi } from '~/api/drafts'
import { clearCsrfTokenForTests } from '~/api/client'
import type { ApiDraftAggregate } from '~/types/domain'

const aggregate: ApiDraftAggregate = {
  draft: {
    id: '11111111-2222-4333-8444-555555555555',
    status: 'active',
    version: 2,
    vacancy: { slug: 'frontend-developer', title: 'Frontend Developer' },
    candidate: {
      full_name: 'Avery Example',
      email: 'avery.candidate@example.test',
      phone: '',
      portfolio_url: 'https://example.test/avery',
      preferred_contact_method: 'email',
    },
    experience: {
      experience_level: 'mid_level',
      skills: ['Vue 3'],
      optional_message: 'Fictional context.',
      consent_acknowledged: true,
      consent_version: 'privacy-v1',
    },
    experience_entries: [
      {
        id: '22222222-3333-4444-8555-666666666666',
        organization: 'Fictional Systems',
        role_title: 'Interface Engineer',
        start_month: '2024-01',
        end_month: null,
        is_current: true,
        summary: 'Built accessible application flows.',
        position: 0,
      },
    ],
    document: {
      original_name_display: 'avery-example-cv.pdf',
      detected_content_type: 'application/pdf',
      size: 42000,
      uploaded_at: '2026-06-22T09:00:00Z',
    },
    last_activity_at: '2026-06-22T09:00:00Z',
    expires_at: '2026-06-29T09:00:00Z',
  },
}

describe('draft API mapping', () => {
  afterEach(() => {
    clearCsrfTokenForTests()
    vi.restoreAllMocks()
  })

  it('maps backend-safe aggregate fields without exposing private document metadata', () => {
    const draft = applicationDraftFromApi(aggregate)

    expect(draft.candidate.fullName).toBe('Avery Example')
    expect(draft.experience.experienceLevel).toBe('mid-level')
    expect(draft.experienceEntries).toEqual([
      {
        id: '22222222-3333-4444-8555-666666666666',
        organization: 'Fictional Systems',
        roleTitle: 'Interface Engineer',
        startMonth: '2024-01',
        endMonth: '',
        isCurrent: true,
        summary: 'Built accessible application flows.',
        position: 0,
      },
    ])
    expect(draft.document).toEqual({
      name: 'avery-example-cv.pdf',
      size: 42000,
      type: 'application/pdf',
    })
    expect(JSON.stringify(draft)).not.toContain('storage_key')
    expect(JSON.stringify(draft)).not.toContain('sha256')
  })

  it('serializes employment entry mutations through the draft API with CSRF and If-Match', async () => {
    const fetch = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ csrf_token: 'masked-token-value' }), {
          headers: { 'Content-Type': 'application/json' },
          status: 200,
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(aggregate), {
          headers: { 'Content-Type': 'application/json', ETag: '"draft-3"' },
          status: 201,
        }),
      )
    vi.stubGlobal('fetch', fetch)

    await draftApi.createExperienceEntry(
      aggregate.draft.id,
      '"draft-2"',
      applicationDraftFromApi(aggregate).experienceEntries[0],
    )

    expect(fetch).toHaveBeenNthCalledWith(
      2,
      `/api/v1/application-drafts/${aggregate.draft.id}/experiences/`,
      {
        method: 'POST',
        credentials: 'include',
        headers: expect.objectContaining({
          'If-Match': '"draft-2"',
          'X-CSRFToken': 'masked-token-value',
        }),
        body: JSON.stringify({
          organization: 'Fictional Systems',
          role_title: 'Interface Engineer',
          start_month: '2024-01',
          end_month: null,
          is_current: true,
          summary: 'Built accessible application flows.',
          position: 0,
        }),
      },
    )
  })
})
