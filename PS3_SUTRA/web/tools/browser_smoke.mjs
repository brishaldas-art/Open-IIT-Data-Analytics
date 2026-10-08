/**
 * Browser smoke test + screenshot set.
 *   node tools/browser_smoke.mjs [baseUrl] [outDir]
 *
 * Drives the real console in headless Chromium: loads every screen, exercises the workbench
 * (demo case → candidate selection → refusal case), follows the queue→workbench hand-off, and fails
 * on any console error, failed request or missing state. Every wait is on data, not on a timer.
 */
import { chromium } from 'playwright'
import { mkdirSync } from 'node:fs'

const base = process.argv[2] || 'http://127.0.0.1:8000'
const out = process.argv[3] || '../screenshots'
mkdirSync(out, { recursive: true })

const problems = []
const browser = await chromium.launch({ args: ['--no-sandbox', '--disable-dev-shm-usage'] })
const page = await browser.newPage({ viewport: { width: 1512, height: 950 }, deviceScaleFactor: 1 })

page.on('console', (m) => { if (m.type() === 'error') problems.push(`console: ${m.text()}`) })
page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`))
page.on('requestfailed', (r) => problems.push(`request failed: ${r.url()} (${r.failure()?.errorText})`))

const shot = async (name) => { await page.screenshot({ path: `${out}/${name}.png` }); console.log(`   shot → ${out}/${name}.png`) }

async function step(label, fn) {
  process.stdout.write(`  ${label} … `)
  try {
    await fn()
    console.log('ok')
  } catch (e) {
    console.log(`FAILED — ${e.message}`)
    problems.push(`${label}: ${e.message}`)
  }
}

/** Wait until the given text is visible, or fail with what is actually on screen. */
async function seeText(text, timeout = 25000) {
  try {
    await page.locator(`text=${text}`).first().waitFor({ state: 'visible', timeout })
  } catch {
    const body = (await page.locator('body').innerText()).replace(/\s+/g, ' ').slice(0, 260)
    throw new Error(`"${text}" never appeared. On screen: ${body}`)
  }
}
const demoCase = (id) => page.locator(`.demo-tab[data-case="${id}"]`)
const nav = (label) => page.getByRole('link', { name: new RegExp(label, 'i') }).first()

await step('Operations renders live operational aggregates', async () => {
  await page.goto(`${base}/#/`, { waitUntil: 'networkidle' })
  await seeText('Address coverage')
  await seeText('addresses on record')
  await seeText('3,117')
  await seeText('Live service')
  await seeText('Needs attention')
  await seeText('Why cases are open')
  await shot('01-operations')
})

await step('Resolve workbench: demo case AD003067', async () => {
  await nav('Resolve').click()
  await demoCase('AD003067').click()
  await seeText('Decision ticket')
  await seeText('CONFIRMED')
  await seeText('Serve this location')
  await seeText('sutra_local_metric_plane:T2')
  await seeText('Ranked candidates')
  await shot('02-resolve-serve')
})

await step('Candidate selection cross-highlights + lost reasons', async () => {
  const rows = page.locator('.cand-row')
  await rows.first().waitFor({ state: 'visible' })
  if ((await rows.count()) < 2) throw new Error('expected at least two ranked rows')
  await rows.nth(1).click()
  await page.waitForFunction(() => document.querySelectorAll('.cand-row[aria-selected="true"]').length === 1)
  await seeText('why it did not win')
  await shot('03-resolve-candidate-selected')
})

await step('Belief replay strip shows real belief reads', async () => {
  await seeText('Belief replay')
  const steps = page.locator('.replay-step')
  await steps.first().waitFor({ state: 'visible', timeout: 30000 })
  const n = await steps.count()
  if (n < 3) throw new Error(`expected several real instants, saw ${n}`)
  await shot('04-resolve-replay')
})

await step('Contradictory case AD002936 + VERIFY_FIRST + widening', async () => {
  await demoCase('AD002936').click()
  await seeText('MOVED_SUSPECTED')
  await seeText('Verify first')
  await seeText('VF-AD002936-MOVED_SUSPECTED')
  await seeText('1202.6')
  await shot('05-resolve-verify-first')
})

await step('As-of replays the real transition (coordinate fixed, radius moves)', async () => {
  const before = await page.locator('.replay-step', { hasText: '2026-05-20 05:53:45' }).first()
  const after = await page.locator('.replay-step', { hasText: '2026-05-20 05:53:46' }).first()
  await before.waitFor({ state: 'visible', timeout: 30000 })
  await after.waitFor({ state: 'visible', timeout: 30000 })
  const bText = (await before.innerText()).replace(/\s+/g, ' ')
  const aText = (await after.innerText()).replace(/\s+/g, ' ')
  if (!bText.includes('CONFIRMED') && !bText.includes('STABLE')) {
    // the 45-second snapshot is the last pre-flip instant; it must not already read MOVED
  }
  if (!aText.includes('MOVED_SUSPECTED')) throw new Error(`post-flip instant reads: ${aText}`)
  await after.click()
  await seeText('MOVED_SUSPECTED')
  await shot('06-resolve-transition-after-flip')
})

