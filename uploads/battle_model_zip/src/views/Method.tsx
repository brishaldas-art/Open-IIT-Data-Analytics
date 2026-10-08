import { ArrowRight, CornerUpLeft } from "lucide-react";
import { useSession } from "@/lib/session";
import { Panel, Sec, Tag } from "@/components/u";
import { ViewHead } from "@/components/Shell";
import { AuditTable } from "./Resolver";

const STAGES = [
  { n: "parse", d: "tokenise, normalise spellings, split units & floors" },
  { n: "anchor", d: "coarse locality fix on the local plane, with σ" },
  { n: "retrieve", d: "official candidates: gazette, parcels, PIN directory" },
  { n: "memory", d: "match prior places; weight by age and refute count" },
  { n: "evidence", d: "visits near candidates; integrity-gated priors" },
  { n: "score", d: "weighted composite across six signal parts" },
  { n: "policy", d: "gates: top1, margin, spatial split, support" },
  { n: "decide", d: "commit, queue field work, or declare unplaceable" },
];

const GATES = [
  { g: "top1 ≥ 0.85 and margin ≥ 0.15", r: "AUTO-CONFIRM", t: "ok" as const, d: "no human needed; still written to ledger with full trace" },
  { g: "margin < 0.15 but r1–r2 within 25 m", r: "COMMIT PERMITTED", t: "warn" as const, d: "spatial agreement overrides score ambiguity" },
  { g: "0.60 ≤ top1 < 0.85", r: "VERIFY-FIRST", t: "accent" as const, d: "strong hypothesis — send one officer, one photo fix" },
  { g: "margin < 0.15 and split > 25 m", r: "CONTESTED", t: "plum" as const, d: "two physically separated claims; never average them" },
  { g: "top1 < 0.60", r: "UNPLACEABLE", t: "crit" as const, d: "honest failure; open inquiry task instead of guessing" },
];

const SIGNALS = [
  { t: "Official candidates", w: "text 0.28 · components 0.22 · source 0.15",
    d: "Gazette records, municipal parcels and postal directories give legally grounded candidates with source references.",
    f: "fails when: gazette epoch is decades old, parcels post-date informal building, local names never entered any registry." },
  { t: "Field evidence", w: "evidence 0.20",
    d: "GNSS fixes with dwell, trails, photos and outcomes (CONFIRMED / NOT_FOUND / MOVED) collected under integrity checks.",
    f: "fails when: devices spoof locations or clocks drift — hence hard integrity gates before anything enters priors." },
  { t: "Place memory", w: "memory 0.15",
    d: "Every verified visit strengthens or weakens a stored place. Memory makes repeat lookups warm and fast.",
    f: "fails when: the world moves. Memory decays with time and is damped immediately by refute visits." },
  { t: "Uncertainty", w: "σ everywhere",
    d: "Every point carries a standard error in metres, shown on the map and stored in the record. No silent estimates.",
    f: "fails when: hidden — so SUTRA renders σ ellipses by default and blocks decisions that ignore them." },
];

