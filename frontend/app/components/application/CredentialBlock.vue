<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  label: string
  value: string
}>()

const copied = ref(false)
const copyError = ref(false)

const copy = async () => {
  copied.value = false
  copyError.value = false
  try {
    await navigator.clipboard.writeText(props.value)
    copied.value = true
    window.setTimeout(() => (copied.value = false), 1800)
  } catch {
    copyError.value = true
  }
}
</script>

<template>
  <div class="credential-block">
    <div>
      <span>{{ label }}</span>
      <strong>{{ value }}</strong>
    </div>
    <button class="button button--secondary" type="button" @click="copy">Copy</button>
    <span class="copy-status" :class="{ 'copy-status--error': copyError }" aria-live="polite">
      {{
        copyError
          ? 'Copy failed. Select the value above and copy it manually.'
          : copied
            ? 'Copied'
            : ''
      }}
    </span>
  </div>
</template>
