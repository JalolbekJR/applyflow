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
        The current Nuxt frontend is backed by fictional data and simulated services. It includes
        responsive vacancy pages, a four-step application flow, validation states, and typed service
        boundaries for the planned API.
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
        Django and DRF will become the source of truth for vacancies, anonymous drafts, private CV
        storage, atomic submission, duplicate protection, and minimal status lookup.
      </p>
    </section>
  </article>
</template>
