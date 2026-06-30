<script setup lang="ts">
import { apiVacancyService } from '~/api/vacancies'
import { useBrand } from '~/branding/useBrand'

const brand = useBrand()
useSeoMeta({
  title: `Open vacancies - ${brand.pageTitleSuffix}`,
  description: `Compare fictional engineering and design vacancies at ${brand.shortName}.`,
})

const route = useRoute()
const { data: vacancies } = await useAsyncData('vacancies', () => apiVacancyService.list())
const visibleVacancies = computed(() =>
  import.meta.dev && route.query.preview === 'empty' ? [] : (vacancies.value ?? []),
)
</script>

<template>
  <div class="page-wrap">
    <header class="page-heading">
      <p class="eyebrow">{{ brand.shortName }} / Careers</p>
      <h1 tabindex="-1">Open vacancies</h1>
      <p>{{ brand.publicCopy.vacancyListIntro }} Every role uses the same four-step process.</p>
    </header>

    <div v-if="visibleVacancies.length" class="vacancy-list">
      <VacanciesVacancyRow
        v-for="(vacancy, index) in visibleVacancies"
        :key="vacancy.id"
        :vacancy="vacancy"
        :index="index + 1"
      />
    </div>
    <FeedbackEmptyState
      v-else
      title="There are no open vacancies right now"
      message="Northline Studio has not published a role that is accepting applications."
    >
      <NuxtLink class="button button--secondary" to="/">Return home</NuxtLink>
    </FeedbackEmptyState>
  </div>
</template>
