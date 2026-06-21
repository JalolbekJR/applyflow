<script setup lang="ts">
import { fixtureApplicationService } from '~/services/application-service'
import { formatFileSize, validateCandidateDetails, validateExperience } from '~/utils/validation'

const { vacancy } = await useVacancyPage({ activeOnly: true })
const { draft, enterApplicationStep, saveState, submission } = useApplicationDraft()
if (vacancy.value) await enterApplicationStep(vacancy.value.slug)
const submitError = ref('')
const isSubmitting = ref(false)

const isComplete = computed(
  () =>
    Object.keys(validateCandidateDetails(draft.value.candidate)).length === 0 &&
    Object.keys(validateExperience(draft.value.experience, draft.value.document)).length === 0,
)

useSeoMeta({
  title: () =>
    vacancy.value ? `Apply for ${vacancy.value.title} - Review` : 'Application unavailable',
})

const submit = async () => {
  if (isSubmitting.value || !vacancy.value || !isComplete.value) return
  if (
    getApplicationDraftOwnership(draft.value.vacancySlug, vacancy.value.slug) !== 'matching-draft'
  ) {
    await enterApplicationStep(vacancy.value.slug)
    return
  }
  isSubmitting.value = true
  submitError.value = ''
  try {
    submission.value = await fixtureApplicationService.submit(draft.value, vacancy.value.title)
    await navigateTo('/application/submitted')
  } catch {
    submitError.value = 'The simulated submission did not finish. Your answers are still available.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <ApplicationShell
    v-if="vacancy"
    :vacancy="vacancy"
    :current-step="4"
    title="Review your application"
    intro="Check every section before the simulated submission. Edit links return here after saving."
    :save-state="saveState"
  >
    <section v-if="!isComplete" class="incomplete-notice" role="alert">
      <h2>Complete the earlier steps before submitting</h2>
      <p>
        Candidate details, experience, consent, and one PDF are required for this simulated
        application.
      </p>
      <NuxtLink :to="`/apply/${vacancy.slug}/details?return=review`"
        >Return to candidate details</NuxtLink
      >
    </section>

    <section class="review-section" aria-labelledby="candidate-review-title">
      <div class="review-section__heading">
        <h2 id="candidate-review-title">Candidate details</h2>
        <NuxtLink class="review-action" :to="`/apply/${vacancy.slug}/details?return=review`"
          >Edit</NuxtLink
        >
      </div>
      <dl class="review-list">
        <dt>Full name</dt>
        <dd>{{ draft.candidate.fullName || 'Not provided' }}</dd>
        <dt>Email</dt>
        <dd>{{ draft.candidate.email || 'Not provided' }}</dd>
        <dt>Phone</dt>
        <dd>{{ draft.candidate.phone || 'Not provided' }}</dd>
        <dt>Profile</dt>
        <dd>{{ draft.candidate.profileUrl || 'Not provided' }}</dd>
        <dt>Preferred contact</dt>
        <dd>{{ draft.candidate.preferredContactMethod || 'Not provided' }}</dd>
      </dl>
    </section>

    <section class="review-section" aria-labelledby="experience-review-title">
      <div class="review-section__heading">
        <h2 id="experience-review-title">Experience</h2>
        <NuxtLink class="review-action" :to="`/apply/${vacancy.slug}/experience?return=review`"
          >Edit</NuxtLink
        >
      </div>
      <dl class="review-list">
        <dt>Experience level</dt>
        <dd>{{ draft.experience.experienceLevel || 'Not provided' }}</dd>
        <dt>Skills</dt>
        <dd>{{ draft.experience.skills.join(', ') || 'Not provided' }}</dd>
        <dt>Message</dt>
        <dd>{{ draft.experience.message || 'Not provided' }}</dd>
        <dt>Consent</dt>
        <dd>{{ draft.experience.consentAcknowledged ? 'Acknowledged' : 'Not acknowledged' }}</dd>
      </dl>
    </section>

    <section class="review-section" aria-labelledby="document-review-title">
      <div class="review-section__heading">
        <h2 id="document-review-title">CV document</h2>
        <NuxtLink class="review-action" :to="`/apply/${vacancy.slug}/experience?return=review`"
          >Replace</NuxtLink
        >
      </div>
      <p v-if="draft.document">
        <strong>{{ draft.document.name }}</strong> - {{ formatFileSize(draft.document.size) }}
      </p>
      <p v-else>Not provided</p>
      <p class="supporting-note">
        Only file metadata is held in memory. This frontend does not upload or store the PDF.
      </p>
    </section>

    <section class="context-note" aria-labelledby="submission-note-title">
      <h2 id="submission-note-title">Before submitting</h2>
      <p>
        The real backend will revalidate every field, enforce duplicate protection, and store the CV
        privately. This button completes only the simulated frontend flow.
      </p>
    </section>

    <p v-if="submitError" class="server-error" role="alert">{{ submitError }}</p>
    <div class="application-actions">
      <NuxtLink class="button button--secondary" :to="`/apply/${vacancy.slug}/experience`"
        >Back</NuxtLink
      >
      <button class="button" type="button" :disabled="!isComplete || isSubmitting" @click="submit">
        {{ isSubmitting ? 'Submitting...' : 'Submit simulated application' }}
      </button>
    </div>
  </ApplicationShell>
  <ApplicationUnavailable v-else />
</template>
