<script setup lang="ts">
defineProps<{
  title: string
  message: string
}>()
</script>

<template>
  <section class="empty-state">
    <p class="eyebrow">Nothing to show</p>
    <h2>{{ title }}</h2>
    <p>{{ message }}</p>
    <slot />
  </section>
</template>
