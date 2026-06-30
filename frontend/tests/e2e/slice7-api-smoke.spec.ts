import { expect, test, type Page, type Route } from '@playwright/test'

type DraftPayload = ReturnType<typeof createDraftPayload>

const vacancy = {
  slug: 'frontend-developer',
  title: 'Frontend Developer',
  summary: 'Build accessible candidate-facing interfaces.',
  description: 'A fictional vacancy used for Slice 7 browser smoke coverage.',
  responsibilities: ['Build resilient Nuxt interfaces', 'Keep candidate flows accessible'],
  requirements: ['Vue 3', 'TypeScript', 'Accessibility'],
  benefits: ['Calm product culture'],
  location: 'Tashkent, Uzbekistan',
  work_format: 'hybrid',
  employment_type: 'full_time',
  status: 'published',
  published_at: '2026-06-20T09:00:00Z',
  closing_at: null,
}

const waitForNuxtHydration = (page: Page) =>
  page.waitForFunction(() => {
    const root = document.querySelector('#__nuxt') as HTMLElement & {
      __vue_app__?: {
        config: { globalProperties: { $nuxt?: { isHydrating: boolean } } }
      }
    }
    const nuxt = root.__vue_app__?.config.globalProperties.$nuxt
    return Boolean(nuxt && !nuxt.isHydrating)
  })

const createDraftPayload = () => ({
  draft: {
    id: '11111111-2222-4333-8444-555555555555',
    status: 'active',
    version: 1,
    vacancy: { slug: vacancy.slug, title: vacancy.title },
    candidate: {
      full_name: '',
      email: '',
      phone: '',
      portfolio_url: '',
      preferred_contact_method: '',
    },
    experience: {
      experience_level: '',
      skills: [],
      optional_message: '',
      consent_acknowledged: false,
      consent_version: '',
    },
    experience_entries: [],
    document: null,
    last_activity_at: '2026-06-24T00:00:00Z',
    expires_at: '2026-07-01T00:00:00Z',
  },
})

const json = async (
  route: Route,
  status: number,
  body: unknown,
  headers: Record<string, string> = {},
) =>
  route.fulfill({
    status,
    contentType: 'application/json',
    headers,
    body: body === null ? '' : JSON.stringify(body),
  })

const installApiRoutes = async (page: Page) => {
  let draft: DraftPayload | null = null

  const mutateDraft = (updater: (payload: DraftPayload) => void) => {
    if (!draft) draft = createDraftPayload()
    updater(draft)
    draft.draft.version += 1
    return draft
  }

  await page.route('**/api/v1/**', async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    const path = url.pathname
    const method = request.method()

    if (path === '/api/v1/csrf/') {
      await json(route, 200, { csrf_token: 'masked-csrf-token-for-browser-test' })
      return
    }
    if (path === '/api/v1/vacancies/' && method === 'GET') {
      await json(route, 200, [vacancy])
      return
    }
    if (path === `/api/v1/vacancies/${vacancy.slug}/` && method === 'GET') {
      await json(route, 200, vacancy)
      return
    }
    if (path === '/api/v1/application-drafts/active/' && method === 'GET') {
      if (!draft) {
        await route.fulfill({ status: 204, body: '' })
        return
      }
      await json(route, 200, draft, { ETag: `"draft-${draft.draft.version}"` })
      return
    }
    if (path === '/api/v1/application-drafts/' && method === 'POST') {
      if (!draft) draft = createDraftPayload()
      await json(route, 201, draft, { ETag: `"draft-${draft.draft.version}"` })
      return
    }
    if (
      path === `/api/v1/application-drafts/${createDraftPayload().draft.id}/` &&
      method === 'GET'
    ) {
      await json(route, 200, draft ?? createDraftPayload(), {
        ETag: `"draft-${draft?.draft.version ?? 1}"`,
      })
      return
    }
    if (path.endsWith('/candidate/') && method === 'PATCH') {
      const body = JSON.parse(request.postData() ?? '{}')
      const payload = mutateDraft((current) => {
        current.draft.candidate = { ...current.draft.candidate, ...body }
      })
      await json(route, 200, payload, { ETag: `"draft-${payload.draft.version}"` })
      return
    }
    if (path.endsWith('/experience/') && method === 'PATCH') {
      const body = JSON.parse(request.postData() ?? '{}')
      const payload = mutateDraft((current) => {
        current.draft.experience = { ...current.draft.experience, ...body }
      })
      await json(route, 200, payload, { ETag: `"draft-${payload.draft.version}"` })
      return
    }
    if (path.endsWith('/experiences/') && method === 'POST') {
      const body = JSON.parse(request.postData() ?? '{}')
      const payload = mutateDraft((current) => {
        current.draft.experience_entries = [
          {
            id: '22222222-3333-4444-8555-666666666666',
            organization: body.organization,
            role_title: body.role_title,
            start_month: body.start_month,
            end_month: body.end_month,
            is_current: body.is_current,
            summary: body.summary,
            position: body.position,
          },
        ]
      })
      await json(route, 201, payload, { ETag: `"draft-${payload.draft.version}"` })
      return
    }
    if (path.endsWith('/documents/cv/') && method === 'PUT') {
      const payload = mutateDraft((current) => {
        current.draft.document = {
          original_name_display: 'avery-example-cv.pdf',
          detected_content_type: 'application/pdf',
          size: 42137,
          uploaded_at: '2026-06-24T00:00:00Z',
        }
      })
      await json(route, 201, payload, { ETag: `"draft-${payload.draft.version}"` })
      return
    }
    if (path.endsWith('/documents/cv/') && method === 'DELETE') {
      const payload = mutateDraft((current) => {
        current.draft.document = null
      })
      await route.fulfill({ status: 204, headers: { ETag: `"draft-${payload.draft.version}"` } })
      return
    }

    await json(route, 404, {
      error: {
        code: 'draft_unavailable',
        message: 'The application draft is unavailable.',
        fields: {},
        request_id: 'req_playwright',
      },
    })
  })
}

