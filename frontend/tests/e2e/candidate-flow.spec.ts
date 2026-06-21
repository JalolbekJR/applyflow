import { expect, test, type Page } from '@playwright/test'

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

const navigateInApp = (page: Page, path: string) =>
  page.evaluate(async (destination) => {
    const root = document.querySelector('#__nuxt') as HTMLElement & {
      __vue_app__?: {
        config: { globalProperties: { $router: { push: (path: string) => Promise<void> } } }
      }
    }
    await root.__vue_app__?.config.globalProperties.$router.push(destination)
  }, path)

const fillCandidateDetails = async (page: Page) => {
  await page.getByLabel('Full name').fill('Avery Example')
  await page.getByLabel('Email address').fill('avery.candidate@example.test')
  await page.getByLabel('Portfolio, GitHub, or LinkedIn').fill('https://example.test/avery')
  await page.getByLabel('Email', { exact: true }).check()
}

const fillExperience = async (page: Page) => {
  await page.getByLabel('Experience level').selectOption('mid-level')
  await page.getByLabel('Relevant skills').fill('Vue 3, TypeScript, accessibility')
  await page.locator('#cv-upload').setInputFiles('tests/fixtures/avery-example-cv.pdf')
  await expect(page.getByText('ready for this simulated application')).toBeVisible()
  await page.getByLabel(/I understand this frontend/).check()
}

const reachReview = async (page: Page) => {
  await page.goto('/apply/frontend-developer')
  await waitForNuxtHydration(page)
  await page.getByRole('link', { name: 'Continue to candidate details' }).click()
  await fillCandidateDetails(page)
  await page.getByRole('button', { name: 'Continue to experience' }).click()
  await fillExperience(page)
  await page.getByRole('button', { name: 'Continue to review' }).click()
  await expect(
    page.getByRole('heading', { level: 1, name: 'Review your application' }),
  ).toBeVisible()
}

const createDistinctiveFrontendDraft = async (page: Page) => {
  await page.goto('/apply/frontend-developer/details')
  await waitForNuxtHydration(page)
  await page.getByLabel('Full name').fill('Avery Frontend Draft')
  await page.getByLabel('Email address').fill('avery.frontend@example.test')
  await page.getByLabel('Email', { exact: true }).check()
  await page.getByRole('button', { name: 'Continue to experience' }).click()
  await expect(page).toHaveURL(/\/apply\/frontend-developer\/experience$/)
}

const expectBackendConflictAndRecoverFrontendDraft = async (page: Page, path: string) => {
  await navigateInApp(page, path)
  await expect(page).toHaveURL(/\/apply\/backend-developer$/)
  await expect(
    page.getByRole('heading', { name: 'You already started another application' }),
  ).toBeVisible()
  await expect(page.getByText('Avery Frontend Draft')).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Submit simulated application' })).toHaveCount(0)

  await page.getByRole('button', { name: 'Continue existing application' }).click()
  await expect(page).toHaveURL(/\/apply\/frontend-developer\/details$/)
  await expect(page.getByLabel('Full name')).toHaveValue('Avery Frontend Draft')
  await expect(page.getByLabel('Email address')).toHaveValue('avery.frontend@example.test')
}

test('candidate can move from vacancy discovery through status lookup', async ({ page }) => {
  await page.goto('/vacancies')
  await waitForNuxtHydration(page)
  await page.getByRole('link', { name: 'Frontend Developer' }).click()
  const vacancyHeading = page.getByRole('heading', { level: 1, name: 'Frontend Developer' })
  await expect(vacancyHeading).toBeVisible()
  await expect(vacancyHeading).toBeFocused()
  await page.getByRole('link', { name: 'Start application' }).click()
  await expect(page.getByText('Step 1 of 4 - Position')).toBeVisible()
  await expect(page.getByRole('heading', { level: 1, name: 'Before you begin' })).toBeFocused()
  await page.getByRole('link', { name: 'Continue to candidate details' }).click()

  await page.getByRole('button', { name: 'Continue to experience' }).click()
  await expect(page.getByRole('alert')).toBeFocused()
  await fillCandidateDetails(page)
  await page.getByRole('button', { name: 'Continue to experience' }).click()

  await fillExperience(page)
  await page.getByRole('button', { name: 'Continue to review' }).click()

  const candidateSection = page.getByRole('region', { name: 'Candidate details' })
  await candidateSection.getByRole('link', { name: 'Edit' }).click()
  await expect(page).toHaveURL(/details\?return=review/)
  await expect(page.getByRole('heading', { level: 1, name: 'Candidate details' })).toBeFocused()
  await page.getByRole('button', { name: 'Save and return to review' }).click()
  await page.getByRole('button', { name: 'Submit simulated application' }).click()
  await expect(
    page.getByRole('heading', { name: 'Keep these status details somewhere private' }),
  ).toBeVisible()
  await expect(page.getByText('AF-9Q2K-M7P4')).toBeVisible()

  await page.getByRole('link', { name: 'Check application status' }).click()
  await page.getByLabel('Application reference').fill('AF-9Q2K-M7P4')
  await page.getByLabel('Private status secret').fill('slk_9Wn6zQp4v2T8mR7cX5bL3kY1')
  await page.getByRole('button', { name: 'Check status' }).click()
  await expect(page.getByRole('heading', { name: 'Received' })).toBeVisible()
})

