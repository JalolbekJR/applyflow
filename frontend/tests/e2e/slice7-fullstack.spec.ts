import { expect, test, type Page } from '@playwright/test'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const fixturePath = resolve(process.cwd(), 'tests/fixtures/avery-example-cv.pdf')

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

const replacementPdf = () => ({
  name: 'avery-replacement-cv.pdf',
  mimeType: 'application/pdf',
  buffer: readFileSync(fixturePath),
})

test('real stack candidate draft, CV, conflict, and abandonment flow', async ({ page }) => {
  await page.goto('/vacancies')
  await waitForNuxtHydration(page)
  await page.getByRole('link', { name: 'Frontend Developer' }).click()
  await page.getByRole('link', { name: 'Start application' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Before you begin' })).toBeVisible()

  await page.getByRole('link', { name: 'Continue to candidate details' }).click()
  await page.getByLabel('Full name').fill('Avery Example')
  await page.getByLabel('Email address').fill('avery.candidate@example.test')
  await page.getByLabel('Portfolio, GitHub, or LinkedIn').fill('https://example.test/avery')
  await page.getByLabel('Email', { exact: true }).check()
  await page.getByRole('button', { name: 'Continue to experience' }).click()
  await expect(page).toHaveURL(/\/apply\/frontend-developer\/experience$/)

  await page.getByLabel('Organization').fill('Fictional Systems')
  await page.getByLabel('Role title').fill('Interface Engineer')
  await page.getByLabel('Start month').fill('2024-01')
  await page.getByLabel('This is my current role').check()
  await page.getByRole('button', { name: 'Add role' }).click()
  await expect(page.getByText('Fictional Systems')).toBeVisible()

  await page.locator('#cv-upload').setInputFiles(fixturePath)
  await expect(page.getByText('avery-example-cv.pdf')).toBeVisible()

  await page.locator('#cv-upload').setInputFiles(replacementPdf())
  await expect(page.getByText('avery-replacement-cv.pdf')).toBeVisible()

  await page.getByLabel('CV upload field').getByRole('button', { name: 'Remove' }).click()
  await expect(page.getByText('avery-replacement-cv.pdf')).toHaveCount(0)
  await page.locator('#cv-upload').setInputFiles(fixturePath)
  await expect(page.getByText('avery-example-cv.pdf')).toBeVisible()

  await page.getByLabel('Experience level').selectOption('mid-level')
  await page.getByLabel('Relevant skills').fill('Vue 3, TypeScript, accessibility')
  await page.getByLabel('Short message').fill('Fictional full-stack smoke context.')
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

  await page.reload()
  await waitForNuxtHydration(page)
  await expect(
    page.getByRole('heading', { level: 1, name: 'Review your application' }),
  ).toBeVisible()
  await expect(page.getByRole('region', { name: 'Candidate details' })).toContainText(
    'Avery Example',
  )

  await page.goto('/apply/backend-developer')
  await waitForNuxtHydration(page)
  await expect(
    page.getByRole('heading', { name: 'You already started another application' }),
  ).toBeVisible()
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
})
