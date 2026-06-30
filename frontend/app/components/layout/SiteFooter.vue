<script setup lang="ts">
import { useBrand } from '~/branding/useBrand'

const brand = useBrand()
</script>

<template>
  <footer class="site-footer">
    <div class="site-footer__inner">
      <p>{{ brand.publicCopy.footerNote }}</p>
      <nav aria-label="Footer navigation">
        <NuxtLink v-for="link in brand.legalLinks" :key="link.href" :to="link.href">
          {{ link.label }}
        </NuxtLink>
        <NuxtLink :to="brand.accessibilityLink.href">{{ brand.accessibilityLink.label }}</NuxtLink>
      </nav>
    </div>
  </footer>
</template>