test('invalid application routes recover without creating a false draft conflict', async ({
  page,
}) => {
  await page.goto('/apply/not-a-role')
  await waitForNuxtHydration(page)

  for (const path of [
    '/apply/not-a-role',
    '/apply/not-a-role/details',
    '/apply/not-a-role/experience',
    '/apply/not-a-role/review',
  ]) {
    await navigateInApp(page, path)
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('This vacancy cannot be found')
    await expect(page.getByRole('link', { name: 'View open vacancies' })).toBeVisible()
  }

  await navigateInApp(page, '/apply/frontend-developer')
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Before you begin')
  await expect(page.getByText('You already started another application')).toHaveCount(0)
  await expect(page.getByRole('link', { name: 'Continue to candidate details' })).toBeVisible()
})

for (const mismatch of [
  { name: 'details', path: '/apply/backend-developer/details' },
  { name: 'experience', path: '/apply/backend-developer/experience' },
  { name: 'review', path: '/apply/backend-developer/review' },
]) {
  test(`direct ${mismatch.name} navigation preserves the original vacancy draft`, async ({
    page,
  }) => {
    await createDistinctiveFrontendDraft(page)
    await expectBackendConflictAndRecoverFrontendDraft(page, mismatch.path)
  })
}

test('a conflicting draft can be deliberately abandoned before starting the requested vacancy', async ({
  page,
}) => {
  await createDistinctiveFrontendDraft(page)
  await navigateInApp(page, '/apply/backend-developer/review')
  await expect(page).toHaveURL(/\/apply\/backend-developer$/)

  await page.getByRole('button', { name: 'Abandon existing draft' }).click()
  await page.getByRole('button', { name: 'Delete and start this role' }).click()
  await expect(
    page.getByRole('heading', { name: 'You already started another application' }),
  ).toHaveCount(0)
  await page.getByRole('link', { name: 'Continue to candidate details' }).click()

  await expect(page).toHaveURL(/\/apply\/backend-developer\/details$/)
  await expect(page.getByRole('complementary', { name: 'Selected vacancy' })).toContainText(
    'Backend Developer',
  )
  await expect(page.getByLabel('Full name')).toHaveValue('')
  await expect(page.getByLabel('Email address')).toHaveValue('')
})

