<template>
  <header class="site-header">
    <div class="site-header__inner">
      <NuxtLink class="wordmark" to="/" aria-label="Northline Studio careers home">
        <span>Northline Studio</span>
        <span class="wordmark__context">Careers</span>
      </NuxtLink>
      <nav aria-label="Primary navigation">
        <ul class="site-nav">
          <li><NuxtLink to="/vacancies">Vacancies</NuxtLink></li>
          <li><NuxtLink to="/application/status">Check status</NuxtLink></li>
          <li><NuxtLink to="/case-study">Product notes</NuxtLink></li>
        </ul>
      </nav>
    </div>
  </header>
</template>
