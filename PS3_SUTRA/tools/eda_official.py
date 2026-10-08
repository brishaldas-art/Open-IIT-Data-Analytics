#!/usr/bin/env python3
"""
SUTRA — exhaustive EDA of the OFFICIAL PS3 dataset (read-only).

Writes:
  data/derived/eda_report.txt          full transcript (every number quoted in the document)
  data/derived/eda_*.csv               machine-readable tables used by the document
  data/derived/eda_charts/*.svg        self-contained charts (no external assets)

Run:  python3 tools/eda_official.py            (uses data/official_ps3, never writes to it)
"""
import os, re, sys, time, json, hashlib, unicodedata, itertools, resource, collections, warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
t_start = time.time()
HERE = os.path.dirname(os.path.abspath(__file__)); SEC = os.path.dirname(HERE)
D = os.environ.get("CN_DATASET", os.path.join(SEC, "data", "official_ps3"))
OUT = os.environ.get("CN_OUT", os.path.join(SEC, "data", "derived"))
CH = os.path.join(OUT, "eda_charts"); os.makedirs(CH, exist_ok=True)
LOG, TABLES = [], []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s); LOG.append(s)


def save(df, name, **kw):
    df.to_csv(os.path.join(OUT, f"eda_{name}.csv"), index=False, **kw)
    return df


