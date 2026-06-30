<script setup lang="ts">
import { useTemplateRef } from 'vue'
import { focusAndReveal } from '~/utils/focus'

const feedback = useTemplateRef<HTMLElement>('feedback')

defineExpose({
  focus: () => focusAndReveal(feedback.value),
})
</script>

<template>
  <section
    ref="feedback"
    class="server-error save-failure"
    tabindex="-1"
    role="alert"
    aria-labelledby="save-failure-title"
  >
    <h2 id="save-failure-title">This step was not saved</h2>
    <p>Your answers are still visible. Check the message, then try saving again.</p>
  </section>
</template>