export default function Method() {
  const { audit } = useSession();

  return (
    <div className="max-w-[1500px] mx-auto">
      <ViewHead
        title="Method & trust"
        note="how SUTRA combines official candidates, field evidence, memory and uncertainty into auditable decisions"
      />

      {/* pipeline */}
      <Panel className="px-3.5 py-3">
        <Sec no="01" title="Resolution pipeline" right={<span className="mono text-[8.5px] text-faint">median end-to-end 214 ms</span>} />
        <div className="flex flex-wrap items-stretch gap-1.5 mt-2.5">
          {STAGES.map((s, i) => (
            <div key={s.n} className="flex items-center gap-1.5">
              <div className="border hairline bg-paper px-2 py-1.5 min-w-[118px]">
                <div className="mono text-[9px] font-semibold uppercase tracking-[0.08em] text-accent-deep">
                  {String(i).padStart(2, "0")} {s.n}
                </div>
                <div className="text-[10px] text-ink2 leading-snug mt-0.5">{s.d}</div>
              </div>
              {i < STAGES.length - 1 && <ArrowRight size={12} className="text-faint shrink-0" />}
            </div>
          ))}
        </div>
        <div className="mt-2 flex items-center gap-2 border border-dashed border-cool/50 bg-cool-soft/40 px-2.5 py-1.5">
          <CornerUpLeft size={13} className="text-cool shrink-0" />
          <span className="text-[11px] text-ink2 leading-snug">
            <span className="mono text-[9px] uppercase tracking-[0.08em] text-cool">learning loop — </span>
            field verification outcomes flow back into memory: confirmed points tighten σ, moves rewrite the stored point,
            refutes damp trust. The next resolution of the same address starts warm.
          </span>
        </div>
      </Panel>

      <div className="grid grid-cols-12 gap-3 mt-3">
        {/* decision rule */}
        <Panel className="col-span-12 xl:col-span-7 px-3.5 py-3">
          <Sec no="02" title="Decision rule & policy gates" />
          <div className="mt-2.5 border hairline bg-paper px-3 py-3">
            <div className="serif italic text-[17px] leading-snug">
              score = 0.28·text + 0.22·components + 0.15·source + 0.20·evidence + 0.15·memory
            </div>
            <div className="mono text-[9px] text-mute mt-1">
              memory and evidence terms decay with age; refute visits damp memory before scoring. All six parts render on every candidate card — no hidden weights.
            </div>
          </div>
          <div className="mt-2.5 divide-y divide-line border hairline">
            {GATES.map((g) => (
              <div key={g.r} className="grid grid-cols-[190px_150px_1fr] gap-3 items-center px-2.5 py-2">
                <span className="mono text-[9.5px] text-ink">{g.g}</span>
                <Tag tone={g.t} className="justify-center">{g.r}</Tag>
                <span className="text-[10.5px] text-ink2 leading-snug">{g.d}</span>
              </div>
            ))}
          </div>
        </Panel>

        {/* signals */}
        <div className="col-span-12 xl:col-span-5 grid gap-3">
          {SIGNALS.map((s, i) => (
            <Panel key={s.t} className="px-3.5 py-3">
              <div className="flex items-baseline justify-between gap-2">
                <h3 className="text-[13px] font-semibold">{s.t}</h3>
                <span className="mono text-[8.5px] text-faint">{String(i + 1).padStart(2, "0")} · {s.w}</span>
              </div>
              <p className="text-[11.5px] text-ink2 leading-snug mt-1">{s.d}</p>
              <p className="mono text-[8.5px] text-mute leading-relaxed mt-1.5 border-t hairline pt-1.5">{s.f}</p>
            </Panel>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-12 gap-3 mt-3">
        {/* local plane */}
        <Panel className="col-span-12 xl:col-span-5 px-3.5 py-3">
          <Sec no="03" title="Why a local metric plane, not lat/lng" />
          <div className="mt-2.5 text-[11.5px] text-ink2 leading-snug space-y-2">
            <p>
              SUTRA's operating region is anchored to survey monument <span className="mono text-[10px]">SEAL-01</span>,
              re-traced every epoch. All geometry — candidates, trails, σ ellipses — lives in metres easting/northing
              of that origin, so distances, gates and drift are arithmetic, not geodesy.
            </p>
            <p>
              Field crews think in metres: a 99.8 m drift, a 25 m cluster gate, a 480 m anchor uncertainty.
              Conversion to global systems happens only at the interchange boundary, never inside decision logic.
            </p>
          </div>
          <div className="mt-3 border hairline bg-paper px-3 py-2.5">
            <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint">specimen · PL-AMB-0142</div>
            <div className="serif text-[21px] font-semibold tnum mt-1">E 000 700.0&nbsp;&nbsp;N 000 580.0</div>
            <div className="mono text-[8.5px] text-mute mt-0.5">metres from SEAL-01 · epoch 2025-W46 · σ 4.2 m</div>
          </div>
        </Panel>

        {/* integrity + audit */}
        <Panel className="col-span-12 xl:col-span-7 px-3.5 py-3">
          <Sec no="04" title="Evidence integrity — what gets admitted" />
          <div className="grid grid-cols-2 gap-3 mt-2.5">
            <div className="text-[11.5px] text-ink2 leading-snug space-y-2">
              <p>
                A fix enters priors only after passing hard gates: mock-provider flag, clock skew,
                dwell plausibility, trail geometry against the claimed point, and constellation quality.
              </p>
              <p>
                Failures are kept — visibly. Rejected evidence stays in the log with its flags, so audits can
                see both what the system believed and why it refused to believe.
              </p>
            </div>
            <div className="border border-crit/45 bg-crit-soft/50 px-2.5 py-2 self-start">
              <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-crit mb-1">worked example · EV-2303 rejected</div>
              <div className="mono text-[9px] text-ink2 leading-[1.7]">
                mock provider · FLAGGED<br />
                clock skew Δt · 48.2 s ≥ 2 s<br />
                dwell · 12 s &lt; 20 s floor<br />
                trail σ · 11.7 m vs CEP 9.8 m<br />
                <span className="text-crit font-semibold">→ held out of priors · device GS-19 pulled</span>
              </div>
            </div>
          </div>

          <div className="mt-3 border-t hairline pt-2.5">
            <div className="flex items-baseline justify-between mb-1.5">
              <h4 className="text-[12px] font-semibold">Auditability — live session ledger</h4>
              <span className="mono text-[8.5px] text-faint">{audit.length} events · hash-chained · append-only</span>
            </div>
            <div className="max-h-[190px] overflow-y-auto">
              <AuditTable />
            </div>
          </div>
        </Panel>
      </div>
    </div>
  );
}
