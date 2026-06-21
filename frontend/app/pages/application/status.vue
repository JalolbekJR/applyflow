<script setup lang="ts">
import { ApiLikeError, fixtureApplicationService } from '~/services/application-service'
import type { StatusLookupResult } from '~/types/domain'
import { focusAndReveal } from '~/utils/focus'

useSeoMeta({ title: 'Check application status - Northline Studio' })

const applicationReference = ref('')
const statusLookupSecret = ref('')
const result = ref<StatusLookupResult | null>(null)
const error = ref('')
const attempts = ref(0)
const isLoading = ref(false)
const isRateLimited = computed(() => attempts.value >= 3)
const formError = useTemplateRef<HTMLElement>('formError')

const reportError = async (message: string) => {
  error.value = message
  await nextTick()
  await focusAndReveal(formError.value)
}

const lookup = async () => {
  result.value = null
  error.value = ''
  if (isRateLimited.value) {
    await reportError(
      'Too many unsuccessful attempts in this simulated status check. Refresh the page before trying again.',
    )
    return
  }
  if (!applicationReference.value.trim() || !statusLookupSecret.value.trim()) {
    await reportError('Enter both the application reference and private status secret.')
    return
  }

  isLoading.value = true
  try {
    result.value = await fixtureApplicationService.lookupStatus({
      applicationReference: applicationReference.value,
      statusLookupSecret: statusLookupSecret.value,
    })
  } catch (caught) {
    attempts.value += 1
    await reportError(
      caught instanceof ApiLikeError ? caught.message : 'Status lookup is unavailable.',
    )
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="page-wrap status-page">
    <header class="page-heading">
      <p class="eyebrow">Private status utility</p>
      <h1 tabindex="-1">Check application status</h1>
      <p>
        Enter both details from the confirmation page. Email is not used as proof of access, and
        results never include internal notes or staff information.
      </p>
    </header>

    <form
      id="status-lookup-form"
      class="status-form"
      novalidate
      :aria-describedby="error ? 'status-form-error' : undefined"
      @submit.prevent="lookup"
    >
      <p
        v-if="error"
        id="status-form-error"
        ref="formError"
        class="server-error"
        tabindex="-1"
        role="alert"
      >
        {{ error }}
      </p>
      <div class="field">
        <label for="applicationReference">Application reference</label>
        <p id="application-reference-hint" class="field-hint">
          Use the reference exactly as shown on the confirmation page.
        </p>
        <input
          id="applicationReference"
          v-model="applicationReference"
          autocomplete="off"
          placeholder="AF-XXXX-XXXX"
          aria-describedby="application-reference-hint"
        />
      </div>
      <div class="field">
        <label for="statusLookupSecret">Private status secret</label>
        <p id="status-secret-hint" class="field-hint">
          Treat this value like a password. It is never placed in the URL.
        </p>
        <input
          id="statusLookupSecret"
          v-model="statusLookupSecret"
          type="password"
          autocomplete="off"
          aria-describedby="status-secret-hint"
        />
      </div>
      <button class="button" type="submit" :disabled="isLoading || isRateLimited">
        {{ isLoading ? 'Checking...' : isRateLimited ? 'Temporarily limited' : 'Check status' }}
      </button>
    </form>

    <section
      v-if="result"
      class="status-panel"
      aria-live="polite"
      aria-labelledby="status-result-title"
    >
      <p class="eyebrow">Application found</p>
      <h2 id="status-result-title">{{ result.status }}</h2>
      <dl class="review-list">
        <dt>Vacancy</dt>
        <dd>{{ result.vacancyTitle }}</dd>
        <dt>Submitted</dt>
        <dd>{{ new Date(result.submittedAt).toLocaleDateString('en-GB') }}</dd>
      </dl>
      <p>{{ result.nextStep }}</p>
    </section>
  </div>
</template>
