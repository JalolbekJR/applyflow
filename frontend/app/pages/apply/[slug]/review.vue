<script setup lang="ts">
import { formatFileSize, validateCandidateDetails, validateExperience } from '~/utils/validation'

const { vacancy } = await useVacancyPage({ activeOnly: true })
const { draft, enterApplicationStep, saveState } = useApplicationDraft()
if (vacancy.value) await enterApplicationStep(vacancy.value.slug)

const isComplete = computed(
  () =>
    Object.keys(validateCandidateDetails(draft.value.candidate)).length === 0 &&
    Object.keys(validateExperience(draft.value.experience, draft.value.document)).length === 0,
)

useSeoMeta({
  title: () =>
    vacancy.value ? `Apply for ${vacancy.value.title} - Review` : 'Application unavailable',
})

const deferredSubmissionMessage =
  'Final submission is not available in this Phase 3 build. Your draft is saved for review, and submission will be implemented in Phase 4.'
</script>

<template>
  <ApplicationShell
    v-if="vacancy"
    :vacancy="vacancy"
    :current-step="4"
    title="Review your application"
    intro="Check every saved section. Edit links return here after saving."
    :save-state="saveState"
  >
    <section v-if="!isComplete" class="incomplete-notice" role="alert">
      <h2>Complete the earlier steps before submitting</h2>
      <p>
        Candidate details, experience, consent, and one PDF are required before the future Phase 4
        submission step.
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
        Only safe document metadata is shown. There is no download or preview action.
      </p>
    </section>

    <section class="context-note" aria-labelledby="submission-note-title">
      <h2 id="submission-note-title">Before submitting</h2>
      <p>
        Final submission, application references, and private status lookup are Phase 4 features.
        This review screen is for checking the persisted draft only.
      </p>
    </section>

    <p id="deferred-submit-note" class="server-error" role="status">
      {{ deferredSubmissionMessage }}
    </p>
    <div class="application-actions">
      <NuxtLink class="button button--secondary" :to="`/apply/${vacancy.slug}/experience`"
        >Back</NuxtLink
      >
      <button class="button" type="button" disabled aria-describedby="deferred-submit-note">
        Submit application unavailable
      </button>
    </div>
  </ApplicationShell>
  <ApplicationUnavailable v-else />
</template>
