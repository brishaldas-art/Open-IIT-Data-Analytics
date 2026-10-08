/* ------------------------------------------------------------------ *
 * Browser smoke against the deployed workbench (battle_model build).
 *
 *   node battle_model/tools/browser_smoke.mjs http://127.0.0.1:8001 ../screenshots
 *
 * Runs against an ISOLATED store (:8001) because it performs the real writes
 * (adjudication, task transition). Every check is a claim the handoff makes:
 * real data, real decision ticket, real uncertainty, refusal hides the
 * coordinate, the map cross-highlights, and the console stays clean.
 * ------------------------------------------------------------------ */
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";

const BASE = process.argv[2] || "http://127.0.0.1:8001";
const SHOTS = process.argv[3] || "../screenshots";
mkdirSync(SHOTS, { recursive: true });

const results = [];
const shot = async (page, name) => page.screenshot({ path: `${SHOTS}/${name}.png`, fullPage: false });
async function check(name, fn) {
  try {
    const detail = await fn();
    results.push([true, name, detail ?? ""]);
  } catch (e) {
    results.push([false, name, (e && e.message ? e.message : String(e)).split("\n")[0].slice(0, 160)]);
  }
}
const ok = (cond, msg) => { if (!cond) throw new Error(msg); };
const text = (page, sel) => page.locator(sel).first().innerText();

const browser = await chromium.launch({
  args: ["--no-sandbox", "--disable-dev-shm-usage"],
});
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
const consoleErrors = [];
const pageErrors = [];
const badResponses = [];
page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text()); });
page.on("pageerror", (e) => pageErrors.push(String(e)));
page.on("response", (r) => {
  const u = new URL(r.url());
  if (r.status() >= 400 && u.origin === new URL(BASE).origin) badResponses.push(`${r.status()} ${u.pathname}`);
});

/* Every request must be a real endpoint — no fixtures, no waiting on invented delays. */
const apiCalls = [];
page.on("request", (r) => {
  const u = new URL(r.url());
  if (u.pathname.startsWith("/v1") || ["/health", "/resolve", "/evidence", "/explain"].includes(u.pathname)) {
    apiCalls.push(`${r.method()} ${u.pathname}`);
  }
});

