<script setup lang="ts">
import { fixtureVacancyService } from '~/services/vacancy-service'

useSeoMeta({
  title: 'Open vacancies - Northline Studio',
  description: 'Compare three fictional engineering and design vacancies at Northline Studio.',
})

const route = useRoute()
const { data: vacancies } = await useAsyncData('vacancies', () => fixtureVacancyService.list())
const visibleVacancies = computed(() =>
  import.meta.dev && route.query.preview === 'empty' ? [] : (vacancies.value ?? []),
)
</script>

<template>
  <div class="page-wrap">
    <header class="page-heading">
      <p class="eyebrow">Northline Studio / Careers</p>
      <h1 tabindex="-1">Open vacancies</h1>
      <p>
        Compare the work, expectations, and practical details before deciding whether to apply.
        Every role uses the same four-step process.
      </p>
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
