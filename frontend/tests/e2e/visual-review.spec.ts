import { test, type Page } from '@playwright/test'

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

const open = async (page: Page, path: string) => {
  await page.goto(path)
  await waitForNuxtHydration(page)
}

const capture = async (page: Page, path: string) => {
  await page.evaluate(() => {
    document.documentElement.style.scrollBehavior = 'auto'
    window.scrollTo(0, 0)
  })
  await page.screenshot({ path, fullPage: true })
}

test('capture corrected audit states at mobile and desktop widths', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium', 'The desktop project captures explicit widths.')
  const screenshotSet = process.env.SCREENSHOT_SET ?? 'corrections'

  for (const viewport of [
    { name: '390', width: 390, height: 844 },
    { name: '1440', width: 1440, height: 1000 },
  ]) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height })

    await open(page, '/vacancies/frontend-developer')
    await capture(page, `tests/screenshots/${screenshotSet}/${viewport.name}/03-vacancy-detail.png`)

    await open(page, '/apply/frontend-developer/details')
    await page.getByRole('button', { name: 'Continue to experience' }).click()
    await page.getByRole('alert').waitFor()
    await capture(
      page,
      `tests/screenshots/${screenshotSet}/states/${viewport.name}/13-details-validation-errors.png`,
    )

    await open(page, '/apply/frontend-developer/experience')
    await page.locator('#cv-upload').setInputFiles({
      buffer: Buffer.from('fictional text fixture'),
      mimeType: 'text/plain',
      name: 'not-a-cv.txt',
    })
    await page.getByText('Choose a PDF file.').waitFor()
    await capture(
      page,
      `tests/screenshots/${screenshotSet}/states/${viewport.name}/17-experience-upload-rejected.png`,
    )

    await open(page, '/application/status')
    await page.getByLabel('Application reference').fill('AF-FICTIONAL')
    await page.getByLabel('Private status secret').fill('incorrect-secret')
    await page.getByRole('button', { name: 'Check status' }).click()
    await page
      .getByText('We could not verify those status details. Check both values and try again.')
      .waitFor()
    await capture(
      page,
      `tests/screenshots/${screenshotSet}/states/${viewport.name}/19-status-invalid.png`,
    )

    await open(page, '/vacancies/not-a-role')
    await capture(
      page,
      `tests/screenshots/${screenshotSet}/states/${viewport.name}/21-vacancy-unavailable.png`,
    )

    await open(page, '/apply/frontend-developer')
    await navigateInApp(page, '/apply/backend-developer')
    await page.getByText('You already started another application').waitFor()
    await capture(
      page,
      `tests/screenshots/${screenshotSet}/states/${viewport.name}/23-active-draft-conflict.png`,
    )

    await open(page, '/apply/frontend-developer/details')
    await page.getByLabel('Full name').fill('Avery Example')
    await page.getByLabel('Email address').fill('avery.candidate@example.test')
    await page.getByLabel('Email', { exact: true }).check()
    await page.evaluate(() => {
      if (!window.__applyflowFixtureControl) throw new Error('Fixture control unavailable')
      window.__applyflowFixtureControl.failNextSave()
    })
    await page.getByRole('button', { name: 'Continue to experience' }).click()
    await page.getByRole('alert', { name: 'This step was not saved' }).waitFor()
    await capture(
      page,
      `tests/screenshots/${screenshotSet}/states/${viewport.name}/24-save-failed-or-offline.png`,
    )

    await open(page, '/apply/not-a-role/details')
    await capture(
      page,
      `tests/screenshots/${screenshotSet}/states/${viewport.name}/25-invalid-application-route.png`,
    )
  }
})

test('capture vacancy detail reflow review widths', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium', 'The desktop project captures explicit widths.')
  const screenshotSet = process.env.SCREENSHOT_SET ?? 'corrections'

  for (const viewport of [
    { name: '320', width: 320, height: 800 },
    { name: '390', width: 390, height: 844 },
    { name: '768', width: 768, height: 1024 },
    { name: '1024', width: 1024, height: 900 },
    { name: '1440', width: 1440, height: 1000 },
  ]) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height })
    await open(page, '/vacancies/frontend-developer')
    await capture(
      page,
      `tests/screenshots/${screenshotSet}/responsive/${viewport.name}/vacancy-detail.png`,
    )
  }
})