try {
  /* ---------- 1. Operations (Overview) ---------- */
  await check("01 overview renders real operational counts", async () => {
    await page.goto(`${BASE}/#/overview`, { waitUntil: "networkidle" });
    await page.waitForSelector("text=Addresses indexed", { timeout: 15000 });
    const indexed = await text(page, "text=Addresses indexed >> xpath=../..");
    ok(/3,117|3.117/.test(indexed), `indexed count not from the store: ${indexed.slice(0, 80)}`);
    await shot(page, "bm-01-overview");
    return "indexed 3,117 · frozen populations shown";
  });

  await check("02 overview shows the three frozen populations, never a single accuracy figure", async () => {
    const body = await page.locator("body").innerText();
    ok(body.includes("Cold start"), "cold population missing");
    ok(body.includes("Product lane"), "product lane missing");
    ok(!/98\s?%/.test(body), "a single blended accuracy figure appeared");
    ok(/not merged into one accuracy figure/i.test(body), "the populations-are-separate note is missing");
    return "cold / warm / product lanes, stated separately";
  });

  /* ---------- 2. Resolve (Resolver) ---------- */
  await check("03 resolver answers AD003067 from the service with SERVE", async () => {
    await page.goto(`${BASE}/#/resolver`, { waitUntil: "networkidle" });
    await page.waitForSelector("[data-testid='arms-considered']", { timeout: 15000 });
    await page.click("text=AD003067 · clean · serve");
    await page.waitForFunction(() => document.body.innerText.includes("AD003067"), null, { timeout: 15000 });
    const meta = await text(page, "[data-testid='answer-meta']");
    ok(/566\.9 m/.test(meta), `expected the 566.9 m radius from the store, got: ${meta}`);
    const body = await page.locator("body").innerText();
    ok(/SERVE/i.test(body), "gate SERVE not shown");
    ok(/CONFIRMED/.test(body), "tier CONFIRMED not shown");
    await shot(page, "bm-02-resolver-serve");
    return meta.replace(/\s+/g, " ").slice(0, 90);
  });

  await check("04 resolver answers AD002936 with VERIFY_FIRST and 1202.6 m", async () => {
    await page.click("text=AD002936 · drift · verify first");
    await page.waitForFunction(() => document.body.innerText.includes("VF-AD002936-MOVED_SUSPECTED"), null, { timeout: 15000 });
    const meta = await text(page, "[data-testid='answer-meta']");
    const body = await page.locator("body").innerText();
    ok(/1202\.6 m/.test(meta), `expected 1202.6 m, got: ${meta}`);
    ok(/VERIFY FIRST|VERIFY_FIRST/i.test(body), "gate VERIFY_FIRST not shown");
    ok(/MOVED SUSPECTED|MOVED_SUSPECTED/i.test(body), "status MOVED_SUSPECTED not shown");
    ok(/negative_accumulation/.test(body), "the live widen reason is missing");
    await shot(page, "bm-03-resolver-verify-first");
    return `${meta.replace(/\s+/g, " ").slice(0, 70)} · gate VERIFY_FIRST`;
  });

  await check("05 the decision ticket carries typed reason codes and real score terms", async () => {
    const chips = await page.locator("[data-testid='provenance']").count();
    ok(chips === 1, "provenance block missing");
    const body = await page.locator("body").innerText();
    ok(/Arm prior field evidence|arm_prior:field_evidence/.test(body), "typed score terms missing");
    ok(/visits:median/.test(body), "the candidate's real source_ref is missing");
    return "typed reason codes + source_ref visits:median(2)";
  });

  await check("06 selecting a candidate cross-highlights the map", async () => {
    const before = await page.locator(".marching").count();
    await page.click("[data-testid='arm-1']");
    await page.waitForTimeout(400);
    const selected = await page.locator("[data-testid='arm-1'].border-accent").count();
    ok(selected === 1, "the clicked arm did not become the active card");
    const after = await page.locator(".marching").count();
    ok(after >= 1 && before >= 1, "no uncertainty ring on the plane");
    await shot(page, "bm-04-cross-highlight");
    return `arm card active · ${after} uncertainty ring(s) drawn`;
  });

  await check("07 free text resolves through the live pipeline (no fixture replay)", async () => {
    await page.fill("[data-testid='intake-input']", "Gali no-11, Azad Mohalla, Devgarh Nagar - 970203");
    await page.click("[data-testid='intake-resolve']");
    await page.waitForFunction(() => document.body.innerText.includes("AD002936"), null, { timeout: 15000 });
    const body = await page.locator("body").innerText();
    ok(/address_text ·/.test(body), "the request was not shown as free text");
    ok(!/fixture|replay/i.test(body), "fixture wording leaked into the UI");
    return "typed address → AD002936 via POST /resolve";
  });

  await check("08 refusal renders no coordinate anywhere (AD000002)", async () => {
    await page.click("text=AD000002 · work-like · refuse");
    await page.waitForSelector("[data-testid='refusal-panel']", { timeout: 15000 });
    const panel = await text(page, "[data-testid='refusal-panel']");
    ok(/no coordinate is served/i.test(panel), "the refusal panel does not say the coordinate is withheld");
    ok(!/E\s+\d{3}/.test(panel), `a coordinate appeared inside the refusal panel: ${panel.slice(0, 90)}`);
    await page.waitForSelector("[data-testid='plane-withheld']", { timeout: 15000 });
    const withheld = await page.locator("[data-testid='plane-withheld']").count();
    ok(withheld === 1, "the plane did not render its withheld state");
    const answer = await page.locator("[data-testid='answer-x']").count();
    ok(answer === 0, "a coordinate block was rendered for a refused answer");
    await shot(page, "bm-05-refusal");
    return panel.replace(/\s+/g, " ").slice(0, 80);
  });

  /* ---------- 3. Places ---------- */
  await check("09 places list and detail come from the place projection", async () => {
    await page.goto(`${BASE}/#/places`, { waitUntil: "networkidle" });
    await page.waitForSelector("text=Place index", { timeout: 15000 });
    await page.waitForSelector("[data-testid='place-row']", { timeout: 20000 });
    const body = await page.locator("body").innerText();
    ok(/colocation<=30m\|adjudicated/i.test(body), "the frozen identity rule is not shown");
    ok(/[\d,]+\s+matching/i.test(body), "no match count from the service");
    ok(!/confidence\s+\d+%/i.test(body), "a confidence percentage appeared on Places");
    await shot(page, "bm-06-places");
    return "PL-* keyed under the frozen identity rule";
  });

  await check("10 place detail shows the stored point, radius and real belief versions", async () => {
    await page.fill("input[placeholder='search label, id, account…']", "AD002936");
    await page.waitForTimeout(900);
    await page.locator("[data-testid='place-row']").first().click();
    await page.waitForFunction(() => /stored point/i.test(document.body.innerText), null, { timeout: 15000 });
    const body = await page.locator("body").innerText();
    ok(/stored point · sutra_local_metric_plane:T\d/i.test(body), "the coordinate space label is missing");
    ok(/radius \d/i.test(body), "no radius on the stored point");
    ok(/belief versions/i.test(body), "the stored belief versions are missing");
    return "point + radius + version rows from /v1/place";
  });

  /* ---------- 4. Evidence ---------- */
  await check("11 evidence feed is the stored observations, with the policy's verdict", async () => {
    await page.goto(`${BASE}/#/evidence`, { waitUntil: "networkidle" });
    await page.waitForSelector("text=all polarities", { timeout: 15000 });
    await page.waitForFunction(() => /obs-VS\d{6}/.test(document.body.innerText), null, { timeout: 15000 });
    const body = await page.locator("body").innerText();
    ok(/obs-VS\d{6}/.test(body), "no real observation ids");
    ok(/evidence weight|what the policy said/i.test(body), "the policy verdict block is missing");
    ok(!/hdop|sats|mock provider/i.test(body), "a fabricated fix diagnostic survived");
    await shot(page, "bm-07-evidence");
    return "real observation rows + policy reason codes";
  });

  await check("12 a negative visit states that it carries no coordinate claim", async () => {
    await page.click("text=all polarities");
    await page.locator("[data-testid='polarity-negative']").click();
    await page.waitForTimeout(900);
    await page.locator("button:has-text('Not traceable')").first().click().catch(() => {});
    await page.waitForTimeout(700);
    const body = await page.locator("body").innerText();
    ok(/device position only|no — device position only/i.test(body), "the non-claim is not stated");
    ok(/never relocates the address|cannot move the coordinate/i.test(body), "the negative-never-relocates rule is not stated");
    return "negative → device position only, widening only";
  });

  /* ---------- 5. Verify queue (real writes) ---------- */
  await check("13 queue lists real tasks with their cause, priority and lifecycle state", async () => {
    await page.goto(`${BASE}/#/queue`, { waitUntil: "networkidle" });
    await page.waitForSelector("[data-testid='task-table']", { timeout: 15000 });
    const body = await page.locator("body").innerText();
    ok(/VF-AD\d{6}-/.test(body), "no real task ids");
    ok(/moved suspected|contested/i.test(body), "no cause shown");
    ok(/priority/.test(body), "no priority shown");
    await shot(page, "bm-08-queue");
    return "real task ids + causes from /v1/tasks";
  });

  await check("14 the case panel shows the ticket, the radius and the case history", async () => {
    await page.click("[data-testid='task-row-VF-AD002936-MOVED_SUSPECTED']").catch(async () => {
      await page.locator("[data-testid^='task-row-']").first().click();
    });
    await page.waitForFunction(() => /why this case exists/i.test(document.body.innerText), null, { timeout: 20000 });
    const body = await page.locator("body").innerText();
    ok(/why this case exists/i.test(body), "the reason block is missing");
    ok(/case history/i.test(body), "the real lifecycle history is missing");
    ok(/clears when/i.test(body), "the recommended action's clearing condition is missing");
    return "ticket + history + clears_when";
  });

  await check("15 a task transition is a real, recorded lifecycle event", async () => {
    const btn = page.locator("[data-testid='transition-in_progress']");
    ok(await btn.count() === 1, "the in_progress transition was not offered");
    await btn.click();
    await page.waitForFunction(() => /→ in_progress|in progress/i.test(document.body.innerText), null, { timeout: 15000 });
    const body = await page.locator("body").innerText();
    ok(/→ in_progress/.test(body), "no transition result was reported");
    await shot(page, "bm-09-transition");
    return "PATCH /v1/tasks → recorded event";
  });

  await check("16 recording a decision writes an adjudication and changes the belief", async () => {
    await page.waitForSelector("[data-testid='queue-record']", { timeout: 20000 });
    await page.click("[data-testid='queue-record']");
    await page.waitForSelector("[data-testid='queue-receipt']", { timeout: 30000 });
    const receipt = await text(page, "[data-testid='queue-receipt']");
    ok(/ADJUDICATION|CASE CLOSED|CASE UPDATED/i.test(receipt), "no receipt rendered");
    ok(/never enters S-Eval/i.test(receipt), "the S-Eval firewall disclosure is missing");
    ok(/belief v\d+/.test(receipt), "no belief version in the receipt");
    await shot(page, "bm-10-adjudication");
    return receipt.replace(/\s+/g, " ").slice(0, 110);
  });

  await check("17 the adjudication is visible in the store as a closed case", async () => {
    const r = await page.evaluate(async (base) => {
      const res = await fetch(`${base}/v1/tasks?state=resolved&limit=5`);
      return res.json();
    }, BASE);
    ok(r.count >= 1, "the resolved case is not in the task store");
    return `${r.count} resolved case(s) readable from /v1/tasks?state=resolved`;
  });

  /* ---------- 6. Method & trust ---------- */
  await check("18 method & trust shows the frozen evaluation, the rules and the four status labels", async () => {
    await page.goto(`${BASE}/#/method`, { waitUntil: "networkidle" });
    await page.waitForSelector("text=frozen evaluation", { timeout: 15000 });
    await page.waitForFunction(() => /obs-VS\d{6}/.test(document.body.innerText), null, { timeout: 15000 });
    const body = await page.locator("body").innerText();
    ok(/96\.77%|0\.9677/.test(body), "the warm-lane figure is missing");
    ok(/71\.00%|0\.7100/.test(body), "the cold-lane figure is missing");
    ok(/IMPLEMENTED/.test(body) && /NOT YET IMPLEMENTED/.test(body) && /NOT MEASURED/.test(body), "the four labels are incomplete");
    ok(/worked example/i.test(body), "no worked example from the evidence policy");
    ok(!/214 ms|median resolve latency/i.test(body), "an invented latency survived");
    await shot(page, "bm-11-method");
    return "frozen populations + safety rules + four labels";
  });

  await check("19 the audit chain is a read-only reconstruction with a real payload hash", async () => {
    await page.waitForFunction(() => /payload sha256/i.test(document.body.innerText), null, { timeout: 15000 });
    const body = await page.locator("body").innerText();
    ok(/payload sha256/.test(body), "no payload hash shown");
    ok(/Read-only reconstruction/i.test(body), "the read-only note is missing");
    return "belief payload hash + evidence rows";
  });

  /* ---------- 7. Narrow viewport ---------- */
  await check("20 narrow viewport: the workbench stays usable at 900 px", async () => {
    await page.setViewportSize({ width: 900, height: 900 });
    await page.goto(`${BASE}/#/resolver`, { waitUntil: "networkidle" });
    await page.waitForSelector("[data-testid='answer-meta']", { timeout: 15000 });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    ok(overflow <= 8, `horizontal overflow of ${overflow}px at 900px width`);
    await shot(page, "bm-12-narrow");
    await page.setViewportSize({ width: 1600, height: 1000 });
    return `no horizontal overflow (${overflow}px)`;
  });

  await check("21 every network call was a real endpoint", async () => {
    const bad = apiCalls.filter((c) => /fixture|mock|demo/i.test(c));
    ok(bad.length === 0, `suspicious calls: ${bad.join(", ")}`);
    const has = (needle) => apiCalls.some((c) => c.includes(needle));
    ok(has("/health"), "never called /health");
    ok(has("/resolve"), "never called POST /resolve");
    ok(has("/v1/tasks"), "never called /v1/tasks");
    return `${apiCalls.length} API calls, all real routes`;
  });

  await check("22 zero failing requests, zero page errors, zero console errors", async () => {
    ok(badResponses.length === 0, `requests answered >=400: ${badResponses.slice(0, 3).join(" | ")}`);
    ok(pageErrors.length === 0, `page errors: ${pageErrors.slice(0, 2).join(" | ")}`);
    const real = consoleErrors.filter((t) => !/fonts\.googleapis|fonts\.gstatic|net::ERR|favicon/i.test(t));
    ok(real.length === 0, `console errors: ${real.slice(0, 3).join(" | ")}`);
    return `no 4xx/5xx from the service · ${consoleErrors.length} console messages, none ours`;
  });
} finally {
  await browser.close();
}

const pass = results.filter(([o]) => o).length;
console.log("");
for (const [o, name, detail] of results) {
  console.log(`${o ? "  ✓" : "  ✗"} ${name}${detail ? `\n      ${detail}` : ""}`);
}
console.log(`\n${pass}/${results.length} browser checks passed against ${BASE}`);
process.exit(pass === results.length ? 0 : 1);
