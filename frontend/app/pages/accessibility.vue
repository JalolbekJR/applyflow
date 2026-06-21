<script setup lang="ts">
useSeoMeta({ title: 'Accessibility approach - ApplyFlow' })
</script>

<template>
  <article class="page-wrap prose">
    <header class="page-heading">
      <p class="eyebrow">Accessibility approach</p>
      <h1 tabindex="-1">Clear structure and recoverable interaction</h1>
      <p>
        ApplyFlow is designed around semantic pages, visible focus, persistent labels, keyboard
        operation, useful errors, and reduced motion.
      </p>
    </header>
    <section>
      <h2>Implemented in this frontend</h2>
      <p>
        Skip navigation, landmarks, page titles, one main heading, linked field errors, error
        summaries, native controls, 44px targets, responsive reflow, and reduced-motion behavior.
      </p>
    </section>
    <section>
      <h2>Still requiring manual review</h2>
      <p>
        Screen-reader behavior, zoom across browser and operating-system combinations, contrast in
        real environments, mobile keyboard behavior, and complete keyboard testing.
      </p>
    </section>
    <section>
      <h2>No conformance claim yet</h2>
      <p>
        Automated tests and implementation intent do not establish WCAG conformance. A documented
        manual audit is required before any claim.
      </p>
    </section>
  </article>
</template>
