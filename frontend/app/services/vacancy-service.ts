import { vacancyFixtures } from '~/data/vacancies'
import type { Vacancy } from '~/types/domain'

export interface VacancyService {
  list(): Promise<Vacancy[]>
  getBySlug(slug: string): Promise<Vacancy | null>
  getActiveBySlug(slug: string): Promise<Vacancy | null>
}

const cloneVacancy = (vacancy: Vacancy): Vacancy => structuredClone(vacancy)

export const fixtureVacancyService: VacancyService = {
  async list() {
    return vacancyFixtures.filter((vacancy) => vacancy.status === 'active').map(cloneVacancy)
  },
  async getBySlug(slug) {
    const vacancy = vacancyFixtures.find((item) => item.slug === slug)
    return vacancy ? cloneVacancy(vacancy) : null
  },
  async getActiveBySlug(slug) {
    const vacancy = vacancyFixtures.find((item) => item.slug === slug && item.status === 'active')
    return vacancy ? cloneVacancy(vacancy) : null
  },
}
