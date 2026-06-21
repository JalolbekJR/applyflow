import { describe, expect, it } from 'vitest'
import { fixtureVacancyService } from '~/services/vacancy-service'

describe('fixtureVacancyService', () => {
  it('returns the three active documented vacancies', async () => {
    const vacancies = await fixtureVacancyService.list()
    expect(vacancies.map((vacancy) => vacancy.title)).toEqual([
      'Frontend Developer',
      'Backend Developer',
      'UI/UX Designer',
    ])
  })

  it('returns clones instead of exposing fixture objects', async () => {
    const first = await fixtureVacancyService.getBySlug('frontend-developer')
    expect(first).not.toBeNull()
    if (!first) return
    first.title = 'Changed in test'
    const second = await fixtureVacancyService.getBySlug('frontend-developer')
    expect(second?.title).toBe('Frontend Developer')
  })

  it('returns only active vacancies for application routes', async () => {
    await expect(
      fixtureVacancyService.getActiveBySlug('frontend-developer'),
    ).resolves.toMatchObject({
      slug: 'frontend-developer',
      status: 'active',
    })
    await expect(fixtureVacancyService.getActiveBySlug('not-a-role')).resolves.toBeNull()
  })
})
