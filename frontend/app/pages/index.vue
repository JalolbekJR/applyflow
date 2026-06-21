<script setup lang="ts">
import { fixtureVacancyService } from '~/services/vacancy-service'

useSeoMeta({
  title: 'ApplyFlow - Northline Studio careers',
  description: 'Review focused product roles and apply through a clear four-step process.',
})

const { data: vacancies } = await useAsyncData('home-vacancies', () => fixtureVacancyService.list())
</script>

<template>
  <div class="home-page">
    <section class="home-hero page-wrap" aria-labelledby="home-title">
      <div>
        <p class="eyebrow">Northline Studio / Open roles</p>
        <h1 id="home-title" tabindex="-1">Applying should not feel like filing taxes twice.</h1>
      </div>
      <div class="home-hero__support">
        <p>
          Understand the role, share only what is needed, review your answers, and know what happens
          next.
        </p>
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
          <strong>Review</strong><span>Check everything before the simulated submission.</span>
        </li>
      </ol>
      <p class="honesty-note">
        The current frontend uses fictional vacancies and simulated services. Saving, upload, and
        submission are not connected to a backend.
        <NuxtLink to="/case-study">Read the product notes</NuxtLink>.
      </p>
    </section>
  </div>
</template>