test('candidate draft flow uses current Slice 7 API states without fake submission', async ({
  page,
}) => {
  await installApiRoutes(page)

  await page.goto('/vacancies')
  await waitForNuxtHydration(page)
  await page.getByRole('link', { name: 'Frontend Developer' }).click()
  await page.getByRole('link', { name: 'Start application' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Before you begin' })).toBeVisible()

  await page.getByRole('link', { name: 'Continue to candidate details' }).click()
  await page.getByLabel('Full name').fill('Avery Example')
  await page.getByLabel('Email address').fill('avery.candidate@example.test')
  await page.getByLabel('Email', { exact: true }).check()
  await page.getByRole('button', { name: 'Continue to experience' }).click()
  await expect(page).toHaveURL(/\/apply\/frontend-developer\/experience$/)

  await page.getByLabel('Experience level').selectOption('mid-level')
  await page.getByLabel('Relevant skills').fill('Vue 3, TypeScript, accessibility')
  await page.getByLabel('Organization').fill('Fictional Systems')
  await page.getByLabel('Role title').fill('Interface Engineer')
  await page.getByLabel('Start month').fill('2024-01')
  await page.getByLabel('This is my current role').check()
  await page.getByRole('button', { name: 'Add role' }).click()
  await expect(page.getByText('Fictional Systems')).toBeVisible()

  await page.locator('#cv-upload').setInputFiles('tests/fixtures/avery-example-cv.pdf')
  await expect(page.getByText('avery-example-cv.pdf')).toBeVisible()
  await page.getByLabel(/I understand this frontend/).check()
  await page.getByRole('button', { name: 'Continue to review' }).click()

  await expect(
    page.getByRole('heading', { level: 1, name: 'Review your application' }),
  ).toBeVisible()
  await expect(page.getByRole('region', { name: 'Candidate details' })).toContainText(
    'Avery Example',
  )
  await expect(page.getByRole('region', { name: 'CV document' })).toContainText(
    'avery-example-cv.pdf',
  )
  await expect(page.getByRole('button', { name: 'Submit application unavailable' })).toBeDisabled()
})

test('mobile layout avoids horizontal overflow in the API-backed vacancy detail', async ({
  page,
}) => {
  await installApiRoutes(page)
  await page.setViewportSize({ width: 320, height: 800 })
  await page.goto('/vacancies/frontend-developer')
  await waitForNuxtHydration(page)

  await expect(page.getByRole('heading', { level: 1, name: 'Frontend Developer' })).toBeVisible()
  await expect
    .poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth))
    .toBe(true)
})
