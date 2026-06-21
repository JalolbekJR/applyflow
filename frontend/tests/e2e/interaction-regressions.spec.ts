import { expect, test, type Locator, type Page } from '@playwright/test'

interface InteractionStyle {
  backgroundColor: string
  borderColor: string
  boxShadow: string
  color: string
  opacity: string
  textDecorationThickness: string
  transform: string
}

const requiredViewports = [
  { width: 320, height: 800 },
  { width: 390, height: 844 },
  { width: 768, height: 1024 },
  { width: 1024, height: 900 },
  { width: 1440, height: 1100 },
]

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

const open = async (page: Page, path: string) => {
  await page.goto(path)
  await waitForNuxtHydration(page)
}

const navigateInApp = (page: Page, path: string) =>
  page.evaluate(async (destination) => {
    const root = document.querySelector('#__nuxt') as HTMLElement & {
      __vue_app__?: {
        config: { globalProperties: { $router: { push: (path: string) => Promise<void> } } }
      }
    }
    await root.__vue_app__?.config.globalProperties.$router.push(destination)
  }, path)

const interactionStyle = (locator: Locator) =>
  locator.evaluate((element): InteractionStyle => {
    const style = getComputedStyle(element)
    return {
      backgroundColor: style.backgroundColor,
      borderColor: style.borderColor,
      boxShadow: style.boxShadow,
      color: style.color,
      opacity: style.opacity,
      textDecorationThickness: style.textDecorationThickness,
      transform: style.transform,
    }
  })

const expectStyleChange = async (locator: Locator, before: InteractionStyle) => {
  await expect
    .poll(async () => JSON.stringify(await interactionStyle(locator)))
    .not.toBe(JSON.stringify(before))
}

const expectHoverChange = async (locator: Locator) => {
  const before = await interactionStyle(locator)
  await locator.hover()
  await expectStyleChange(locator, before)
}

const expectPressedChange = async (page: Page, locator: Locator) => {
  await locator.hover()
  const before = await interactionStyle(locator)
  const bounds = await locator.boundingBox()
  expect(bounds).not.toBeNull()
  if (!bounds) return

  await page.mouse.move(bounds.x + bounds.width / 2, bounds.y + bounds.height / 2)
  await page.mouse.down()
  try {
    await expectStyleChange(locator, before)
    const active = await interactionStyle(locator)
    expect(active.color).not.toBe(active.backgroundColor)
    return active
  } finally {
    await page.mouse.move(0, 0)
    await page.mouse.up()
  }
}

const waitForSettledLayout = (page: Page) =>
  page.evaluate(
    () =>
      new Promise<void>((resolve) => {
        requestAnimationFrame(() => requestAnimationFrame(() => resolve()))
      }),
  )

const expectFocusedRegionVisible = async (page: Page, region: Locator, firstLink?: Locator) => {
  await expect(region).toBeFocused()
  await waitForSettledLayout(page)
  const viewport = page.viewportSize()
  const regionBounds = await region.boundingBox()
  const linkBounds = firstLink ? await firstLink.boundingBox() : null
  expect(viewport).not.toBeNull()
  expect(regionBounds).not.toBeNull()
  if (!viewport || !regionBounds) return

  expect(regionBounds.y).toBeGreaterThanOrEqual(8)
  expect(regionBounds.y + regionBounds.height).toBeLessThanOrEqual(viewport.height - 8)
  if (firstLink) {
    expect(linkBounds).not.toBeNull()
    expect(linkBounds?.y).toBeGreaterThanOrEqual(8)
    expect((linkBounds?.y ?? 0) + (linkBounds?.height ?? 0)).toBeLessThanOrEqual(
      viewport.height - 8,
    )
  }
  await expect
    .poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth))
    .toBe(true)
}

const expectKeyboardFocus = async (page: Page, locator: Locator) => {
  await page.keyboard.press('Tab')
  await locator.focus()
  await expect(locator).toBeFocused()
  await expect
    .poll(() =>
      locator.evaluate((element) => {
        const style = getComputedStyle(element)
        return style.outlineStyle !== 'none' && Number.parseFloat(style.outlineWidth) >= 2
      }),
    )
    .toBe(true)
}

