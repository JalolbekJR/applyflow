<script setup lang="ts">
import type { SaveState } from '~/types/domain'

defineProps<{
  state: SaveState
}>()
</script>

<template>
  <p class="save-status" aria-live="polite" aria-atomic="true">
    <span v-if="state === 'saving'">Saving this step...</span>
    <span v-else-if="state === 'saved'">Saved for this browser session.</span>
    <span v-else-if="state === 'error'">Not saved. Your answers are still visible.</span>
    <span v-else>Changes are kept in this browser tab until you continue.</span>
  </p>
</template>
