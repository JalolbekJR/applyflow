import { fixtureVacancyService } from '~/services/vacancy-service'

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
        ? fixtureVacancyService.getActiveBySlug(slug.value)
        : fixtureVacancyService.getBySlug(slug.value),
    { watch: [slug] },
  )
  return { vacancy, slug }
}
