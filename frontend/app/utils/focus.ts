const nextFrame = () =>
  new Promise<void>((resolve) => {
    requestAnimationFrame(() => resolve())
  })

const revealIfNeeded = (element: HTMLElement) => {
  const safeEdge = 8
  const bounds = element.getBoundingClientRect()
  if (bounds.top < safeEdge || bounds.bottom > window.innerHeight - safeEdge) {
    const root = document.documentElement
    const previousScrollBehavior = root.style.scrollBehavior
    root.style.scrollBehavior = 'auto'
    element.scrollIntoView({ behavior: 'auto', block: 'start' })
    root.style.scrollBehavior = previousScrollBehavior
  }
}

export const focusAndReveal = async (element: HTMLElement | null) => {
  if (!element) return

  element.focus({ preventScroll: true })
  await nextFrame()
  if (document.activeElement !== element) return
  revealIfNeeded(element)

  await nextFrame()
  if (document.activeElement === element) revealIfNeeded(element)
}
