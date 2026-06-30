<script setup lang="ts">
const { vacancy } = await useVacancyPage({ activeOnly: true })
const { draft, saveState, enterApplicationStep, abandonServerDraft } = useApplicationDraft()
const confirmAbandon = ref(false)
const startState = ref<'loading' | 'ready' | 'conflict' | 'unavailable'>('loading')

const hasConflict = computed(
  () =>
    getApplicationDraftOwnership(draft.value.vacancySlug, vacancy.value?.slug ?? null) ===
    'conflicting-draft',
)

watch(
  vacancy,
  async (verifiedVacancy) => {
    if (!verifiedVacancy) {
      startState.value = 'unavailable'
      return
    }
    const result = await enterApplicationStep(verifiedVacancy.slug)
    startState.value = result === 'conflicting-draft' ? 'conflict' : 'ready'
  },
  { immediate: true },
)

useSeoMeta({
  title: () =>
    vacancy.value ? `Apply for ${vacancy.value.title} - Step 1` : 'Application unavailable',
})

const continueExisting = () => navigateTo(`/apply/${draft.value.vacancySlug}/details`)
const abandonAndStart = async () => {
  if (!vacancy.value) return
  await abandonServerDraft()
  await enterApplicationStep(vacancy.value.slug)
  confirmAbandon.value = false
  startState.value = 'ready'
}
</script>

<template>
  <ApplicationShell
    v-if="vacancy"
    :vacancy="vacancy"
    :current-step="1"
    title="Before you begin"
    intro="Confirm the role and what you will need. Position is the first of four application steps."
    :save-state="saveState"
  >
    <section
      v-if="hasConflict || startState === 'conflict'"
      class="conflict-state"
      aria-labelledby="conflict-title"
    >
      <p class="eyebrow">Existing application</p>
      <h2 id="conflict-title">You already started another application</h2>
      <p>
        Continue the existing application without losing your work, or abandon it before starting
        this role. ApplyFlow keeps one active server draft for this browser.
      </p>
      <div class="conflict-comparison">
        <div>
          <span>Existing draft</span><strong>{{ draft.vacancySlug }}</strong>
        </div>
        <div>
          <span>Requested role</span><strong>{{ vacancy.title }}</strong>
        </div>
      </div>
      <div class="application-actions">
        <button class="button button--secondary" type="button" @click="continueExisting">
          Continue existing application
        </button>
        <button
          v-if="!confirmAbandon"
          class="text-button text-button--danger"
          type="button"
          @click="confirmAbandon = true"
        >
          Abandon existing draft
        </button>
      </div>
      <div v-if="confirmAbandon" class="destructive-confirmation" role="alert">
        <h3>Delete the current draft?</h3>
        <p>Candidate answers and uploaded CV metadata for the current draft will be abandoned.</p>
        <div class="inline-actions">
          <button class="button button--secondary" type="button" @click="confirmAbandon = false">
            Keep draft
          </button>
          <button class="button button--danger" type="button" @click="abandonAndStart">
            Delete and start this role
          </button>
        </div>
      </div>
    </section>

    <template v-else>
      <section class="position-overview" aria-labelledby="process-title">
        <h2 id="process-title">What the application asks for</h2>
        <ol class="process-list">
          <li>
            <strong>Position</strong><span>Confirm this vacancy and understand the process.</span>
          </li>
          <li>
            <strong>Candidate details</strong
            ><span>Add contact details and one relevant profile link.</span>
          </li>
          <li>
            <strong>Experience</strong
            ><span>Share skills, context, and one PDF CV under 5 MB.</span>
          </li>
          <li>
            <strong>Review</strong><span>Check and edit every answer before submission.</span>
          </li>
        </ol>
      </section>

      <section class="context-note" aria-labelledby="draft-note-title">
        <h2 id="draft-note-title">About saving in this frontend</h2>
        <p>
          Answers are saved to a protected same-origin draft. Reloading restores the active draft
          while the server-side ownership cookie remains valid.
        </p>
      </section>

      <section class="context-note" aria-labelledby="privacy-note-title">
        <h2 id="privacy-note-title">What stays private later</h2>
        <p>
          CV files are uploaded to private backend storage. This frontend never receives a storage
          key, checksum, document ID, path, preview, or download URL.
        </p>
      </section>

      <div class="application-actions">
        <NuxtLink class="button button--secondary" :to="`/vacancies/${vacancy.slug}`"
          >Back to vacancy</NuxtLink
        >
        <NuxtLink class="button" :to="`/apply/${vacancy.slug}/details`"
          >Continue to candidate details</NuxtLink
        >
      </div>
    </template>
  </ApplicationShell>
  <ApplicationUnavailable v-else />
</template>