test('validation feedback remains visible after focus at required viewports', async ({
  page,
}, testInfo) => {
  test.setTimeout(90_000)
  const viewports =
    testInfo.project.name === 'chromium' ? requiredViewports : [{ width: 390, height: 844 }]

  for (const viewport of viewports) {
    await page.setViewportSize(viewport)
    await open(page, '/apply/frontend-developer/details')
    await page.getByRole('button', { name: 'Continue to experience' }).click()

    const summary = page.getByRole('alert')
    await expectFocusedRegionVisible(page, summary, summary.getByRole('link').first())
  }

  if (testInfo.project.name === 'mobile-chromium') {
    await open(page, '/apply/frontend-developer/experience')
    await page.getByRole('button', { name: 'Continue to review' }).click()
    const experienceSummary = page.getByRole('alert')
    await expectFocusedRegionVisible(
      page,
      experienceSummary,
      experienceSummary.getByRole('link').first(),
    )

    await open(page, '/application/status')
    await page.getByLabel('Application reference').fill('AF-FICTIONAL')
    await page.getByLabel('Private status secret').fill('incorrect-secret')
    await page.getByRole('button', { name: 'Check status' }).click()
    await expectFocusedRegionVisible(page, page.locator('#status-form-error'))
  }
})

test('pointer interaction states are distinct and keyboard focus remains visible', async ({
  page,
}, testInfo) => {
  if (testInfo.project.name === 'chromium') {
    await open(page, '/vacancies/frontend-developer')
    const primary = page.getByRole('link', { name: 'Start application' })
    const navigation = page
      .getByRole('navigation', { name: 'Primary navigation' })
      .getByRole('link', { name: 'Vacancies' })
    await expectHoverChange(primary)
    await expectPressedChange(page, primary)
    await expectHoverChange(navigation)
    await expectPressedChange(page, navigation)
    await expectKeyboardFocus(page, navigation)

    await open(page, '/vacancies')
    const vacancyTitle = page.getByRole('link', { name: 'Frontend Developer' })
    const vacancyAction = page.getByRole('link', { name: 'View role' }).first()
    await expectHoverChange(vacancyTitle)
    await expectPressedChange(page, vacancyTitle)
    await expectHoverChange(vacancyAction)
    await expectPressedChange(page, vacancyAction)
    await expectKeyboardFocus(page, vacancyAction)

    await open(page, '/apply/frontend-developer/review')
    const edit = page.getByRole('region', { name: 'Candidate details' }).getByRole('link', {
      name: 'Edit',
    })
    await expectHoverChange(edit)
    await expectPressedChange(page, edit)
    await expectKeyboardFocus(page, edit)

    await open(page, '/apply/frontend-developer')
    await navigateInApp(page, '/apply/backend-developer')
    const textButton = page.getByRole('button', { name: 'Abandon existing draft' })
    await expectHoverChange(textButton)
    await expectPressedChange(page, textButton)
    await expectKeyboardFocus(page, textButton)

    await open(page, '/application/submitted?preview=success')
    const copy = page.getByRole('button', { name: 'Copy both' })
    await expectHoverChange(copy)
    await expectPressedChange(page, copy)

    await open(page, '/apply/frontend-developer/details')
    await expectKeyboardFocus(page, page.getByLabel('Full name'))
    await page.getByRole('button', { name: 'Continue to experience' }).click()
    const summary = page.getByRole('alert')
    await expectKeyboardFocus(page, summary.getByRole('link').first())
    await expectKeyboardFocus(page, page.locator('#preferredContactMethod'))

    await open(page, '/apply/frontend-developer/experience')
    await page.getByRole('button', { name: 'Continue to review' }).click()
    await expectKeyboardFocus(page, page.getByLabel(/I understand this frontend/))
    return
  }

  await open(page, '/vacancies/frontend-developer')
  await expectPressedChange(page, page.getByRole('link', { name: 'Start application' }))

  await open(page, '/application/submitted?preview=success')
  const copy = page.getByRole('button', { name: 'Copy both' })
  const defaultStyle = await interactionStyle(copy)
  const defaultBounds = await copy.boundingBox()
  await copy.tap()
  await expect
    .poll(async () => JSON.stringify(await interactionStyle(copy)))
    .toBe(JSON.stringify(defaultStyle))
  expect(await copy.boundingBox()).toEqual(defaultBounds)

  await expectPressedChange(page, copy)
})

test('Review actions provide practical touch targets without overflow', async ({
  page,
}, testInfo) => {
  await page.setViewportSize(
    testInfo.project.name === 'mobile-chromium'
      ? { width: 390, height: 844 }
      : { width: 1440, height: 1000 },
  )
  await open(page, '/apply/frontend-developer/review')

  const reviewActions = page.locator('.review-section__heading a')
  await expect(reviewActions).toHaveCount(3)
  for (const action of await reviewActions.all()) {
    const bounds = await action.boundingBox()
    expect(bounds?.width).toBeGreaterThanOrEqual(44)
    expect(bounds?.height).toBeGreaterThanOrEqual(44)
  }
  await expect
    .poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth))
    .toBe(true)
})
