<script setup lang="ts">
import type { Vacancy } from '~/types/domain'

defineProps<{
  vacancy: Vacancy
  index: number
}>()
</script>

<template>
  <article class="vacancy-row">
    <div class="vacancy-row__index" aria-hidden="true">{{ String(index).padStart(2, '0') }}</div>
    <div class="vacancy-row__body">
      <p class="eyebrow">{{ vacancy.discipline }}</p>
      <h2>
        <NuxtLink :to="`/vacancies/${vacancy.slug}`">{{ vacancy.title }}</NuxtLink>
      </h2>
      <p class="vacancy-row__summary">{{ vacancy.summary }}</p>
      <VacanciesVacancyMeta :vacancy="vacancy" />
    </div>
    <NuxtLink class="vacancy-row__action" :to="`/vacancies/${vacancy.slug}`">
      <span>View role</span>
      <span aria-hidden="true">-&gt;</span>
    </NuxtLink>
  </article>
</template>
