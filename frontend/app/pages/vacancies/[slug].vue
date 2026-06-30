<script setup lang="ts">
import { useBrand } from '~/branding/useBrand'

const route = useRoute()
const { vacancy } = await useVacancyPage()
const brand = useBrand()
const isUnavailable = computed(
  () =>
    !vacancy.value ||
    vacancy.value.status === 'closed' ||
    (import.meta.dev && route.query.preview === 'closed'),
)

useSeoMeta({
  title: () =>
    vacancy.value ? `${vacancy.value.title} - ${brand.pageTitleSuffix}` : 'Vacancy unavailable',
  description: () => vacancy.value?.summary ?? 'This vacancy is not available.',
})
</script>

<template>
  <div v-if="vacancy" class="page-wrap vacancy-detail">
    <NuxtLink class="back-link" to="/vacancies">&lt;- All vacancies</NuxtLink>
    <article class="vacancy-detail__layout">
      <header class="page-heading vacancy-detail__heading">
        <p class="eyebrow">{{ vacancy.discipline }}</p>
        <h1 tabindex="-1">{{ vacancy.title }}</h1>
        <VacanciesVacancyMeta :vacancy="vacancy" />
        <p>{{ vacancy.summary }}</p>
      </header>

      <aside class="vacancy-apply" aria-label="Apply for this vacancy">
        <template v-if="isUnavailable">
          <p class="eyebrow">Applications closed</p>
          <h2>This role is not accepting applications</h2>
          <p>You can still review the vacancy, then compare the roles that remain open.</p>
          <NuxtLink class="button button--secondary" to="/vacancies">View open vacancies</NuxtLink>
        </template>
        <template v-else>
          <p class="eyebrow">Four steps</p>
          <h2>Ready to apply?</h2>
          <p>You will need contact details, relevant skills, and one PDF CV under 5 MB.</p>
          <NuxtLink class="button" :to="`/apply/${vacancy.slug}`">Start application</NuxtLink>
          <p class="supporting-note">
            Draft saving and CV upload use the implemented secure draft APIs. Final submission is
            planned for Phase 4.
          </p>
        </template>
      </aside>

      <div class="vacancy-detail__sections">
        <section aria-labelledby="essential-title">
          <h2 id="essential-title">What is essential</h2>
          <ul class="detail-list">
            <li v-for="item in vacancy.essentialRequirements" :key="item">{{ item }}</li>
          </ul>
        </section>

        <section aria-labelledby="responsibilities-title">
          <h2 id="responsibilities-title">What you will work on</h2>
          <ul class="detail-list">
            <li v-for="item in vacancy.responsibilities" :key="item">{{ item }}</li>
          </ul>
        </section>

        <section aria-labelledby="helpful-title">
          <h2 id="helpful-title">Helpful, not required</h2>
          <ul class="detail-list">
            <li v-for="item in vacancy.niceToHave" :key="item">{{ item }}</li>
          </ul>
        </section>
      </div>
    </article>
  </div>

  <div v-else class="page-wrap">
    <header class="page-heading">
      <p class="eyebrow">Vacancy unavailable</p>
      <h1 tabindex="-1">We could not find that role</h1>
      <p>The vacancy may have been removed or the link may be incorrect.</p>
    </header>
    <NuxtLink class="button" to="/vacancies">View open vacancies</NuxtLink>
  </div>
</template>