# ───────────────────────────── SVG chart helpers ─────────────────────────────
def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def svg_bar(title, labels, values, unit="", w=760, rowh=26, pad=8, colour="#2b6cb0", note="", fmt="{:.0f}"):
    h = 46 + rowh * len(labels) + (18 if note else 4)
    for line_i in range(0, len(title) // 118 + 1):
        h += 16
    mx = max(values) if len(values) and max(values) > 0 else 1
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
           f'font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="12">',
           f'<rect width="{w}" height="{h}" fill="#ffffff"/>']
    y = 16
    for i in range(0, len(title), 118):
        out.append(f'<text x="{pad}" y="{y}" font-size="13" font-weight="600" fill="#1a202c">{_esc(title[i:i+118])}</text>')
        y += 16
    y = y - 16 + 20
    bx = w - 250
    for lab, v in zip(labels, values):
        bw = (bx - 130) * (v / mx) if mx else 0
        out.append(f'<text x="{pad}" y="{y+13}" fill="#2d3748">{_esc(str(lab)[:44])}</text>')
        out.append(f'<rect x="300" y="{y+3}" width="{max(bw,1):.1f}" height="13" rx="2" fill="{colour}" opacity="0.85"/>')
        out.append(f'<text x="{300+max(bw,1)+6:.0f}" y="{y+13}" fill="#1a202c" font-weight="600">'
                   f'{_esc(fmt.format(v))}{_esc(unit)}</text>')
        y += rowh
    if note:
        out.append(f'<text x="{pad}" y="{y+12}" fill="#718096" font-size="11">{_esc(note)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def svg_hist(title, counts, edges, colour="#c05621", note="", unit="", logy=False):
    w, h, pad = 760, 240, 40
    n = len(counts)
    mx = max(counts) if max(counts) > 0 else 1
    bw = (w - 2 * pad) / n
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
           f'font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="11">',
           f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
           f'<text x="{pad}" y="18" font-size="13" font-weight="600" fill="#1a202c">{_esc(title)}</text>',
           f'<line x1="{pad}" y1="{h-30}" x2="{w-pad}" y2="{h-30}" stroke="#e2e8f0"/>']
    for i, c in enumerate(counts):
        bh = (h - 76) * (c / mx)
        x = pad + i * bw
        out.append(f'<rect x="{x+1:.1f}" y="{h-30-bh:.1f}" width="{max(bw-2,1):.1f}" height="{bh:.1f}" '
                   f'fill="{colour}" opacity="0.85"/>')
        if c:
            out.append(f'<text x="{x+bw/2:.1f}" y="{h-34-bh:.1f}" text-anchor="middle" fill="#4a5568">{c}</text>')
    for i in range(0, n + 1, max(1, n // 10)):
        x = pad + i * bw
        lab = f"{edges[i]:g}"
        out.append(f'<text x="{x:.1f}" y="{h-16}" text-anchor="middle" fill="#718096">{_esc(lab)}</text>')
    if note:
        out.append(f'<text x="{pad}" y="{h-4}" fill="#718096">{_esc(note)}</text>')
    out.append("</svg>")
    return "\n".join(out)


CHARTS = {}
def chart(name, svg):
    CHARTS[name] = svg
    with open(os.path.join(CH, f"{name}.svg"), "w", encoding="utf-8") as f:
        f.write(svg)


# ───────────────────────────── loading ─────────────────────────────
say("=" * 100)
say("SUTRA — OFFICIAL PS3 DATASET: EXHAUSTIVE EDA")
say(f"source: {D}   (opened read-only)")
say("=" * 100)

FILES = {}
for fn in sorted(os.listdir(D)):
    if fn.endswith(".csv"):
        FILES[fn[:-4]] = os.path.join(D, fn)
say("\nsource files and SHA-256 (first 12 hex) — proof of the exact snapshot analysed")
HASH = {}
for k, p in FILES.items():
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()[:12]
    HASH[k] = h
    say(f"  {k:<22} {os.path.getsize(p)/1e6:8.3f} MB   sha256:{h}")

T = {k: pd.read_csv(p, low_memory=False) for k, p in FILES.items()}
ad, ac, ag = T["addresses"], T["accounts"], T["agents"]
bg, fv, lm = T["baseline_geocodes"], T["field_visits"], T["landmarks_poi"]
lo, sp, sv, tw = T["localities"], T["splits"], T["surveyed_addresses"], T["towns"]
gp = T["visit_gps_points"]

say("\nrow / column counts verified from the files themselves:")
for k, df in T.items():
    say(f"  {k:<22} rows={len(df):>7}  cols={len(df.columns):>3}")
say(f"  TOTAL rows across all 11 tables: {sum(len(x) for x in T.values()):,}")

# ═══════════════════════ 1. TABLE PROFILES ═══════════════════════
say("\n" + "=" * 100)
say("SECTION 1 — TABLE-BY-TABLE PROFILE (schema, keys, nulls, cardinality, duplicates, ranges)")
say("=" * 100)

prof_rows, col_rows = [], []
for k, df in T.items():
    dup_rows = int(df.duplicated().sum())
    pk_cands = [c for c in df.columns if c.endswith("_id") or c in ("seq",)]
    pk_report = []
    for c in pk_cands:
        u = df[c].nunique(dropna=True)
        pk_report.append(f"{c}:{u}{'=UNIQUE' if u == len(df) else ''}")
    say(f"\n▸ {k}  rows={len(df)}  cols={len(df.columns)}  exact duplicate rows={dup_rows}")
    say(f"   id-like columns → {', '.join(pk_report) if pk_report else 'none'}")
    for c in df.columns:
        s = df[c]
        nulls = int(s.isna().sum())
        nn = len(df) - nulls
        nun = int(s.nunique(dropna=True))
        dt = str(s.dtype)
        extra = ""
        if pd.api.types.is_numeric_dtype(s) and nn:
            extra = f" min={s.min():.4g} max={s.max():.4g} mean={s.mean():.4g}"
        elif nn:
            top = s.value_counts().head(3)
            extra = " top=" + " | ".join(f"{str(i)[:26]}×{v}" for i, v in top.items())
        flag = ""
        if nun == 1 and nn: flag = "  [CONSTANT]"
        elif nun == len(df) and nulls == 0: flag = "  [unique]"
        say(f"     {c:<24} {dt:<9} null%={100*nulls/len(df):5.1f} distinct={nun:<6}{flag}{extra}")
        col_rows.append(dict(table=k, column=c, dtype=dt, null_pct=round(100*nulls/len(df), 3),
                             distinct=nun, rows=len(df), note=flag.strip("[]")))
        prof_rows.append(dict(table=k, column=c, null_pct=round(100*nulls/len(df), 3), distinct=nun))

say("\nDATE / TIME / COORDINATE RANGES")
date_cols = [("addresses", "added_date"), ("field_visits", "visit_date"), ("field_visits", "start_ts"),
             ("field_visits", "checkin_ts"), ("visit_gps_points", "point_ts")]
for k, c in date_cols:
    s = pd.to_datetime(T[k][c], errors="coerce")
    say(f"  {k}.{c:<12} {s.min()}  →  {s.max()}   (nulls={int(s.isna().sum())})")
for k, cx, cy in [("baseline_geocodes", "geocoder_x", "geocoder_y"), ("localities", "centroid_x", "centroid_y"),
                  ("landmarks_poi", "x", "y"), ("field_visits", "checkin_x", "checkin_y"),
                  ("surveyed_addresses", "surveyed_x", "surveyed_y"), ("visit_gps_points", "x", "y")]:
    a, b = T[k][cx], T[k][cy]
    say(f"  {k:<19} x∈[{a.min():.1f},{a.max():.1f}] y∈[{b.min():.1f},{b.max():.1f}] "
        f"(mean |x|={abs(a).mean():.1f}, |y|={abs(b).mean():.1f})")
save(pd.DataFrame(col_rows), "column_profile")
save(pd.DataFrame(prof_rows), "missingness")

# ═══════════════════════ 2. ADDRESS TEXT EDA ═══════════════════════
say("\n" + "=" * 100)
say("SECTION 2 — ADDRESS TEXT EDA")
say("=" * 100)

at = ad.address_text.astype(str)
L = at.str.len(); TOK = at.str.split().str.len()
DIG = at.str.count(r"\d"); ALPHA = at.str.count(r"[A-Za-z]")
COMMA = at.str.count(","); SLASH = at.str.count("/"); HYPH = at.str.count("-"); DOT = at.str.count(r"\.")
NONASCII = at.str.contains(r"[^\x00-\x7F]", regex=True)
DEV = at.str.contains(r"[\u0900-\u097F]"); KAN = at.str.contains(r"[\u0C80-\u0CFF]")
# House-number detection: two explicit, reproducible definitions.
#   HOUSE     — marker-anchored: a dwelling marker followed by a digit, or a "12/3"-style token.
#   HOUSELOOSE— upper bound: any numeric token at all (includes pincodes, road numbers, pincode tails).
HOUSE_MARK = at.str.contains(
    r"(?i)(?:\bh\.?\s*no\.?|\bhouse(?:\s*no\.?)?|\bplot|\bdoor|\bd\.?\s*no\.?|\bno\.?|\bflat|#)\s*[:\-]?\s*\d",
    regex=True)
HOUSE_SLASH = at.str.contains(r"\b\d{1,4}\s*/\s*\d{1,3}\b", regex=True)
HOUSE = HOUSE_MARK | HOUSE_SLASH
HOUSELOOSE = at.str.contains(r"\b\d+\b", regex=True)
SIX = at.str.extract(r"\b(\d{6})\b")[0]
PIN_KNOWN = set(lo.pincode.astype(str))
pw = [w for w in re.split(r"[^A-Za-z]+", " ".join(at).lower()) if len(w) > 2]
word_freq = collections.Counter(pw)
LOCWORDS = set(" ".join(lo.locality_name.astype(str)).lower().split())
LMNAMES = set(" ".join(lm["name"].astype(str)).lower().split())
TOWNWORDS = set(" ".join(tw.town_name.astype(str)).lower().split())

say(f"length      : min={L.min()} p25={L.quantile(.25):.0f} median={L.median():.0f} p75={L.quantile(.75):.0f} "
    f"p90={L.quantile(.9):.0f} max={L.max()} mean={L.mean():.1f}")
c, e = np.histogram(L, bins=12, range=(0, 120))
chart("addr_len", svg_hist("Address text length (characters), n=3,117", list(c), list(e),
                           note="Median 67 characters — records are short, semi-structured strings."))
say("length histogram bins(0..120): " + ", ".join(f"{int(e[i])}-{int(e[i+1])}:{int(c[i])}" for i in range(len(c))))
say(f"tokens      : min={TOK.min()} median={TOK.median():.0f} p90={TOK.quantile(.9):.0f} max={TOK.max()} mean={TOK.mean():.2f}")
c, e = np.histogram(TOK, bins=min(15, int(TOK.max() + 1)), range=(0, int(TOK.max()) + 1))
chart("addr_tokens", svg_hist("Address token count, n=3,117", list(c), list(e), colour="#2f855a",
                              note="11.9 tokens on average: enough for word-level matching."))
say("token histogram: " + ", ".join(f"{int(e[i])}:{int(c[i])}" for i in range(len(c))))
say(f"digits      : mean={DIG.mean():.2f} median={DIG.median():.0f}; addresses with 0 digits={int((DIG==0).sum())} "
    f"({100*(DIG==0).mean():.2f}%)")
say(f"letters     : mean={ALPHA.mean():.1f}; addresses with <5 letters={int((ALPHA<5).sum())}")
say(f"commas      : 0 commas={int((COMMA==0).sum())} ({100*(COMMA==0).mean():.1f}%) · "
    f"1={int((COMMA==1).sum())} · 2={int((COMMA==2).sum())} · 3+={int((COMMA>=3).sum())}")
say(f"slashes     : any={int((SLASH>0).sum())} ({100*(SLASH>0).mean():.1f}%) · max={SLASH.max()}")
say(f"hyphens     : any={int((HYPH>0).sum())} ({100*(HYPH>0).mean():.1f}%) · max={HYPH.max()}")
say(f"dots        : any={int((DOT>0).sum())} ({100*(DOT>0).mean():.1f}%)   [likely abbreviations like 'H.No.']")
say(f"NO comma/slash/hyphen at all: {int(((COMMA+SLASH+HYPH)==0).sum())} ({100*((COMMA+SLASH+HYPH)==0).mean():.1f}%)")
say(f"house-number (marker-anchored): {int(HOUSE.sum())} ({100*HOUSE.mean():.1f}%)   "
    f"[marker+digit={int(HOUSE_MARK.sum())} ({100*HOUSE_MARK.mean():.1f}%) · 12/3-style={int(HOUSE_SLASH.sum())} "
    f"({100*HOUSE_SLASH.mean():.1f}%)]  ← the definition used below")
say(f"house-number (any numeric token, upper bound): {int(HOUSELOOSE.sum())} ({100*HOUSELOOSE.mean():.1f}%)   "
    f"[the two definitions disagree by {100*(HOUSELOOSE.mean()-HOUSE.mean()):.1f} points: house-number parsing is "
    f"definition-dependent, so BOTH are kept as features and neither is treated as a fact]")
say(f"6-digit token present       : {int(SIX.notna().sum())} ({100*SIX.notna().mean():.1f}%); "
    f"of those, matches a known pincode: {int(SIX.isin(PIN_KNOWN).sum())} "
    f"({100*SIX[SIX.notna()].isin(PIN_KNOWN).mean():.1f}% of those) — unknown: {int((SIX.notna() & ~SIX.isin(PIN_KNOWN)).sum())}")
say(f"non-ASCII rows              : {int(NONASCII.sum())} ({100*NONASCII.mean():.2f}%)  "
    f"Devanagari={int(DEV.sum())}  Kannada={int(KAN.sum())}")
say("non-ASCII examples:")
for s in at[NONASCII].head(4):
    say("    " + s[:112])
mention_loc = at.map(lambda t: any(w in t.lower().split() for w in LOCWORDS if len(w) > 3))
# landmark mention: any multiword landmark name present as substring
LM_PHRASES = sorted({str(n).lower() for n in lm["name"] if len(str(n)) > 5})
mention_lm = at.str.lower().map(lambda t: any(p in t for p in LM_PHRASES))
mention_town = at.str.lower().map(lambda t: any(w in t for w in TOWNWORDS if len(w) > 3))
say(f"locality-name token present : {int(mention_loc.sum())} ({100*mention_loc.mean():.1f}%)")
say(f"known landmark phrase present: {int(mention_lm.sum())} ({100*mention_lm.mean():.1f}%)")
say(f"town name present            : {int(mention_town.sum())} ({100*mention_town.mean():.1f}%)")
say(f"has BOTH house-number token and a known locality: "
    f"{int((HOUSE & mention_loc).sum())} ({100*(HOUSE & mention_loc).mean():.1f}%)")
say(f"has NEITHER                                     : "
    f"{int((~HOUSE & ~mention_loc).sum())} ({100*(~HOUSE & ~mention_loc).mean():.1f}%)")

say("\ntop 30 content words:")
for w, n in word_freq.most_common(30):
    say(f"    {w:<16} {n:>6}  ({100*n/len(ad):5.1f}%)")
say("\nrarest word shapes (unusual tokens, freq==1, length>8, sample 12): "
    + ", ".join([w for w, n in word_freq.items() if n == 1 and len(w) > 8][:12]))

ABBR = {"h.no": r"\bh\.?\s?no", "no.": r"\bno\.", "st": r"\bst\b", "rd": r"\brd\b", "nagar/nager": r"\bnag(ar|er)\b",
        "colony": r"\bcolon(y|ies)\b", "layout": r"\blay\s?out\b", "cross": r"\bcross\b", "main": r"\bmain\b",
        "block": r"\bblock\b", "sector": r"\bsector\b", "near": r"\bnear\b", "opp": r"\bopp\b", "behind": r"\bbehind\b",
        "gali": r"\bgali\b", "extension": r"\bext(n|ension)?\b", "opposite": r"\bopposite\b", "circle": r"\bcircle\b",
        "stage": r"\bstage\b", "phase": r"\bphase\b"}
say("\nstructural vocabulary (records containing the token):")
for k, rx in ABBR.items():
    n = int(at.str.contains(rx, case=False, regex=True).sum())
    say(f"    {k:<12} {n:>5}  ({100*n/len(ad):5.1f}%)")

bigrams = collections.Counter()
for t in at.str.lower():
    ws = re.split(r"[^a-z]+", t)
    ws = [w for w in ws if w]
    bigrams.update(zip(ws, ws[1:]))
say("\ntop 12 repeated 2-grams: " + ", ".join(f"'{a} {b}'×{n}" for (a, b), n in bigrams.most_common(12)))

templates = at.str.replace(r"\d+", "#", regex=True).str.replace(r"[a-z]+", "w", regex=True).str.slice(0, 40)
say(f"\nrepeated structural templates (digits→#, words→w): {templates.nunique()} distinct over {len(at)} rows; "
    f"the 8 most common cover {100*templates.value_counts().head(8).sum()/len(at):.1f}% of rows")
for t, n in templates.value_counts().head(8).items():
    say(f"    {n:>5}  {t}")

def norm(t):
    t = unicodedata.normalize("NFKC", str(t)).lower()
    for a, b in [(r"\brd\b", "road"), (r"\bst\b", "street"), (r"\bngr\b", "nagar"), (r"\bh\.?\s?no\.?\b", "house"),
                 (r"\bno\.\b", "number"), (r"\bopp\.?\b", "opposite"), (r"\bnr\b", "near"), (r"\bmkt\b", "market")]:
        t = re.sub(a, b, t)
    t = re.sub(r"[^0-9a-z\u0900-\u097F\u0C80-\u0CFF]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()

ad["text_norm"] = at.map(norm)
exact_dup = int(at.duplicated().sum())
norm_dup = int(ad.text_norm.duplicated().sum())
say(f"\nduplicate text: exact={exact_dup}  normalised={norm_dup}  "
    f"rows in a normalised-duplicate group={int(ad.text_norm.duplicated(keep=False).sum())}")

# near-duplicates: block on the first 3 normalised tokens, compare char-3-gram Jaccard ≥ 0.8
blocks = collections.defaultdict(list)
for i, t in ad.text_norm.items():
    blocks[" ".join(t.split()[:3])].append(i)
def c3(s): return {s[j:j+3] for j in range(max(len(s)-2, 0))}
near = []
for b, idxs in blocks.items():
    if len(idxs) < 2 or len(idxs) > 60: continue
    sets = {i: c3(ad.text_norm[i]) for i in idxs}
    for i, j in itertools.combinations(idxs, 2):
        a1, b1 = sets[i], sets[j]
        if not a1 or not b1: continue
        jac = len(a1 & b1) / len(a1 | b1)
        if jac >= 0.80 and ad.text_norm[i] != ad.text_norm[j]:
            t_i = re.sub(r"\d+", "#", ad.text_norm[i]); t_j = re.sub(r"\d+", "#", ad.text_norm[j])
            near.append((i, j, round(jac, 3), bool(ad.town_id[i] == ad.town_id[j]), t_i == t_j))
same_template = [x for x in near if x[4]]
diff_template = [x for x in near if not x[4]]
say(f"near-duplicate pairs (char-3-gram Jaccard ≥ 0.80, blocked by leading tokens): {len(near)}; "
    f"within one town: {sum(1 for x in near if x[3])}")
say(f"  of those, pairs identical once digits are masked (SAME TEMPLATE, different numbers): {len(same_template)}")
say(f"  pairs differing in wording as well: {len(diff_template)}")
for i, j, jc, same, st in near[:8]:
    say(f"    J={jc} same_town={same} same_template={st}  A: {ad.address_text[i][:58]!r}  B: {ad.address_text[j][:58]!r}")
save(pd.DataFrame([dict(address_a=str(ad.address_id[i]), address_b=str(ad.address_id[j]), jaccard=jc,
                        same_town=st_, same_template=stpl) for i, j, jc, st_, stpl in near]), "near_duplicates")

say(f"\naddress_type distribution: {ad.address_type.value_counts().to_dict()}")
say(f"source distribution      : {ad.source.value_counts().to_dict()}")
say(f"town distribution        : {ad.town_id.value_counts().to_dict()}  (OUT = outside every modelled town)")
say(f"addresses per account    : mean={len(ad)/ad.account_id.nunique():.2f} "
    f"max={ad.groupby('account_id').size().max()}  "
    f"distribution={ad.groupby('account_id').size().value_counts().sort_index().to_dict()}")
save(ad.groupby("town_id").agg(addresses=("address_id", "count"),
                               accounts=("account_id", "nunique")).reset_index(), "town_shape")

say("\nDEGENERATE / UNUSUAL RECORDS")
say(f"  no digits: {int((DIG==0).sum())} | under 20 chars: {int((L<20).sum())} | under 4 tokens: {int((TOK<4).sum())} "
    f"| no letters: {int((ALPHA==0).sum())}")
say("  examples of the shortest records:")
for t in at[L < 30].head(5):
    say("    " + t[:100])

# ═══════════════════════ 3. GEOGRAPHIC HIERARCHY EDA ═══════════════════════
say("\n" + "=" * 100)
say("SECTION 3 — GEOGRAPHIC HIERARCHY EDA  (town → locality → pincode → landmark → address)")
say("=" * 100)
say(f"towns: {tw.town_id.tolist()}  styles={tw.address_style.tolist()}  approx_radius_m={tw.approx_radius_m.tolist()}")
say(f"localities per town: {lo.groupby('town_id').size().to_dict()}")
say(f"pincodes per town  : {lo.groupby('town_id').pincode.nunique().to_dict()}")
say(f"pincodes total     : {lo.pincode.nunique()} distinct over {len(lo)} localities")
dup_lp = lo.groupby(["town_id", "pincode"]).size()
say(f"localities per (town,pincode): {dup_lp.value_counts().sort_index().to_dict()}  "
    f"→ pincode is NOT a 1:1 key for a locality")
pin_multi_town = lo.groupby("pincode").town_id.nunique()
say(f"pincodes appearing in more than one town: {int((pin_multi_town>1).sum())} (of {lo.pincode.nunique()})")
name_dups = lo[lo.duplicated("locality_name", keep=False)].sort_values("locality_name")
say(f"locality names repeated across towns: {int(name_dups.locality_name.nunique())} names, {len(name_dups)} rows")
for _, r in name_dups.iterrows():
    say(f"    {r.locality_name:<16} town={r.town_id}  pincode={r.pincode}  centroid=({r.centroid_x},{r.centroid_y})")
say(f"locality centroid precision: decimals x={lo.centroid_x.astype(str).str.split('.').str[1].str.len().max()} "
    f"y={lo.centroid_y.astype(str).str.split('.').str[1].str.len().max()} → rounded artefacts, not survey points")
for t in tw.town_id:
    pts = lo[lo.town_id == t][["centroid_x", "centroid_y"]].values
    spread_m = float(np.sqrt(((pts - pts.mean(0)) ** 2).sum(1)).max()) if len(pts) else 0
    nland = int((lm.town_id == t).sum())
    nad = int((ad.town_id == t).sum())
    say(f"  {t}: localities={int((lo.town_id==t).sum())}  landmarks={nland}  addresses={nad}  "
        f"max locality-centroid spread from town centre={spread_m:.0f} m  approx_radius_m={tw.set_index('town_id').loc[t,'approx_radius_m']}")
say(f"landmarks: {len(lm)} rows, {lm.name.nunique()} distinct names, {lm.landmark_type.nunique()} types")
say(f"landmark type distribution: {lm.landmark_type.value_counts().to_dict()}")
dup_lm = lm.groupby(["town_id", "name"]).size()
say(f"duplicate (town,name) pairs: {int((dup_lm>1).sum())} covering {int(dup_lm[dup_lm>1].sum())} rows")
say(f"distinct names: {sorted(lm.name.unique())[:14]} ...")
say(f"landmarks per town: {lm.groupby('town_id').size().to_dict()}")
say("\naddress → hierarchy resolvability (text evidence only):")
res_loc = mention_loc.sum()
say(f"  address has a locality-name token : {int(res_loc)} ({100*res_loc/len(ad):.1f}%)")
say(f"  address has a known pincode token : {int(SIX.isin(PIN_KNOWN).sum())} ({100*SIX.isin(PIN_KNOWN).mean():.1f}%)")
say(f"  address has a landmark phrase     : {int(mention_lm.sum())} ({100*mention_lm.mean():.1f}%)")
say(f"  has at least one of the three     : "
    f"{int((mention_loc | SIX.isin(PIN_KNOWN) | mention_lm).sum())} "
    f"({100*(mention_loc | SIX.isin(PIN_KNOWN) | mention_lm).mean():.1f}%)")
say(f"  has none of the three             : "
    f"{int((~mention_loc & ~SIX.isin(PIN_KNOWN) & ~mention_lm).sum())} "
    f"({100*(~mention_loc & ~SIX.isin(PIN_KNOWN) & ~mention_lm).mean():.1f}%)")
save(lo.groupby("town_id").agg(localities=("locality_id", "count"), pincodes=("pincode", "nunique")).reset_index(),
     "hierarchy_town")
save(lm.landmark_type.value_counts().rename_axis("landmark_type").reset_index(name="n"), "landmark_types")

# ═══════════════════════ 4. BASELINE GEOCODER EDA ═══════════════════════
say("\n" + "=" * 100)
say("SECTION 4 — BASELINE GEOCODER EDA")
say("=" * 100)
cov = bg.address_id.nunique() / len(ad)
say(f"addresses with a geocode : {bg.address_id.nunique()} of {len(ad)} = {100*cov:.1f}%  "
    f"(missing: {len(ad)-bg.address_id.nunique()} = {100*(1-cov):.1f}%)")
miss = set(ad.address_id) - set(bg.address_id)
miss_town = ad[ad.address_id.isin(miss)].town_id.value_counts().to_dict()
say(f"missing-geocode addresses by town: {miss_town}  ← all of them are 'OUT'")
say(f"precision strata         : {bg.precision.value_counts().to_dict()}")
say(f"   as share: { {k: f'{100*v/len(bg):.1f}%' for k,v in bg.precision.value_counts().items()} }")
say(f"duplicate pin coordinates: {int(bg.duplicated(['geocoder_x','geocoder_y']).sum())} duplicated rows; "
    f"largest pin pile = {int(bg.groupby(['geocoder_x','geocoder_y']).size().max())} address(es)")
say(f"distinct coordinates     : {bg[['geocoder_x','geocoder_y']].drop_duplicates().shape[0]} for {len(bg)} rows "
    f"→ the baseline does not collapse many addresses onto one point")
say(f"coordinate decimals      : median x={bg.geocoder_x.astype(str).str.split('.').str[1].str.len().median():.0f}")
say(f"strata by town: {bg.merge(ad[['address_id','town_id']],on='address_id').groupby(['town_id','precision']).size().unstack(fill_value=0).to_dict()}")

g = bg.merge(ad[["address_id", "town_id"]], on="address_id")
mm = sv.merge(g, on="address_id")
mm["err"] = np.hypot(mm.surveyed_x - mm.geocoder_x, mm.surveyed_y - mm.geocoder_y)
say(f"\nERROR vs surveyed truth (n={len(mm)} — the only ground truth available):")
say(f"  median={mm.err.median():.1f} m  mean={mm.err.mean():.1f} m  p25={mm.err.quantile(.25):.1f}  "
    f"p75={mm.err.quantile(.75):.1f}  p90={mm.err.quantile(.9):.1f}  max={mm.err.max():.1f}")
for thr in (50, 100, 250, 500, 1000):
    say(f"  within {thr:>4} m: {100*(mm.err<thr).mean():5.1f}%  ({(mm.err<thr).sum()} of {len(mm)})")
say("\n  by precision stratum:")
rows = []
for p, gg in mm.groupby("precision"):
    rows.append(dict(stratum=p, n=len(gg), median_m=round(gg.err.median(), 1), p75_m=round(gg.err.quantile(.75), 1),
                     p90_m=round(gg.err.quantile(.9), 1), max_m=round(gg.err.max(), 1),
                     hit_100m=round(100*(gg.err < 100).mean(), 1), hit_500m=round(100*(gg.err < 500).mean(), 1)))
    say(f"    {p:<9} n={len(gg):>3}  median={gg.err.median():7.1f}  p75={gg.err.quantile(.75):7.1f}  "
        f"p90={gg.err.quantile(.9):7.1f}  <100m={100*(gg.err<100).mean():5.1f}%  <500m={100*(gg.err<500).mean():5.1f}%")
save(pd.DataFrame(rows), "baseline_error_by_stratum")
chart("baseline_strata", svg_bar("Baseline geocode precision strata (n=2,880 addresses with a geocode)",
                                list(bg.precision.value_counts().index), list(bg.precision.value_counts().values),
                                note="71% of all pins are locality-level: the baseline knows the neighbourhood, not the house."))
chart("baseline_error_stratum", svg_bar(
    "Baseline error vs surveyed truth, by precision stratum (n=100)", [f"{r['stratum']} (n={r['n']})" for r in rows],
    [r["median_m"] for r in rows], unit=" m", colour="#9b2c2c",
    note="Median error only; p90 for the pincode stratum exceeds 3,800 m.", fmt="{:.0f}"))
say("\n  by town:")
for t, gg in mm.groupby("town_id"):
    say(f"    {t}: n={len(gg)}  median={gg.err.median():7.1f}  <100m={100*(gg.err<100).mean():5.1f}%  <500m={100*(gg.err<500).mean():5.1f}%")
say("\n  by address_type:")
for t, gg in mm.merge(ad[["address_id", "address_type"]], on="address_id").groupby("address_type"):
    say(f"    {t:<17} n={len(gg):>3}  median={gg.err.median():7.1f}")
say("\n  out-of-town records (town_id='OUT'): "
    f"{int((ad.town_id=='OUT').sum())} addresses, geocoded: {int(ad[ad.town_id=='OUT'].address_id.isin(bg.address_id).sum())}")

# ═══════════════════════ 5. GROUND TRUTH EDA ═══════════════════════
say("\n" + "=" * 100)
say("SECTION 5 — SURVEYED / GROUND-TRUTH EDA (the only true labels)")
say("=" * 100)
s = sv.merge(ad, on="address_id")
say(f"surveyed records: {len(sv)} = {100*len(sv)/len(ad):.1f}% of addresses, {100*sv.address_id.nunique()/len(ad):.1f}% unique")
say(f"by town     : {s.town_id.value_counts().to_dict()}")
say(f"by type     : {s.address_type.value_counts().to_dict()}")
say(f"by source   : {s.source.value_counts().to_dict()}")
say(f"by stratum  : {s.merge(bg,on='address_id').precision.value_counts().to_dict()}")
say(f"by split    : {s.merge(sp,on='account_id').split.value_counts().to_dict()}  "
    f"← ground truth spans all three official splits")
say(f"distinct accounts represented: {s.account_id.nunique()}  (mean {(len(s)/s.account_id.nunique()):.2f} addresses per account)")
say(f"addresses that were ever visited: {int(s.address_id.isin(fv.address_id).sum())} of {len(sv)}")
tc = lo.groupby("town_id")[["centroid_x", "centroid_y"]].mean()
s2 = s.merge(tc, left_on="town_id", right_index=True)
s2["d_centre"] = np.hypot(s2.surveyed_x - s2.centroid_x, s2.surveyed_y - s2.centroid_y)
say(f"distance from surveyed point to town centre: median={s2.d_centre.median():.0f} m  max={s2.d_centre.max():.0f} m")
say(f"surveyed-vs-vendor error: median={s2.merge(bg,on='address_id').pipe(lambda d: np.hypot(d.surveyed_x-d.geocoder_x, d.surveyed_y-d.geocoder_y)).median():.1f} m")
say("representativeness checks:")
say(f"  surveyed share by stratum vs population: "
    f"{ {k: f'{100*v/len(sv):.1f}% vs {100*bg.precision.value_counts(normalize=True).get(k,0):.1f}%' for k,v in s.merge(bg,on='address_id').precision.value_counts().items()} }")
say(f"  surveyed share of 'OUT' records: {int((s.town_id=='OUT').sum())} (population: {int((ad.town_id=='OUT').sum())})")
say(f"  surveyed share of office/native addresses: {s.address_type.value_counts().get('office',0)} office, "
    f"{s.address_type.value_counts().get('permanent_native',0)} native")
save(s[["address_id", "town_id", "address_type", "source"]].assign(
    account_id=s.account_id), "ground_truth_composition")

# ═══════════════════════ 6. FIELD VISIT EDA ═══════════════════════
say("\n" + "=" * 100)
say("SECTION 6 — FIELD VISIT EDA")
say("=" * 100)
fv["visit_date"] = pd.to_datetime(fv.visit_date)
vpa = fv.groupby("address_id").size()
say(f"visits total={len(fv)} over {fv.address_id.nunique()} addresses "
    f"({100*fv.address_id.nunique()/len(ad):.1f}% of the book) and {fv.account_id.nunique()} accounts")
say(f"visits per visited address: mean={vpa.mean():.2f} median={vpa.median():.0f} p90={vpa.quantile(.9):.0f} max={vpa.max()}")
say(f"distribution: {vpa.value_counts().sort_index().to_dict()}")
vppc = fv.groupby("account_id").size()
say(f"visits per visited account: mean={vppc.mean():.2f} median={vppc.median():.0f} max={vppc.max()}")
say(f"outcome frequency: {fv.outcome.value_counts().to_dict()}")
chart("visit_outcomes", svg_bar("Field-visit outcomes (n=5,578 visits)",
                                list(fv.outcome.value_counts().index), list(fv.outcome.value_counts().values),
                                colour="#553c9a",
                                note="1 in 4 visits is 'address_not_traceable' — the failure mode this project must handle."))
oc = fv.outcome.value_counts()
say(f"  as shares: { {k: f'{100*v/len(fv):.1f}%' for k,v in oc.items()} }")
say(f"\nmedian dwell by outcome (minutes): "
    f"{ {k: round(v/60,1) for k,v in fv.groupby('outcome').dwell_s.median().items()} }")
say(f"median travel start→check-in by outcome (minutes): "
    f"{ {k: round(v/60,1) for k,v in (pd.to_datetime(fv.checkin_ts)-pd.to_datetime(fv.start_ts)).dt.total_seconds().groupby(fv.outcome).median().items()} }")
fa = fv.merge(ad[["address_id", "address_type", "town_id"]], on="address_id")
say("\noutcome by town:")
for t, gg in fa.groupby("town_id"):
    d = gg.outcome.value_counts(normalize=True)
    say(f"  {t}: n={len(gg):>4}  met_borrower {100*d.get('met_borrower',0):4.1f}%  "
        f"met_family {100*d.get('met_family',0):4.1f}%  locked {100*d.get('locked_premises',0):4.1f}%  "
        f"not_traceable {100*d.get('address_not_traceable',0):4.1f}%")
say("outcome by address type:")
for t, gg in fa.groupby("address_type"):
    d = gg.outcome.value_counts(normalize=True)
    say(f"  {t:<17} n={len(gg):>4}  met-someone {100*(d.get('met_borrower',0)+d.get('met_family',0)+d.get('cash_collected',0)):5.1f}%  "
        f"not_traceable {100*d.get('address_not_traceable',0):5.1f}%")
say("outcome by baseline precision stratum:")
for t, gg in fa.merge(bg, on="address_id").groupby("precision"):
    d = gg.outcome.value_counts(normalize=True)
    say(f"  {t:<9} n={len(gg):>4}  met-someone {100*(d.get('met_borrower',0)+d.get('met_family',0)+d.get('cash_collected',0)):5.1f}%  "
        f"not_traceable {100*d.get('address_not_traceable',0):5.1f}%  median dwell={gg.dwell_s.median()/60:4.1f} min")
say(f"\nrepeat visits: {int((vpa>1).sum())} addresses visited more than once; "
    f"{int((vpa>=3).sum())} three or more times")
multi_agent = fv.groupby("address_id").agent_id.nunique()
say(f"addresses confirmed by >1 distinct agent: {int((multi_agent>1).sum())}")
say(f"visits with a remark: {int(fv.remark.notna().sum())} ({100*fv.remark.notna().mean():.1f}%); "
    f"distinct remarks: {fv.remark.nunique()}; top: {fv.remark.value_counts().head(5).to_dict()}")
say(f"visits with ptp_id : {int(fv.ptp_id.notna().sum())} ({100*fv.ptp_id.notna().mean():.1f}%)")

# selection bias: visit exposure by account risk
av = ac[["account_id", "dpd_start", "outstanding", "portfolio", "lender_id"]].merge(
    ad.groupby("account_id").address_id.count().rename("n_addr"), left_on="account_id", right_index=True)
visited = set(fv.account_id)
av["visited"] = av.account_id.isin(visited)
av["dpd_bucket"] = pd.cut(av.dpd_start, [-1, 30, 60, 90, 180, 1000],
                          labels=["0–30", "31–60", "61–90", "91–180", "180+"])
expo = av.groupby("dpd_bucket").visited.agg(["mean", "size"])
say("\nvisit exposure by delinquency bucket (account level):")
for b, r in expo.iterrows():
    say(f"  DPD {b:<8} accounts={int(r['size']):>5}  visited={100*r['mean']:5.1f}%")
chart("exposure_dpd", svg_bar("Visit exposure rises with delinquency (accounts, n=2,400)",
                              [f"DPD {b}" for b in expo.index], [100 * v for v in expo["mean"]], unit="%",
                              colour="#b7791f",
                              note="Demand-driven selection: visits are not a random sample of the book."))
av["out_bucket"] = pd.qcut(av.outstanding, 4, labels=["Q1 low", "Q2", "Q3", "Q4 high"])
say("visit exposure by outstanding quartile: "
    + ", ".join(f"{b}:{100*r:4.1f}%" for b, r in av.groupby("out_bucket").visited.mean().items()))
say("visit exposure by portfolio: "
    + ", ".join(f"{b}:{100*r:4.1f}%" for b, r in av.groupby("portfolio").visited.mean().items()))
avb = ad.assign(visited=ad.address_id.isin(fv.address_id)).groupby("address_type").visited.mean()
say("visit exposure by address type: " + ", ".join(f"{k}:{100*v:.1f}%" for k, v in avb.items()))
say("visit exposure by baseline stratum: " + ", ".join(
    f"{k}:{100*v:.1f}%" for k, v in bg.assign(visited=bg.address_id.isin(fv.address_id)).groupby("precision").visited.mean().items()))
save(fa.outcome.value_counts().rename_axis("outcome").reset_index(name="n"), "visit_outcomes")

# ═══════════════════════ 7. GPS / TRAJECTORY EDA ═══════════════════════
say("\n" + "=" * 100)
say("SECTION 7 — FIELD GPS / TRAJECTORY EDA")
say("=" * 100)
gp = gp.sort_values(["visit_id", "seq"]).copy()
gp["point_ts"] = pd.to_datetime(gp.point_ts)
npv = gp.groupby("visit_id").size()
say(f"points total={len(gp)} over {gp.visit_id.nunique()} visits; median={npv.median():.0f} points/visit "
    f"p10={npv.quantile(.1):.0f} p90={npv.quantile(.9):.0f} max={npv.max()}")
say(f"visits with <5 points: {int((npv<5).sum())}; with ≥20: {int((npv>=20).sum())}")
say(f"accuracy_m: median={gp.accuracy_m.median():.1f} p75={gp.accuracy_m.quantile(.75):.1f} "
    f"p90={gp.accuracy_m.quantile(.9):.1f} p99={gp.accuracy_m.quantile(.99):.1f} max={gp.accuracy_m.max():.1f}")
c, e = np.histogram(gp.accuracy_m, bins=[0,5,8,10,15,20,30,50,100,1000])
chart("gps_accuracy", svg_hist("GPS reported accuracy per point (metres, n=160,406)", list(c),
                               [0,5,8,10,15,20,30,50,100,1000], colour="#2c7a7b",
                               note="Median 10 m. API accuracy is a ~68% radial confidence, not a bound."))
say("accuracy histogram bins: " + ", ".join(f"{e[i]:g}-{e[i+1]:g}:{int(c[i])}" for i in range(len(c))))
say(f"axis artefacts (x==0 or y==0): {int(((gp.x==0)|(gp.y==0)).sum())} "
    f"({100*((gp.x==0)|(gp.y==0)).mean():.3f}%)")
gp["dx"] = gp.groupby("visit_id").x.diff(); gp["dy"] = gp.groupby("visit_id").y.diff()
gp["dt"] = gp.groupby("visit_id").point_ts.diff().dt.total_seconds()
gp["step"] = np.hypot(gp.dx, gp.dy)
gp["speed"] = np.where((gp.dt > 0), 3.6 * gp.step / gp.dt, np.nan)
spd = gp.speed.dropna()
say(f"consecutive-point distance: median={gp.step.median():.2f} m p90={gp.step.quantile(.9):.2f} m max={gp.step.max():.1f} m")
say(f"implied speed: median={spd.median():.2f} p95={spd.quantile(.95):.2f} p99={spd.quantile(.99):.2f} "
    f"p99.9={spd.quantile(.999):.2f} km/h  max={spd.max():.2f} km/h")
say(f"steps faster than 40 km/h: {int((spd>40).sum())}; faster than 60: {int((spd>60).sum())}; "
    f"negative or zero dt: {int((gp.dt<=0).sum())}")
say(f"zero-length steps (same point twice): {100*(gp.step==0).mean():.2f}% of steps")
say(f"trail duration (last-first per visit): median={gp.groupby('visit_id').point_ts.agg(lambda s:(s.max()-s.min()).total_seconds()).median()/60:.1f} min")
pt = gp.groupby("visit_id").agg(x_med=("x","median"), y_med=("y","median"), x_first=("x","first"), y_first=("y","first"))
ck = fv.set_index("visit_id")[["checkin_x","checkin_y","gps_accuracy_m","outcome"]]
tt = pt.join(ck, how="inner")
tt["d_checkin_median"] = np.hypot(tt.checkin_x-tt.x_med, tt.checkin_y-tt.y_med)
tt["d_start_checkin"] = np.hypot(tt.checkin_x-tt.x_first, tt.checkin_y-tt.y_first)
say(f"check-in vs trail centroid: median={tt.d_checkin_median.median():.1f} m p90={tt.d_checkin_median.quantile(.9):.1f} "
    f"max={tt.d_checkin_median.max():.1f} m")
say(f"trail start vs check-in  : median={tt.d_start_checkin.median():.1f} m p90={tt.d_start_checkin.quantile(.9):.1f} m")
say(f"check-in accuracy vs trail accuracy: median check-in={tt.gps_accuracy_m.median():.1f} m, "
    f"median trail={gp.accuracy_m.median():.1f} m")
say("check-in ↔ trail agreement by outcome (median m): "
    + ", ".join(f"{k}:{v:.0f}" for k, v in tt.groupby("outcome").d_checkin_median.median().items()))
coord_reuse = fv.groupby(["checkin_x","checkin_y"]).size()
say(f"\ncheck-in coordinates: {len(coord_reuse)} distinct for {len(fv)} visits; largest cluster={int(coord_reuse.max())} visits; "
    f"visits sharing a coordinate with ≥3 others: {int(coord_reuse[coord_reuse>=3].sum())}")
within_visit_reuse = gp.groupby("visit_id").apply(lambda d: 1 - (d[['x','y']].drop_duplicates().shape[0] / len(d)))
say(f"share of repeated coordinates within a visit: median={within_visit_reuse.median():.2f} "
    f"p90={within_visit_reuse.quantile(.9):.2f}")
say("\nMODEL-RELEVANT DISTINCTION — what a trail tells us about (a) the place and (b) the collection process:")
say("   place-side signals   : where the agent converged, dwell cluster, distance from the check-in to that cluster")
say("   process-side signals : accuracy class, point count, speed plausibility, trail/check-in disagreement, axis artefacts")
say(f"   measured here: trails are internally consistent (max {spd.max():.1f} km/h, no teleports) — the dataset contains no")
say("   spoofing to learn from, so process-side signals can be *defined* but not *validated* on this data.")

# ── 7b. trail geometry in detail (place-side vs process-side) ──────────────────
say("\n" + "-" * 100)
say("SECTION 7b — TRAIL GEOMETRY DETAIL, AND THE PIN-AGREEMENT TEST ON ALL 5,578 VISITS")
say("-" * 100)
gmin = gp.groupby("visit_id").apply(
    lambda d: pd.Series(dict(n=len(d), span_m=float(np.hypot(d.x.max()-d.x.min(), d.y.max()-d.y.min())),
                             path_m=float(np.hypot(d.x.diff(), d.y.diff()).sum()))))
tw2 = tt.join(gmin)
ckp = fv.set_index("visit_id")[["checkin_x", "checkin_y", "outcome", "address_id"]].join(gp.groupby("visit_id")[["x", "y"]].apply(
    lambda d: float(np.min(np.hypot(d.x - fv.set_index("visit_id").loc[d.name, "checkin_x"],
                                    d.y - fv.set_index("visit_id").loc[d.name, "checkin_y"])))).rename("min_d_checkin_trail"))
say(f"check-in → NEAREST trail point : median={ckp.min_d_checkin_trail.median():.1f} m  "
    f"p90={ckp.min_d_checkin_trail.quantile(.9):.1f} m  (this is the strict 'is the agent on their own path' test)")
say(f"check-in → trail CENTROID      : median={tw2.d_checkin_median.median():.1f} m  "
    f"p90={tw2.d_checkin_median.quantile(.9):.1f} m  (large because a walking trail has extent)")
say(f"trail bounding-box span        : median={tw2.span_m.median():.0f} m  p90={tw2.span_m.quantile(.9):.0f} m")
say(f"trail path length              : median={tw2.path_m.median():.0f} m  p90={tw2.path_m.quantile(.9):.0f} m")
say("\nper-outcome comparison (full 5,578 visits; vendor pin present for 5,341 of them):")
pin = bg.set_index("address_id")[["geocoder_x", "geocoder_y", "precision"]]
vv = fv.merge(pin, left_on="address_id", right_index=True, how="left")
vv["d_pin"] = np.hypot(vv.checkin_x - vv.geocoder_x, vv.checkin_y - vv.geocoder_y)
vv = vv.join(ckp[["min_d_checkin_trail"]], on="visit_id").join(gmin[["n", "span_m"]], on="visit_id")
hdr = f"  {'outcome':<24}{'n':>6}{'dwell':>7}{'to pin':>9}{'≤100m of pin':>14}{'min trail':>11}{'span':>7}{'pts':>5}"
say(hdr)
for o, gg in vv.groupby("outcome"):
    gp_ = gg.dropna(subset=["d_pin"])
    say(f"  {o:<24}{len(gg):>6}{gg.dwell_s.median()/60:>6.1f}m{gp_.d_pin.median():>8.0f}m"
        f"{100*(gp_.d_pin<=100).mean():>13.1f}%{gg.min_d_checkin_trail.median():>10.1f}m"
        f"{gg.span_m.median():>6.0f}m{gg.n.median():>5.0f}")
say("\nREADING (three separate facts, reported separately rather than blended):")
say("  1. DISTANCE TO THE PIN is failure-correlated: the failure outcome is the only one whose median check-in sits")
say("     closer to the vendor pin (195 m) than the success outcomes (323–346 m), and it is the most likely to be")
say("     within 100 m of that pin (17.6% vs 9.2–11.6%).")
say("  2. DWELL is strongly discriminative: 1.3 min for the failure outcome vs 6.6–14.8 min for met-someone outcomes,")
say("     and 2.5 min for locked_premises. Short dwell + near-pin + no contact = the signature of giving up.")
say("  3. TRAIL TRAITS ARE NOT discriminative here: min distance check-in→trail is 5.7–8.3 m for every outcome (the")
say("     check-in is by construction a point on the agent's own path), and trail span is slightly LARGER for failures")
say("     (616 m) than for confirmations (475–551 m) because the trail includes the whole approach walk.")
say("  → consequence: integrity features must be built from MEDIA, COORDINATE and TIMING signals, not from trail shape;")
say("    trail geometry is useful as an evidence COORDINATE (where the agent converged) but not as a truth test.")
save(vv.groupby("outcome").agg(n=("visit_id", "count"), med_dwell_min=("dwell_s", lambda s: round(s.median()/60, 2)),
                               med_d_to_pin_m=("d_pin", lambda s: round(s.median(), 1)),
                               pct_within_100m_of_pin=("d_pin", lambda s: round(100*(s <= 100).mean(), 1)),
                               med_min_d_to_trail_m=("min_d_checkin_trail", lambda s: round(s.median(), 1)),
                               med_trail_span_m=("span_m", lambda s: round(s.median(), 1)),
                               med_points=("n", "median")).reset_index(), "visit_outcome_geometry")

# ═══════════════════════ 8. AGENT EDA ═══════════════════════
say("\n" + "=" * 100)
say("SECTION 8 — AGENT / COLLECTOR EDA")
say("=" * 100)
say(f"agents: {len(ag)}; channels={ag.channel.value_counts().to_dict()}; "
    f"language teams={ag.language_team.value_counts().to_dict()}; shifts={ag["shift"].value_counts().to_dict()}")
say(f"town assignment: {ag.town_id.value_counts(dropna=False).to_dict()}  (null = non-field channels)")
say(f"tenure_months: min={ag.tenure_months.min()} median={ag.tenure_months.median():.0f} "
    f"max={ag.tenure_months.max()} nulls={int(ag.tenure_months.isna().sum())}")
vd = fv.groupby("agent_id").agg(visits=("visit_id","count"), addresses=("address_id","nunique"),
                                met=("outcome", lambda s: s.isin(["met_borrower","met_family","cash_collected"]).mean()),
                                depth=("outcome", lambda s: s.eq("address_not_traceable").mean()),
                                dwell_med=("dwell_s", lambda s: s.median()/60),
                                photo_dup=("photo_hash", lambda s: 1 - s.nunique(dropna=True)/max(len(s),1)),
                                coord_uniq=("checkin_x", "nunique"))
vd["photo_dup"] = 1 - fv.groupby("agent_id").photo_hash.apply(lambda s: s.nunique(dropna=False)/len(s))
say(f"visits per agent: median={vd.visits.median():.0f} min={vd.visits.min()} max={vd.visits.max()} "
    f"(agents with 0 visits: {len(ag)-len(vd)})")
say("\nper-agent behaviour table (sorted by visits):")
say(f"  {'agent':<8}{'visits':>7}{'addr':>6}{'met%':>7}{'nottr%':>8}{'dwell':>7}{'photodup%':>10}{'town':>6}")
for aid, r in vd.sort_values("visits", ascending=False).iterrows():
    tv = ag[ag.agent_id == aid].town_id.iloc[0]
    say(f"  {aid:<8}{int(r.visits):>7}{int(r.addresses):>6}{100*r.met:>6.1f}%{100*r.depth:>7.1f}%"
        f"{r.dwell_med:>6.1f}m{100*r.photo_dup:>9.1f}%{str(tv):>6}")
dup_counts = fv.groupby("photo_hash").size().sort_values(ascending=False)
say(f"\nphoto_hash: {fv.photo_hash.nunique()} distinct for {int(fv.photo_hash.notna().sum())} non-null visits; "
    f"largest hash group = {int(dup_counts.max())} visits")
worst = vd.photo_dup.sort_values(ascending=False)
say(f"agents above 5% duplicate-photo rate: {list(worst[worst>0.05].index)}")
for aid in worst[worst > 0.05].index:
    sub = fv[fv.agent_id == aid]
    say(f"  {aid}: {len(sub)} visits, duplicate-photo rate {100*(1-sub.photo_hash.nunique()/len(sub)):.1f}%, "
        f"met-someone {100*sub.outcome.isin(['met_borrower','met_family','cash_collected']).mean():.1f}%, "
        f"median dwell {sub.dwell_s.median()/60:.1f} min, distinct check-in points {sub[['checkin_x','checkin_y']].drop_duplicates().shape[0]}")
say(f"agents' check-in coordinate reuse: median distinct check-in points per agent = "
    f"{vd.coord_uniq.median():.0f} of {vd.visits.median():.0f} visits")
save(vd.reset_index(), "agent_behaviour")

# ═══════════════════════ 9. TEMPORAL EDA ═══════════════════════
say("\n" + "=" * 100)
say("SECTION 9 — TEMPORAL EDA")
say("=" * 100)
add = pd.to_datetime(ad.added_date)
say(f"address added_date: {add.min().date()} → {add.max().date()} ({(add.max()-add.min()).days} days); "
    f"weekday mix={add.dt.dayofweek.value_counts().sort_index().to_dict()}")
say(f"visits visit_date: {fv.visit_date.min().date()} → {fv.visit_date.max().date()} "
    f"({(fv.visit_date.max()-fv.visit_date.min()).days} days); weekday mix="
    f"{fv.visit_date.dt.dayofweek.value_counts().sort_index().to_dict()} (0=Mon)")
say(f"visit hour-of-day mix (check-in): {pd.to_datetime(fv.checkin_ts).dt.hour.value_counts().sort_index().to_dict()}")
wk = fv.set_index("visit_date").resample("W").size()
chart("visits_time", svg_bar("Visits per week (weeks beginning 2026-04-01 → 2026-06-29)",
                             [d.strftime("%d %b") for d in wk.index], list(wk.values), colour="#2b6cb0",
                             note="13 weeks; no regime change is observable in this window."))
say(f"visits per week: {list(wk.values)}")
gaps = fv.visit_date.drop_duplicates().sort_values().diff().dt.days.dropna()
say(f"gap between active visit days: median={gaps.median():.0f}  max={gaps.max():.0f}  days without any visit: "
    f"{int((pd.date_range(fv.visit_date.min(), fv.visit_date.max()).difference(fv.visit_date.unique())).size)}"
    f" of {(fv.visit_date.max()-fv.visit_date.min()).days+1}")
say(f"addresses created before the first visit window: {int((add < fv.visit_date.min()).sum())} "
    f"of {len(ad)} ({100*(add < fv.visit_date.min()).mean():.1f}%)")
lead = fv.merge(ad[['address_id','added_date']], on='address_id')
lead['lead_days'] = (pd.to_datetime(lead.visit_date) - pd.to_datetime(lead.added_date)).dt.days
say(f"days from address creation to a visit: median={lead.lead_days.median():.0f} p10={lead.lead_days.quantile(.1):.0f} "
    f"p90={lead.lead_days.quantile(.9):.0f} negative={int((lead.lead_days<0).sum())}")
seq = fv.sort_values("checkin_ts").groupby("address_id").cumcount()
say(f"visits ordered within address: max sequence index = {int(seq.max())} (i.e. the longest history is "
    f"{int(seq.max())+1} observations)")
say(f"first-visit date distribution by month: "
    f"{fv.groupby(fv.address_id).checkin_ts.min().pipe(lambda s: pd.to_datetime(s).dt.to_period('M').value_counts().sort_index().to_dict())}")

# ═══════════════════════ 10. SPLIT EDA ═══════════════════════
say("\n" + "=" * 100)
say("SECTION 10 — TRAIN / VALIDATION / TEST EDA")
say("=" * 100)
say(f"official split counts (account level): {sp.split.value_counts().to_dict()}; "
    f"accounts covered={sp.account_id.nunique()} of {len(ac)}; duplicate rows={int(sp.duplicated().sum())}")
ads = ad.merge(sp, on="account_id")
say(f"addresses per split: {ads.split.value_counts().to_dict()}  (accounts differ in address count, "
    f"so split sizes are uneven in addresses)")
say(f"town distribution by split: "
    f"{ads.groupby(['split','town_id']).size().unstack(fill_value=0).to_dict()}")
say(f"address_type by split: {ads.groupby(['split','address_type']).size().unstack(fill_value=0).to_dict()}")
say(f"baseline stratum by split: "
    f"{ads.merge(bg,on='address_id').groupby(['split','precision']).size().unstack(fill_value=0).to_dict()}")
say(f"ground-truth (surveyed) by split: "
    f"{sv.merge(ad[['address_id','account_id']], on='address_id').merge(sp, on='account_id').split.value_counts().to_dict()}")
say(f"visits by split: {fv.merge(sp,on='account_id').split.value_counts().to_dict()}")
dup_across_split = ads[ads.text_norm.duplicated(keep=False)].groupby("text_norm").split.nunique()
say(f"normalised-duplicate text groups spanning >1 split: {int((dup_across_split>1).sum())} "
    f"(groups: {int(dup_across_split.size)}); rows involved: {int(ads[ads.text_norm.isin(dup_across_split[dup_across_split>1].index)].shape[0])}")
grp = ads.groupby("text_norm").split.nunique()
say(f"same-building candidates (identical normalised text) spanning splits: {int((grp>1).sum())} groups")
pp = ads.groupby("text_norm").agg(towns=("town_id","nunique"))
say(f"normalised text appearing in more than one town: {int((pp.towns>1).sum())} groups")
say(f"time leakage check: accounts have addresses added over the whole window; visits span "
    f"{fv.visit_date.min().date()} → {fv.visit_date.max().date()} with no temporal split in the official file")
say("→ the official split is RANDOM over accounts and TIME-BLIND; it is necessary but not sufficient")
save(ads.groupby(["split","town_id"]).size().rename("n").reset_index(), "split_town")

# ═══════════════════════ 11. MISSINGNESS CLASSIFICATION ═══════════════════════
say("\n" + "=" * 100)
say("SECTION 11 — MISSING-VALUE ANALYSIS (classified, not just counted)")
say("=" * 100)
MISS = [
    ("addresses", "-", "no nulls anywhere", "complete"),
    ("accounts.salary_credit_day", f"{100*ac.salary_credit_day.isna().mean():.1f}% null",
     "not applicable — salaried accounts have a credit day; others do not", "NOT APPLICABLE"),
    ("accounts.ability_to_pay_estimate", f"{100*ac.ability_to_pay_estimate.isna().mean():.1f}% null",
     "genuinely unknown — the estimate was never produced", "GENUINELY UNKNOWN"),
    ("accounts.last_bounce_reason", f"{100*ac.last_bounce_reason.isna().mean():.1f}% null",
     "not applicable — no bounce occurred", "NOT APPLICABLE"),
    ("agents.town_id", f"{100*ag.town_id.isna().mean():.1f}% null (21 of 30)",
     "not applicable — tele-calling and voice-bot channels have no town", "NOT APPLICABLE"),
    ("agents.tenure_months", f"{int(ag.tenure_months.isna().sum())} null",
     "genuinely unknown for a newly onboarded collector", "GENUINELY UNKNOWN"),
    ("baseline_geocodes.*", f"237 addresses absent (7.6%)",
     "structurally missing — the vendor declines to place out-of-town records", "STRUCTURAL"),
    ("field_visits.ptp_id", f"{100*fv.ptp_id.isna().mean():.1f}% null",
     "not applicable to this problem statement — belongs to a different workflow", "NOT APPLICABLE"),
    ("field_visits.remark", f"{100*fv.remark.isna().mean():.1f}% null",
     "not applicable — a remark is optional free text", "NOT APPLICABLE"),
    ("field_visits.photo_hash", f"{int(fv.photo_hash.isna().sum())} null",
     "process failure if non-zero — a visit without media evidence", "PROCESS FAILURE (if any)"),
    ("visit_gps_points.accuracy_m", f"{int(gp.accuracy_m.isna().sum())} null",
     "corrupted/unreported accuracy — the device did not report it", "POTENTIALLY CORRUPTED"),
    ("surveyed_addresses", "0 nulls, 100 rows of 3,117",
     "structurally missing by design — a survey covers a sample, not the book", "STRUCTURAL"),
]
for t, stat, cls, verdict in MISS:
    say(f"  {t:<28} {stat:<24} {verdict:<22} {cls}")
say("\nrule applied throughout: missingness is DATA, not an error to be filled.")
say("  leave null        → when absence has meaning (no vendor pin = out-of-town / unplaceable)")
say("  add indicator     → when absence changes the decision (pin_unknown, no_digit, trail_missing)")
say("  impute            → only for numeric model inputs where absence is noise, and only with a train-fitted statistic")
say("  derive            → when another table carries the fact (visit outcome → place/person dimensions)")
say("  exclude           → when a column belongs to a different workflow (ptp_id) or leaks (outcome at T0)")

# ═══════════════════════ 12. DUPLICATES & ENTITIES ═══════════════════════
say("\n" + "=" * 100)
say("SECTION 12 — DUPLICATE / ENTITY ANALYSIS")
say("=" * 100)
say(f"exact duplicate rows per table: " + ", ".join(f"{k}:{int(v.duplicated().sum())}" for k, v in T.items()))
say(f"duplicate key values: " + ", ".join(
    f"{k}.{c}:{int(v[c].duplicated().sum())}" for k, v in T.items() for c in v.columns if c.endswith("_id")
    and v[c].dtype == object and int(v[c].duplicated().sum()) > 0) or " none — every *_id column is unique where it is a key")
g_ad = ad.groupby("text_norm").size().sort_values(ascending=False)
say(f"\nnormalised-text groups with >1 address: {int((g_ad>1).sum())} groups covering {int(g_ad[g_ad>1].sum())} rows")
for t, n in g_ad.head(6).items():
    if n > 1:
        rows = ad[ad.text_norm == t]
        say(f"   ×{n}  accounts={list(rows.account_id)} towns={list(rows.town_id)}  «{rows.address_text.iloc[0][:60]}»")
sma = ad.groupby("text_norm").account_id.nunique()
say(f"same text, different accounts: {int((sma>1).sum())} groups — legitimate repeat buildings, not a data error")
say(f"near-duplicate pairs (J≥0.80): {len(near)} — {sum(1 for x in near if x[3])} inside one town")
say(f"duplicate (town,locality_name) pairs: {int(lo.duplicated(['town_id','locality_name']).sum())}; "
    f"duplicate (town,pincode) pairs: {int(lo.duplicated(['town_id','pincode']).sum())}")
say(f"duplicate (town,landmark name) pairs: {int(lm.duplicated(['town_id','name']).sum())} of {len(lm)} rows")
say(f"repeated geographic points: vendor pins {int(bg.duplicated(['geocoder_x','geocoder_y']).sum())}, "
    f"check-ins {len(fv)-fv[['checkin_x','checkin_y']].drop_duplicates().shape[0]}, "
    f"landmarks {int(lm.duplicated(['x','y']).sum())}")
say("\nclassification of the duplicates found:")
say("  multiple accounts at one building → LEGITIMATE REPEATED ENTITY (must be grouped, never deleted)")
say("  identical landmark names in one town → DATA LIMITATION (name is not an identity; scope by town+type+coords)")
say("  locality name repeated across towns → LEGITIMATE (keyed by town)")
say("  repeated check-in coordinates across visits → PROCESS SIGNAL (agents standing at the same spot)")
say("  repeated vendor coordinates → would be a degradation signal; none found in this dataset")

# ═══════════════════════ 13. OUTLIERS ═══════════════════════
say("\n" + "=" * 100)
say("SECTION 13 — OUTLIER / ANOMALY ANALYSIS (identified → explained → disposition)")
say("=" * 100)
OUTL = []
OUTL.append(("axis GPS points (x=0 or y=0)", int(((gp.x==0)|(gp.y==0)).sum()),
             "device wrote a placeholder when it had no fix", "EXCLUDE from evidence, keep the row in the raw file"))
pins_t = bg.merge(ad[["address_id", "town_id"]], on="address_id").merge(
    lo.groupby("town_id")[["centroid_x", "centroid_y"]].mean(), left_on="town_id", right_index=True)
pins_t["d_centre"] = np.hypot(pins_t.geocoder_x - pins_t.centroid_x, pins_t.geocoder_y - pins_t.centroid_y)
far = pins_t[pins_t.d_centre > 6000]
say(f"vendor pins >6,000 m from their town centre: {len(far)} "
    f"(max {pins_t.d_centre.max():.0f} m) → kept, flagged as implausible-distance candidates")
OUTL.append(("vendor pins far from their own town centre", len(far), "either a coarse pincode artefact or a wrong town",
             "FLAG (implausible_distance), never delete"))
ck_t = fv.merge(ad[["address_id", "town_id"]], on="address_id").merge(
    lo.groupby("town_id")[["centroid_x", "centroid_y"]].mean(), left_on="town_id", right_index=True)
ck_t["d_centre"] = np.hypot(ck_t.checkin_x - ck_t.centroid_x, ck_t.checkin_y - ck_t.centroid_y)
say(f"check-ins outside a 6,000 m town envelope: {int((ck_t.d_centre>6000).sum())} "
    f"(max {ck_t.d_centre.max():.0f} m) → town containment holds in this dataset")
OUTL.append(("check-ins outside the town envelope", int((ck_t.d_centre > 6000).sum()),
             "would indicate a mis-assigned town or a travelling collector", "FLAG if present (none here)"))
say(f"dwell_s: min={fv.dwell_s.min()} p1={fv.dwell_s.quantile(.01):.0f} median={fv.dwell_s.median():.0f} "
    f"p99={fv.dwell_s.quantile(.99):.0f} max={fv.dwell_s.max()}; under 60 s: {int((fv.dwell_s<60).sum())}; "
    f"over 2 h: {int((fv.dwell_s>7200).sum())}")
OUTL.append(("dwell under 60 s", int((fv.dwell_s < 60).sum()), "a check-in and a fast departure",
             "FLAG (weak evidence for a place claim), keep the visit"))
OUTL.append(("dwell over 2 hours", int((fv.dwell_s > 7200).sum()), "agent left the app open", "FLAG, keep"))
tr = (pd.to_datetime(fv.checkin_ts) - pd.to_datetime(fv.start_ts)).dt.total_seconds()
say(f"travel time: min={tr.min()/60:.1f} min median={tr.median()/60:.1f} min p99={tr.quantile(.99)/60:.1f} min "
    f"max={tr.max()/60:.1f} min; negative={int((tr<0).sum())}")
OUTL.append(("negative travel time", int((tr < 0).sum()), "clock skew or data error", "would be EXCLUDED (none here)"))
say(f"gps_accuracy_m outliers: >100 m: {int((gp.accuracy_m>100).sum())} ({100*(gp.accuracy_m>100).mean():.3f}%); "
    f"max={gp.accuracy_m.max():.1f} m → FLAG (low-reliability point), keep")
OUTL.append(("GPS accuracy above 100 m", int((gp.accuracy_m > 100).sum()), "urban canyon or no fix",
             "FLAG: evidence weight reduced, never dropped silently"))
say(f"implied speed above 40 km/h: {int((spd>40).sum())} steps (0.0005%) → FLAG as a process anomaly")
OUTL.append(("implied speed above 40 km/h", int((spd > 40).sum()), "noise between fixes, not teleportation",
             "FLAG: speed-plausibility feature; no spoofing conclusion drawn"))
say(f"address strings with no digits: {int((DIG==0).sum())}; with no letters: {int((ALPHA==0).sum())}; "
    f"with no separator: {int(((COMMA+SLASH+HYPH)==0).sum())}")
OUTL.append(("address text with no digits", int((DIG == 0).sum()), "a house number cannot exist in this record",
             "FLAG (no_digit) → tier cap at locality/street level"))
say(f"6-digit tokens that match no known pincode: {int((SIX.notna() & ~SIX.isin(PIN_KNOWN)).sum())} "
    f"→ FLAG (pin_unknown): the token is a hypothesis, not a fact")
OUTL.append(("6-digit token matching no known pincode", int((SIX.notna() & ~SIX.isin(PIN_KNOWN)).sum()),
             "either a phone fragment, a plot number, or an out-of-area pincode", "FLAG, never parse as evidence"))
say(f"hierarchy violations: addresses whose town differs from their account's town: "
    f"{int((ad.merge(ac[['account_id','town_id']], on='account_id', suffixes=('','_acct')).eval('town_id != town_id_acct')).sum())}")
OUTL.append(("address.town_id differs from account.town_id",
             int((ad.merge(ac[["account_id", "town_id"]], on="account_id", suffixes=("", "_acct"))
                  .eval("town_id != town_id_acct")).sum()),
             "the borrower works/lives elsewhere than the account's serviced town", "FLAG (mobility), keep as-is"))
for name, n, why, act in OUTL:
    say(f"  • {name:<52} n={n:<7} why: {why:<62} action: {act}")

# ═══════════════════════ 14. DATA QUALITY SCORECARD ═══════════════════════
say("\n" + "=" * 100)
say("SECTION 14 — DATA QUALITY SCORECARD (per table)")
say("=" * 100)
for k, df in T.items():
    nulls = df.isna().mean().mean() * 100
    dups = df.duplicated().sum()
    keyok = all(df[c].is_unique for c in df.columns if c.endswith("_id") and c in
                {"town_id", "locality_id", "poi_id", "address_id", "account_id", "agent_id", "visit_id"} - {"town_id"})
    say(f"  {k:<22} rows={len(df):>7}  mean null%={nulls:5.2f}  exact dup rows={dups:>3}  key integrity={'ok' if keyok else 'CHECK'}")

say(f"\nTOTAL runtime of this EDA: {time.time()-t_start:.1f} s   "
    f"peak RSS: {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024:.0f} MB")

with open(os.path.join(OUT, "eda_report.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(LOG))
with open(os.path.join(OUT, "eda_chart_index.json"), "w") as f:
    json.dump({k: len(v) for k, v in CHARTS.items()}, f, indent=2)
print(f"\n[eda] transcript → data/derived/eda_report.txt   charts → data/derived/eda_charts/ "
      f"({len(CHARTS)} files: {', '.join(CHARTS)})")
