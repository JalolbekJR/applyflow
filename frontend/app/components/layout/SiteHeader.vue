<script setup lang="ts">
import { useBrand } from '~/branding/useBrand'

const brand = useBrand()
</script>

<template>
  <header class="site-header">
    <div class="site-header__inner">
      <NuxtLink class="wordmark" to="/" :aria-label="`${brand.logoAlt} home`">
        <span>{{ brand.logoText }}</span>
        <span class="wordmark__context">Careers</span>
      </NuxtLink>
      <nav aria-label="Primary navigation">
        <ul class="site-nav">
          <li><NuxtLink to="/vacancies">Vacancies</NuxtLink></li>
          <li v-if="brand.experience.statusLookup">
            <NuxtLink to="/application/status">Check status</NuxtLink>
          </li>
          <li><NuxtLink to="/case-study">Product notes</NuxtLink></li>
        </ul>
      </nav>
    </div>
  </header>
</template>
