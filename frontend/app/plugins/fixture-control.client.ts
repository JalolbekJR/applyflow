import { fixtureApplicationServiceControl } from '~/services/application-service'

declare global {
  interface Window {
    __applyflowFixtureControl?: typeof fixtureApplicationServiceControl
  }
}

export default defineNuxtPlugin(() => {
  if (!import.meta.dev) return

  Object.defineProperty(window, '__applyflowFixtureControl', {
    configurable: true,
    value: fixtureApplicationServiceControl,
  })
})