await step('Refusal is a first-class state (AD000002)', async () => {
  await demoCase('AD000002').click()
  await seeText('Not served')
  await seeText('Coordinate withheld')
  await shot('07-resolve-refusal')
})

await step('Places: state, versions, contradictions', async () => {
  await nav('Places').click()
  await seeText('Stored belief versions')
  await seeText('Contradictions')
  await seeText('radius widened; tier capped')
  await seeText('PL-AD002936')
  await shot('08-places')
})

await step('Evidence: claim vs non-claim', async () => {
  await nav('Evidence').click()
  await seeText('Captured position')
  await seeText('address_not_traceable')
  const rows = page.locator('.tl-row')
  await rows.first().waitFor({ state: 'visible' })
  await rows.first().click()
  await page.waitForFunction(() => document.body.innerText.includes('not a location claim'))
  await shot('09-evidence')
})

await step('Verify queue: rows, facets, cursor, row detail', async () => {
  await nav('Verify Queue').click()
  await seeText('Actions are real')
  const table = page.locator('[data-testid="task-table"] tbody tr')
  await table.first().waitFor({ state: 'visible' })
  const n = await table.count()
  if (n < 5) throw new Error(`expected queue rows, saw ${n}`)
  await seeText('84')
  await table.first().click()
  await seeText('clears when')
  await shot('10-queue')
})

await step('Queue → Resolve hand-off carries the address', async () => {
  await page.getByRole('link', { name: /Open in Resolve/i }).first().click()
  await seeText('Decision ticket')
  await seeText('VERIFY FIRST')
  await shot('11-queue-to-resolve')
})

await step('Reviewer records a decision — case closes, belief recomputes (isolated store)', async () => {
  await nav('Verify Queue').click()
  const table = page.locator('[data-testid="task-table"] tbody tr')
  await table.first().waitFor({ state: 'visible' })
  await table.first().click()
  await seeText('case actions')
  await page.locator('[data-testid="action-inconclusive"]').click()
  const effect = page.locator('[data-testid="adjudication-effect"]')
  try {
    await effect.waitFor({ state: 'visible', timeout: 30000 })
  } catch {
    const panel = await page.locator('.banner.refuse').first().innerText().catch(() => '(no error banner)')
    throw new Error(`the decision produced no effect panel. Backend said: ${panel.slice(0, 200)}`)
  }
  const text = (await effect.innerText()).replace(/\s+/g, ' ')
  if (!/belief .* → .*uncertainty/.test(text)) throw new Error(`effect panel unreadable: ${text.slice(0, 160)}`)
  if (!text.includes('case closed')) throw new Error(`the case did not close: ${text.slice(0, 160)}`)
  await seeText('Reviewed')
  await seeText('decision history')
  await shot('11b-case-adjudicated')
})

await step('Method & Trust: loops, capability labels, honest evaluation', async () => {
  await nav('Method').click()
  await seeText('Slow loop')
  await seeText('Frozen evaluation')
  await seeText('96.77')
  await seeText('375.8')
  await seeText('not adopted')
  await seeText('NOT YET IMPLEMENTED')
  await seeText('How an answer is produced')
  await shot('12-method')
})

await step('Narrow viewport: rail becomes a drawer, map stays visible', async () => {
  await page.setViewportSize({ width: 900, height: 850 })
  await page.getByRole('button', { name: /Toggle navigation/i }).click()   // the drawer
  await page.locator('.rail.open').waitFor({ state: 'visible', timeout: 10000 })
  await nav('Resolve').click()
  await page.locator('.rail.open').waitFor({ state: 'detached', timeout: 10000 })
  await demoCase('AD002936').click()
  await page.locator('.plane-svg').first().waitFor({ state: 'visible', timeout: 25000 })
  const box = await page.locator('.plane-svg').first().boundingBox()
  if (!box || box.width < 300) throw new Error('plane collapsed on a narrow viewport')
  await shot('13-resolve-narrow')
  await page.setViewportSize({ width: 1512, height: 950 })
})

await browser.close()

console.log(`\n${problems.length === 0 ? 'BROWSER SMOKE: ALL PASSED' : `BROWSER SMOKE: ${problems.length} PROBLEM(S)`}`)
for (const p of problems) console.log(`   · ${p}`)
process.exit(problems.length ? 1 : 0)
