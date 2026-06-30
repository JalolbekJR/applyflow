<script setup lang="ts">
import type { SaveState } from '~/types/domain'

defineProps<{
  state: SaveState
}>()
</script>

<template>
  <p class="save-status" aria-live="polite" aria-atomic="true">
    <span v-if="state === 'saving'">Saving this step...</span>
    <span v-else-if="state === 'dirty' || state === 'waiting'">Unsaved changes are visible.</span>
    <span v-else-if="state === 'saved'">Saved to the protected draft.</span>
    <span v-else-if="state === 'conflict'">The draft changed. Review the refreshed draft.</span>
    <span v-else-if="state === 'offline'">Connection interrupted. Review before retrying.</span>
    <span v-else-if="state === 'error'">Not saved. Your answers are still visible.</span>
    <span v-else>Changes save when you continue.</span>
  </p>
</template>
