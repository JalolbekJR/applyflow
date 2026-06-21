<script setup lang="ts">
import type { SaveState, Vacancy } from '~/types/domain'

defineProps<{
  vacancy: Vacancy
  currentStep: 1 | 2 | 3 | 4
  title: string
  intro: string
  saveState?: SaveState
}>()
</script>

<template>
  <div class="application-page page-wrap">
    <ApplicationStepProgress :current="currentStep" />
    <div class="application-layout">
      <section class="application-main">
        <header class="application-heading">
          <p class="eyebrow">Application / {{ vacancy.title }}</p>
          <h1 tabindex="-1">{{ title }}</h1>
          <p>{{ intro }}</p>
        </header>
        <slot />
      </section>
      <aside class="application-context" aria-label="Selected vacancy">
        <p class="eyebrow">Selected vacancy</p>
        <h2>{{ vacancy.title }}</h2>
        <VacanciesVacancyMeta :vacancy="vacancy" />
        <p>{{ vacancy.summary }}</p>
        <ApplicationSaveStatus v-if="saveState" :state="saveState" />
      </aside>
    </div>
  </div>
</template>
