import type { ApiVacancy, Vacancy } from '~/types/domain'
import { apiRequest } from './client'
import { ApplyFlowApiError } from './errors'
import { assertApiVacancy, assertApiVacancyList } from './runtime-guards'

const formatWorkFormat = (value: string): Vacancy['workFormat'] => {
  if (value === 'remote_friendly') return 'Remote-friendly'
  if (value === 'on_site') return 'On-site'
  return 'Hybrid'
}

const formatEmploymentType = (value: string): Vacancy['employmentType'] => {
  if (value === 'full_time') return 'Full-time'
  return 'Full-time'
}

export const vacancyFromApi = (vacancy: ApiVacancy): Vacancy => ({
  id: vacancy.slug,
  slug: vacancy.slug,
  title: vacancy.title,
  discipline: vacancy.title.toLowerCase().includes('designer') ? 'Product design' : 'Engineering',
  location: vacancy.location,
  workFormat: formatWorkFormat(vacancy.work_format),
  employmentType: formatEmploymentType(vacancy.employment_type),
  summary: vacancy.summary,
  responsibilities: vacancy.responsibilities,
  essentialRequirements: vacancy.requirements,
  niceToHave: vacancy.benefits,
  status: vacancy.status === 'published' ? 'active' : 'closed',
})

export const apiVacancyService = {
  async list(): Promise<Vacancy[]> {
    const response = await apiRequest('/api/v1/vacancies/', { guard: assertApiVacancyList })
    return response.data.map(vacancyFromApi)
  },
  async getBySlug(slug: string): Promise<Vacancy | null> {
    try {
      const response = await apiRequest(`/api/v1/vacancies/${encodeURIComponent(slug)}/`, {
        guard: assertApiVacancy,
      })
      return vacancyFromApi(response.data)
    } catch (error) {
      if (error instanceof ApplyFlowApiError && error.status === 404) return null
      throw error
    }
  },
  async getActiveBySlug(slug: string): Promise<Vacancy | null> {
    const vacancy = await this.getBySlug(slug)
    return vacancy?.status === 'active' ? vacancy : null
  },
}
