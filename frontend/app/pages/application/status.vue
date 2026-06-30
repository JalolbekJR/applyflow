<script setup lang="ts">
import { useBrand } from '~/branding/useBrand'

const brand = useBrand()
const applicationReference = ref('')
const statusLookupSecret = ref('')

useSeoMeta({ title: `Check application status - ${brand.pageTitleSuffix}` })
</script>

<template>
  <div class="page-wrap status-page">
    <header class="page-heading">
      <p class="eyebrow">Private status utility</p>
      <h1 tabindex="-1">Check application status</h1>
      <p>
        Status lookup is planned for Phase 4. This page does not accept fabricated references or
        secrets in the real draft flow.
      </p>
    </header>

    <form id="status-lookup-form" class="status-form" novalidate aria-describedby="status-deferred">
      <p id="status-deferred" class="server-error" tabindex="-1" role="status">
        Private status lookup is not available in this build. Application references and status
        secrets will be issued only after Phase 4 submission exists.
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
      <button class="button" type="submit" disabled aria-describedby="status-deferred">
        Status lookup unavailable
      </button>
    </form>
  </div>
</template>
