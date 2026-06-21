export default defineNuxtConfig({
  compatibilityDate: '2026-06-20',
  devtools: { enabled: false },
  modules: ['@nuxt/eslint'],
  css: ['~/assets/css/main.css'],
  app: {
    head: {
      htmlAttrs: { lang: 'en' },
      meta: [
        { name: 'theme-color', content: '#f3f0e8' },
        { name: 'color-scheme', content: 'light' },
      ],
    },
  },
  typescript: {
    strict: true,
    typeCheck: false,
  },
  eslint: {
    config: {
      stylistic: false,
    },
  },
})
