import { apiVacancyService } from '~/api/vacancies'

interface VacancyPageOptions {
  activeOnly?: boolean
}

export const useVacancyPage = async (options: VacancyPageOptions = {}) => {
  const route = useRoute()
  const slug = computed(() => String(route.params.slug ?? ''))
  const keyPrefix = options.activeOnly ? 'application-vacancy' : 'vacancy'
  const { data: vacancy } = await useAsyncData(
    () => `${keyPrefix}-${slug.value}`,
    () =>
      options.activeOnly
        ? apiVacancyService.getActiveBySlug(slug.value)
        : apiVacancyService.getBySlug(slug.value),
    { watch: [slug] },
  )
  return { vacancy, slug }
}
