<script setup lang="ts">
useSeoMeta({ title: 'Privacy approach - ApplyFlow' })
</script>

<template>
  <article class="page-wrap prose">
    <header class="page-heading">
      <p class="eyebrow">Product privacy approach</p>
      <h1 tabindex="-1">Collect less, explain why</h1>
      <p>
        This page explains the intended product behavior. It is not legal advice or a production
        privacy notice.
      </p>
    </header>
    <section>
      <h2>What the form asks for</h2>
      <p>
        Contact details, one relevant profile link, a small amount of structured experience,
        consent, and one PDF CV.
      </p>
    </section>
    <section>
      <h2>What this frontend stores</h2>
      <p>
        Candidate answers and file metadata remain only in memory while the browser tab is open.
        File contents are not uploaded.
      </p>
    </section>
    <section>
      <h2>What production still requires</h2>
      <p>
        Reviewed notices, retention and deletion rules, private storage, authorization, secure
        logging, backups, and legal review.
      </p>
    </section>
  </article>
</template>
