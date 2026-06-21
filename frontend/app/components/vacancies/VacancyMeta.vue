<script setup lang="ts">
import type { Vacancy } from '~/types/domain'

defineProps<{
  vacancy: Vacancy
}>()
</script>

<template>
  <ul class="vacancy-meta" aria-label="Vacancy details">
    <li>{{ vacancy.location }}</li>
    <li>{{ vacancy.workFormat }}</li>
    <li>{{ vacancy.employmentType }}</li>
  </ul>
</template>
