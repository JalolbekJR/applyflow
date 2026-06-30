<script setup lang="ts">
import { useBrand } from '~/branding/useBrand'

const brand = useBrand()

useSeoMeta({ title: `Application confirmation - ${brand.pageTitleSuffix}` })
</script>

<template>
  <div class="page-wrap confirmation-page">
    <header class="page-heading">
      <p class="eyebrow">Confirmation unavailable</p>
      <h1 tabindex="-1">Final submission is not available yet</h1>
      <p>
        Phase 3 saves drafts and private CV metadata only. Application references, confirmation
        pages, and status secrets will return when Phase 4 submission is implemented.
      </p>
    </header>
    <div class="application-actions confirmation-actions">
      <NuxtLink class="button" to="/vacancies">View vacancies</NuxtLink>
      <NuxtLink class="button button--secondary" to="/">Return home</NuxtLink>
    </div>
  </div>
</template>
