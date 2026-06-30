import { mkdtemp, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawn } from 'node:child_process'

const scriptDir = dirname(fileURLToPath(import.meta.url))
const frontendDir = resolve(scriptDir, '..')
const repoRoot = resolve(frontendDir, '..')
const backendDir = join(repoRoot, 'backend')
const python = join(backendDir, '.venv', 'Scripts', 'python.exe')
const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm'
const npx = process.platform === 'win32' ? 'npx.cmd' : 'npx'
const djangoPort = Number(process.env.FULLSTACK_DJANGO_PORT ?? 8001)
const nuxtPort = Number(process.env.FULLSTACK_NUXT_PORT ?? 3010)
const djangoOrigin = `http://127.0.0.1:${djangoPort}`
const nuxtOrigin = `http://127.0.0.1:${nuxtPort}`

const processes = []

const spawnLogged = (command, args, options = {}) => {
  const needsWindowsShell =
    process.platform === 'win32' && (command.endsWith('.cmd') || command.endsWith('.bat'))
  const child = spawn(command, args, {
    shell: needsWindowsShell,
    stdio: ['ignore', 'pipe', 'pipe'],
    ...options,
  })
  processes.push(child)
  child.stdout.on('data', (chunk) => process.stdout.write(chunk))
  child.stderr.on('data', (chunk) => process.stderr.write(chunk))
  return child
}

const run = (command, args, options = {}) =>
  new Promise((resolveRun, rejectRun) => {
    const child = spawnLogged(command, args, options)
    child.on('exit', (code) => {
      if (code === 0) {
        resolveRun()
        return
      }
      rejectRun(new Error(`${command} ${args.join(' ')} exited with ${code}`))
    })
  })

const waitFor = async (url, label) => {
  const deadline = Date.now() + 120_000
  let lastError
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url)
      if (response.ok) return
      lastError = new Error(`${label} returned ${response.status}`)
    } catch (error) {
      lastError = error
    }
    await new Promise((resolveWait) => setTimeout(resolveWait, 750))
  }
  throw new Error(`${label} did not become ready: ${lastError?.message ?? 'unknown error'}`)
}

const killProcessTree = (child) =>
  new Promise((resolveKill) => {
    if (child.exitCode !== null || child.killed) {
      resolveKill()
      return
    }

    if (process.platform !== 'win32') {
      child.once('exit', () => resolveKill())
      child.kill()
      setTimeout(() => {
        if (child.exitCode === null && !child.killed) child.kill('SIGKILL')
        resolveKill()
      }, 3000).unref()
      return
    }

    const killer = spawn('taskkill', ['/PID', String(child.pid), '/T', '/F'], {
      stdio: 'ignore',
    })
    killer.once('exit', () => resolveKill())
    killer.once('error', () => {
      child.kill()
      resolveKill()
    })
  })

const terminateProcesses = async () => {
  await Promise.all(processes.map((child) => killProcessTree(child)))
}

const seedPython = `
from django.utils import timezone
from apps.vacancies.models import Vacancy

roles = [
    ("frontend-developer", "Frontend Developer", "Build accessible candidate-facing interfaces."),
    ("backend-developer", "Backend Developer", "Build secure Django APIs for candidate drafts."),
]

for slug, title, summary in roles:
    Vacancy.objects.update_or_create(
        slug=slug,
        defaults={
            "title": title,
            "summary": summary,
            "description": f"{title} is a fictional full-stack smoke vacancy.",
            "responsibilities": ["Build clear product workflows", "Keep security boundaries intact"],
            "requirements": ["TypeScript", "Django", "Accessibility"],
            "benefits": ["Focused product work"],
            "location": "Tashkent, Uzbekistan",
            "work_format": "hybrid",
            "employment_type": "full_time",
            "status": "published",
            "published_at": timezone.now(),
            "closing_at": None,
        },
    )
`

const main = async () => {
  const tempRoot = await mkdtemp(join(tmpdir(), 'applyflow-slice7-'))
  const settingsModule = 'applyflow_fullstack_settings'
  const settingsPath = join(tempRoot, `${settingsModule}.py`)
  const sqlitePath = join(tempRoot, 'db.sqlite3').replaceAll('\\', '\\\\')
  const privateRoot = join(tempRoot, 'private-documents').replaceAll('\\', '\\\\')
  const settingsSource = `
from pathlib import Path
from config.settings import *  # noqa: F403

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": r"${sqlitePath}"}}
DOCUMENT_PRIVATE_ROOT = Path(r"${privateRoot}")
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
`

  await writeFile(settingsPath, settingsSource, 'utf8')

  const backendEnv = {
    ...process.env,
    PYTHONPATH: `${tempRoot};${backendDir};${process.env.PYTHONPATH ?? ''}`,
    DJANGO_SETTINGS_MODULE: settingsModule,
    APP_ENV: 'development',
    DJANGO_DEBUG: '1',
    DJANGO_ALLOWED_HOSTS: '127.0.0.1,localhost,testserver',
    DOCUMENT_PRIVATE_ROOT: join(tempRoot, 'private-documents'),
  }

  try {
    await run(python, ['manage.py', 'migrate', '--noinput'], { cwd: backendDir, env: backendEnv })
    await run(python, ['manage.py', 'shell', '-c', seedPython], {
      cwd: backendDir,
      env: backendEnv,
    })

    spawnLogged(python, ['manage.py', 'runserver', `127.0.0.1:${djangoPort}`, '--noreload'], {
      cwd: backendDir,
      env: backendEnv,
    })
    await waitFor(`${djangoOrigin}/api/v1/health/`, 'Django API')

    spawnLogged(npm, ['run', 'dev', '--', '--host', '127.0.0.1', '--port', String(nuxtPort)], {
      cwd: frontendDir,
      env: { ...process.env, NUXT_API_PROXY_TARGET: djangoOrigin },
    })
    await waitFor(nuxtOrigin, 'Nuxt app')

    await run(npx, ['playwright', 'test', '--config', 'playwright.fullstack.config.ts'], {
      cwd: frontendDir,
      env: { ...process.env, FULLSTACK_BASE_URL: nuxtOrigin },
    })
  } finally {
    await terminateProcesses()
    await rm(tempRoot, { recursive: true, force: true })
  }
}

main().catch(async (error) => {
  await terminateProcesses()
  console.error(error)
  process.exit(1)
})
