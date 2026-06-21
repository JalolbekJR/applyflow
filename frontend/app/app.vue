<script setup lang="ts">
const route = useRoute()

if (import.meta.client) {
  watch(
    () => route.path,
    async () => {
      await nextTick()
      document.querySelector<HTMLElement>('main h1')?.focus()
    },
  )
}
</script>

<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