test('error summaries focus text, grouped radio, upload, and consent destinations', async ({
  page,
}) => {
  await page.goto('/apply/frontend-developer/details')
  await waitForNuxtHydration(page)
  await page.getByRole('button', { name: 'Continue to experience' }).click()

  const detailsSummary = page.getByRole('alert')
  await expect(detailsSummary).toBeFocused()
  await expect(page.getByLabel('Full name')).toHaveAttribute(
    'aria-describedby',
    'fullName-hint fullName-error',
  )
  await detailsSummary.getByRole('link', { name: 'Enter your full name.' }).click()
  await expect(page.getByLabel('Full name')).toBeFocused()
  await expect(page).toHaveURL(/#fullName$/)

  await detailsSummary.getByRole('link', { name: 'Choose a preferred contact method.' }).click()
  const contactGroup = page.locator('#preferredContactMethod')
  await expect(contactGroup).toBeFocused()
  await expect(contactGroup).toHaveAttribute(
    'aria-describedby',
    'contact-hint preferredContactMethod-error',
  )

  await navigateInApp(page, '/apply/frontend-developer/experience')
  await page.getByRole('button', { name: 'Continue to review' }).click()
  const experienceSummary = page.getByRole('alert')
  await expect(experienceSummary).toBeFocused()
  await experienceSummary.getByRole('link', { name: 'Upload a PDF CV under 5 MB.' }).click()
  await expect(page.locator('#document')).toBeFocused()
  await experienceSummary
    .getByRole('link', { name: 'Review the privacy acknowledgement before continuing.' })
    .click()
  const consent = page.getByLabel(/I understand this frontend/)
  await expect(consent).toBeFocused()
  await expect(consent).toHaveAttribute('aria-describedby', 'consentAcknowledged-error')
  await expect(consent).toHaveAttribute('aria-invalid', 'true')
})

test('status lookup errors stay generic, associated, focused, and preserve the reference', async ({
  page,
}) => {
  await page.goto('/application/status')
  await waitForNuxtHydration(page)
  await page.getByLabel('Application reference').fill('AF-FICTIONAL')
  await page.getByLabel('Private status secret').fill('incorrect-secret')
  await expect(page.getByLabel('Application reference')).toHaveValue('AF-FICTIONAL')
  await expect(page.getByLabel('Private status secret')).toHaveValue('incorrect-secret')
  await page.getByRole('button', { name: 'Check status' }).click()

  const error = page.locator('#status-form-error')
  await expect(error).toBeFocused()
  await expect(error).toContainText('We could not verify those status details')
  await expect(page.locator('#status-lookup-form')).toHaveAttribute(
    'aria-describedby',
    'status-form-error',
  )
  await expect(page.getByLabel('Application reference')).toHaveValue('AF-FICTIONAL')
})

test('save failure preserves answers, announces the problem, and permits retry', async ({
  page,
}) => {
  await page.goto('/apply/frontend-developer/details')
  await waitForNuxtHydration(page)
  await fillCandidateDetails(page)
  await page.evaluate(() => {
    if (!window.__applyflowFixtureControl) throw new Error('Fixture control unavailable')
    window.__applyflowFixtureControl.failNextSave()
  })

  await page.getByRole('button', { name: 'Continue to experience' }).click()

  const failure = page.getByRole('alert', { name: 'This step was not saved' })
  await expect(failure).toBeFocused()
  await expect(page.getByLabel('Full name')).toHaveValue('Avery Example')
  await expect(page.getByLabel('Email address')).toHaveValue('avery.candidate@example.test')
  await page.getByRole('button', { name: 'Try saving again' }).click()
  await expect(page).toHaveURL(/\/apply\/frontend-developer\/experience$/)
})

test('rejected upload keeps unrelated experience values and a valid PDF can follow', async ({
  page,
}) => {
  await page.goto('/apply/frontend-developer/experience')
  await waitForNuxtHydration(page)
  await page.getByLabel('Relevant skills').fill('Vue, accessibility')
  await page.getByLabel('Short message').fill('Fictional context that must remain visible.')
  await page.locator('#cv-upload').setInputFiles({
    buffer: Buffer.from('fictional text fixture'),
    mimeType: 'text/plain',
    name: 'not-a-cv.txt',
  })

  await expect(page.getByText('Choose a PDF file.')).toBeVisible()
  await expect(page.getByLabel('Relevant skills')).toHaveValue('Vue, accessibility')
  await expect(page.getByLabel('Short message')).toHaveValue(
    'Fictional context that must remain visible.',
  )

  await page.locator('#cv-upload').setInputFiles('tests/fixtures/avery-example-cv.pdf')
  await expect(page.getByText('avery-example-cv.pdf')).toBeVisible()
})

test('rapid repeated submission activates the fixture service once', async ({ page }) => {
  await reachReview(page)
  await page.evaluate(() => window.__applyflowFixtureControl?.reset())
  const submit = page.getByRole('button', { name: 'Submit simulated application' })

  await submit.evaluate((button: HTMLButtonElement) => {
    button.click()
    button.click()
  })

  await expect(page).toHaveURL(/\/application\/submitted$/)
  const calls = await page.evaluate(
    () => window.__applyflowFixtureControl?.getSubmitCallCount() ?? -1,
  )
  expect(calls).toBe(1)
})

test('mobile vacancy order, footer targets, and 320px reflow follow the semantic order', async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 800 })
  await page.goto('/vacancies/frontend-developer')
  await waitForNuxtHydration(page)

  const title = page.getByRole('heading', { level: 1, name: 'Frontend Developer' })
  const apply = page.getByRole('complementary', { name: 'Apply for this vacancy' })
  const essentials = page.getByRole('heading', { name: 'What is essential' })
  const responsibilities = page.getByRole('heading', { name: 'What you will work on' })
  const positions = await Promise.all(
    [title, apply, essentials, responsibilities].map(
      async (locator) => (await locator.boundingBox())?.y,
    ),
  )
  expect(positions.every((position) => typeof position === 'number')).toBe(true)
  expect(positions[0]).toBeLessThan(positions[1] ?? 0)
  expect(positions[1]).toBeLessThan(positions[2] ?? 0)
  expect(positions[2]).toBeLessThan(positions[3] ?? 0)
  await expect
    .poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth))
    .toBe(true)

  for (const name of ['Privacy', 'Accessibility']) {
    const box = await page.getByRole('link', { name }).boundingBox()
    expect(box?.height).toBeGreaterThanOrEqual(44)
  }
})

test('public product copy describes current behavior without project-pitch framing', async ({
  page,
}) => {
  await page.goto('/')
  await waitForNuxtHydration(page)
  await expect(page.locator('body')).not.toContainText(
    /portfolio project|frontend portfolio build/i,
  )
  await expect(page.getByRole('contentinfo')).toContainText(
    'ApplyFlow currently uses fixture data and simulated services.',
  )
  await page.getByRole('link', { name: 'Product notes' }).first().click()
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(
    'Building a calmer job application flow',
  )
  await expect(page.locator('body')).not.toContainText(/portfolio case study|demonstrates/i)
})

test('critical public navigation and application start work by keyboard', async ({ page }) => {
  await page.goto('/vacancies/frontend-developer')
  await waitForNuxtHydration(page)
  await page.keyboard.press('Tab')
  await expect(page.getByRole('link', { name: 'Skip to main content' })).toBeFocused()
  await page.getByRole('link', { name: 'Start application' }).focus()
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/\/apply\/frontend-developer$/)
})
