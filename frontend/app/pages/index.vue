<script setup lang="ts">
import { apiVacancyService } from '~/api/vacancies'
import { useBrand } from '~/branding/useBrand'

const brand = useBrand()
useSeoMeta({
  title: `ApplyFlow - ${brand.pageTitleSuffix} careers`,
  description: 'Review focused product roles and apply through a clear four-step process.',
})

const { data: vacancies } = await useAsyncData('home-vacancies', () => apiVacancyService.list())
</script>

<template>
  <div class="home-page">
    <section class="home-hero page-wrap" aria-labelledby="home-title">
      <div>
        <p class="eyebrow">{{ brand.publicCopy.homeEyebrow }}</p>
        <h1 id="home-title" tabindex="-1">{{ brand.publicCopy.homeTitle }}</h1>
      </div>
      <div class="home-hero__support">
        <p>{{ brand.publicCopy.homeIntro }}</p>
        <NuxtLink class="button" to="/vacancies">View all vacancies</NuxtLink>
      </div>
    </section>

    <section class="page-wrap home-vacancies" aria-labelledby="featured-roles">
      <header class="section-heading">
        <div>
          <p class="eyebrow">Current opportunities</p>
          <h2 id="featured-roles">Three roles, one respectful application process</h2>
        </div>
        <NuxtLink to="/vacancies">Compare all roles</NuxtLink>
      </header>
      <div class="vacancy-list">
        <VacanciesVacancyRow
          v-for="(vacancy, index) in vacancies"
          :key="vacancy.id"
          :vacancy="vacancy"
          :index="index + 1"
        />
      </div>
    </section>

    <section class="page-wrap home-principle" aria-labelledby="how-it-works">
      <p class="eyebrow">Before you apply</p>
      <h2 id="how-it-works">A short path with visible progress</h2>
      <ol>
        <li><strong>Position</strong><span>Confirm the role and what you will need.</span></li>
        <li>
          <strong>Candidate details</strong><span>Add only the contact information needed.</span>
        </li>
        <li><strong>Experience</strong><span>Share one PDF CV and relevant skills.</span></li>
        <li>
          <strong>Review</strong><span>Check everything before the Phase 4 submission step.</span>
        </li>
      </ol>
      <p class="honesty-note">
        The current frontend uses real draft APIs for implemented Phase 3 behaviour. Final
        submission and status lookup remain future work.
        <NuxtLink to="/case-study">Read the product notes</NuxtLink>.
      </p>
    </section>
  </div>
</template>
