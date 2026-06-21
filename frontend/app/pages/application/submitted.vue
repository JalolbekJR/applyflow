<script setup lang="ts">
import { simulatedCredentials } from '~/services/application-service'
import type { ApplicationSubmissionResult } from '~/types/domain'

const route = useRoute()
const { submission } = useApplicationDraft()
const copiedAll = ref(false)
const copyError = ref(false)

const previewResult: ApplicationSubmissionResult = {
  vacancyTitle: 'Frontend Developer',
  applicationReference: simulatedCredentials.applicationReference,
  statusLookupSecret: simulatedCredentials.statusLookupSecret,
  submittedAt: '2026-06-20T09:00:00Z',
}

const result = computed(
  () =>
    submission.value ??
    (import.meta.dev && route.query.preview === 'success' ? previewResult : null),
)

useSeoMeta({ title: 'Application confirmation - Northline Studio' })

const copyBoth = async () => {
  if (!result.value) return
  copiedAll.value = false
  copyError.value = false
  try {
    await navigator.clipboard.writeText(
      `Application reference: ${result.value.applicationReference}\nStatus secret: ${result.value.statusLookupSecret}`,
    )
    copiedAll.value = true
    window.setTimeout(() => (copiedAll.value = false), 1800)
  } catch {
    copyError.value = true
  }
}
</script>

<template>
  <div class="page-wrap confirmation-page">
    <template v-if="result">
      <header class="page-heading">
        <p class="eyebrow">Simulated submission complete</p>
        <h1 tabindex="-1">Keep these status details somewhere private</h1>
        <p>
          The application for {{ result.vacancyTitle }} reached the frontend confirmation state.
          These fictional credentials cannot be recovered after this in-memory session ends.
        </p>
      </header>

      <section class="credential-section" aria-labelledby="credentials-title">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Status access</p>
            <h2 id="credentials-title">Reference and private secret</h2>
          </div>
          <button class="button" type="button" @click="copyBoth">Copy both</button>
        </div>
        <p class="persistent-warning">
          The application reference is not private and cannot authorize status access. Protect the
          separate status secret as you would a password.
        </p>
        <div class="credential-group">
          <ApplicationCredentialBlock
            label="Application reference"
            :value="result.applicationReference"
          />
          <ApplicationCredentialBlock
            label="Private status secret"
            :value="result.statusLookupSecret"
          />
        </div>
        <p class="copy-status" :class="{ 'copy-status--error': copyError }" aria-live="polite">
          {{
            copyError
              ? 'Copy failed. Select the values above and copy them manually.'
              : copiedAll
                ? 'Both details copied'
                : ''
          }}
        </p>
      </section>

      <div class="application-actions confirmation-actions">
        <NuxtLink class="button" to="/application/status">Check application status</NuxtLink>
        <NuxtLink class="button button--secondary" to="/vacancies">Return to vacancies</NuxtLink>
      </div>
    </template>

    <template v-else>
      <header class="page-heading">
        <p class="eyebrow">Confirmation unavailable</p>
        <h1 tabindex="-1">This page does not retain application credentials</h1>
        <p>
          Direct visits and reloads cannot restore the simulated confirmation. In the future, the
          backend will deliver credentials only through a successful no-store submission response.
        </p>
      </header>
      <NuxtLink class="button" to="/vacancies">View vacancies</NuxtLink>
    </template>
  </div>
</template>
