<script setup lang="ts">
useSeoMeta({ title: 'ApplyFlow product notes - Current implementation' })
</script>

<template>
  <article class="page-wrap prose">
    <header class="page-heading">
      <p class="eyebrow">Product notes / Current implementation</p>
      <h1 tabindex="-1">Building a calmer job application flow</h1>
      <p>
        ApplyFlow combines vacancy discovery, concise forms, recovery states, and a planned secure
        backend in one candidate-facing flow.
      </p>
    </header>
    <section>
      <h2>What exists today</h2>
      <p>
        The current Nuxt frontend uses the Django vacancy, draft, employment-entry, and private CV
        metadata APIs for the candidate draft path. Final submission and private status lookup are
        still future Phase 4 work.
      </p>
    </section>
    <section>
      <h2>What has not been validated</h2>
      <p>
        No participant research, production traffic, usability test, accessibility conformance
        audit, or business outcome exists yet. Current choices remain product hypotheses.
      </p>
    </section>
    <section>
      <h2>What comes later</h2>
      <p>
        Phase 4 adds atomic submission, duplicate protection, application references, and minimal
        private status lookup. Later phases cover cleanup automation, deployment, and production
        operations.
      </p>
    </section>
  </article>
</template>
