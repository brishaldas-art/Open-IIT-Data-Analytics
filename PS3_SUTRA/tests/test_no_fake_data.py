"""§49/§11 — the no-fake-data guard for the workstation frontend.

Three claims are enforced here, on the source tree and on the built bundle:

1. **No invented sources or simulated behaviour.** The production frontend may not contain the
   fabricated source names, a fixture replay presented as live data, a simulated delay, a mock
   provider, or any client-side randomness used to mint business identifiers.

2. **No client-side geography.** No latitude/longitude, WGS84, EPSG, Mercator or basemap. Statements
   that *refuse* those things ("no basemap", "never latitude/longitude") are prose and are allowed —
   the check only fires on a token that is not sitting in a refusal sentence.

3. **Fixture data cannot be a production dependency.** Every reference to `src/fixtures/**` from
   production code is a *dynamic* import guarded by `FIXTURES_ENABLED`, and the built bundle carries
   no fixture payload at all. The labelled captured fallback is legitimate — but it must be
   unreachable when the build does not explicitly enable fixtures, and the built artefact is the
   proof.

This deliberately does **not** flag the labelled captured/offline fallback itself, which the brief
permits: the test asserts it is gated, not that it is absent.
"""
import json
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
SRC = os.path.join(WEB, "src")
SITE = os.path.join(WEB, "site")

# The deployed workbench (the battle-model frontend, ported onto the live API). Same rules apply to
# its source tree and to its built artefact: it is the frontend the service actually serves at `/`.
BM = os.path.join(ROOT, "battle_model")
BM_SRC = os.path.join(BM, "src")
BM_SITE = os.path.join(BM, "site")

# invented sources / simulated behaviour that must never exist in this product
BANNED_LITERALS = (
    "Municipal Parcel DB", "Gazette Registry", "Postal PIN Directory",
    "demo 0.9.4", "fixture replay", "mock provider", "fake provider", "fake GPS",
    "simulated delay", "Math.random",
)

# geography tokens that are only acceptable inside a refusal sentence
GEO_TOKENS = re.compile(r"wgs84|epsg|mercator|\bbasemap\b|\blatitude\b|\blongitude\b|\blat/lon\b", re.I)
REFUSAL_WORDS = ("no ", "not ", "never", "refus", "without")

# Captured *values* that could only ship if the dump itself did. Key names such as `captured_from`
# are deliberately not used: our own code reads those keys, so the name proves nothing about data.


def _sources():
    for base, dirs, files in os.walk(SRC):
        dirs[:] = [d for d in dirs if d not in ("node_modules",)]
        for f in sorted(files):
            if f.endswith((".ts", ".tsx", ".css")) and not base.endswith(os.sep + "fixtures"):
                yield os.path.join(base, f)


def _workbench_sources():
    """The deployed workbench tree — every .ts/.tsx/.css file it ships from."""
    for base, dirs, files in os.walk(BM_SRC):
        dirs[:] = [d for d in dirs if d not in ("node_modules",)]
        for f in sorted(files):
            if f.endswith((".ts", ".tsx", ".css")):
                yield os.path.join(base, f)


def _production_sources():
    """Everything except the fixture module itself — both frontends."""
    yield from _sources()
    yield from _workbench_sources()


def _rel(path: str) -> str:
    return os.path.relpath(path, ROOT)


def test_no_invented_sources_or_simulated_behaviour_in_the_frontend():
    offenders = []
    for path in _production_sources():
        text = open(path, encoding="utf-8").read()
        for token in BANNED_LITERALS:
            if token in text:
                line = next((i for i, l in enumerate(text.splitlines(), 1) if token in l), 0)
                offenders.append(f"{_rel(path)}:{line}: {token}")
    assert not offenders, "invented source or simulated behaviour in the frontend: " + "; ".join(offenders)


def test_no_client_side_geography():
    """Only a refusal *sentence* may name a geographic system, and sentences wrap across lines."""
    offenders = []
    for path in _production_sources():
        lines = open(path, encoding="utf-8").read().splitlines()
        for i, line in enumerate(lines, 1):
            if not GEO_TOKENS.search(line):
                continue
            window = " ".join(lines[max(0, i - 2):i]).lower()   # this line + the two before it
            if any(w in window for w in REFUSAL_WORDS):
                continue                    # "…and no / third-party basemap or geocoder is consulted…"
            offenders.append(f"{_rel(path)}:{i}: {line.strip()[:90]}")
    assert not offenders, "geographic coordinate system leaked into the frontend: " + "; ".join(offenders)


def test_the_frontend_never_mints_identifiers_or_delays():
    """No `Date.now()`-as-id, no counters standing in for backend ids, no fake latency."""
    offenders = []
    for path in _production_sources():
        text = open(path, encoding="utf-8").read()
        for pat in (r"Math\.random", r"Date\.now\(\)\s*\+", r"setTimeout\([^)]*\bdelay\b",
                    r"await\s+sleep\(", r"new\s+Promise\([^)]*setTimeout"):
            m = re.search(pat, text)
            if m:
                offenders.append(f"{_rel(path)}: {m.group(0)[:40]}")
    assert not offenders, "client-side identifier minting or simulated latency: " + "; ".join(offenders)


def test_fixture_data_is_only_reachable_through_a_gated_dynamic_import():
    """No production file may statically import the fixture module — only `import()`, behind the flag."""
    offenders = []
    for path in _production_sources():
        for i, line in enumerate(open(path, encoding="utf-8").read().splitlines(), 1):
            if "fixtures/" not in line:
                continue
            stripped = line.strip()
            if stripped.startswith("*") or stripped.startswith("//"):
                continue
            if stripped.startswith("import(") or "await import(" in stripped or "import('../fixtures" in stripped:
                continue                # dynamic import — gated below
            offenders.append(f"{_rel(path)}:{i}: {stripped[:80]}")
    assert not offenders, "a static fixture import reached production code: " + "; ".join(offenders)


def test_the_fixture_gate_exists_and_is_false_in_a_production_build():
    cfg = open(os.path.join(SRC, "config", "product.ts"), encoding="utf-8").read()
    assert "import.meta.env.DEV" in cfg, "the fixture gate must key off the build mode"
    assert "VITE_DEV_FIXTURES" in cfg, "an explicit opt-in must be required for an offline demo build"
    use_api = open(os.path.join(SRC, "api", "useApi.ts"), encoding="utf-8").read()
    assert "if (!FIXTURES_ENABLED) return null" in use_api, "the captured dump must be unreachable when gated off"


def test_the_built_bundle_carries_no_fixture_payload():
    """The strongest form of the claim: the shipped artefact contains no captured data at all."""
    assets = os.path.join(SITE, "assets")
    if not os.path.isdir(assets):
        pytest.skip("no build present (run `npm run build`)")
    bundles = [os.path.join(assets, f) for f in os.listdir(assets) if f.endswith(".js")]
    assert bundles, "no javascript bundle in web/site/assets"
    captured = json.load(open(os.path.join(SRC, "fixtures", "captured.json"), encoding="utf-8"))
    values = [captured["note"], captured["captured_from"]]
    health = captured["cases"].get("health", {}).get("response", {})
    packs = (health.get("packs") or [{}])
    if packs and packs[0].get("pack_version"):
        values.append(packs[0]["pack_version"])          # a string that exists only in a captured row
    offenders = []
    for path in bundles:
        text = open(path, encoding="utf-8", errors="replace").read()
        for value in values:
            if value and value in text:
                offenders.append(f"{os.path.basename(path)}: {value[:40]}")
    assert not offenders, "fixture payload shipped in the production bundle: " + "; ".join(offenders)


def test_the_workbench_build_ships_no_banned_token():
    """The single-file build served at `/` must not carry an invented source, mode or geography token.

    `Math.random` is excluded for the same reason as below (React's own runtime uses it for DOM keys);
    the source-level check above is the guard for our code.
    """
    entry = os.path.join(BM_SITE, "index.html")
    if not os.path.isfile(entry):
        pytest.skip("no workbench build present (run `npm run build` in battle_model/)")
    text = open(entry, encoding="utf-8", errors="replace").read()
    banned = tuple(t for t in BANNED_LITERALS if t != "Math.random")
    offenders = [t for t in banned if t in text]
    assert not offenders, "invented token shipped in the workbench build: " + "; ".join(offenders)
    # and it must not be able to render a fixture: the fixture module does not exist in this tree
    assert not os.path.exists(os.path.join(BM_SRC, "lib", "fixtures.ts")), \
        "the workbench must have no fixture module at all"


def test_the_workbench_serves_real_endpoints_only():
    """Every fetcher in the data seam must address a real SUTRA route — no fixture-shaped fallback."""
    text = open(os.path.join(BM_SRC, "lib", "api.ts"), encoding="utf-8").read()
    for route in ("/health", "/v1/overview", "/v1/places", "/v1/place/", "/v1/evidence",
                  "/v1/tasks", "/v1/address/", "/v1/geometry/", "/v1/plane/", "/v1/audit/",
                  "/resolve", "/v1/adjudicate", "/v1/tasks/"):
        assert route in text, f"the workbench never calls {route}"
    for fake in ("fixtures", "net(", "setTimeout("):
        assert fake not in text, f"the workbench data seam still contains {fake!r}"


def test_the_built_bundle_has_no_invented_source_names():
    """Tokens that could only be ours. `Math.random` is excluded here on purpose: React's own runtime
    uses it for internal DOM keys (`__reactFiber$…`), which is vendored library behaviour, not product
    behaviour — the source-level check above is the guard for our code, and it passes with zero."""
    bundle_tokens = tuple(t for t in BANNED_LITERALS if t != "Math.random")
    assets = os.path.join(SITE, "assets")
    if not os.path.isdir(assets):
        pytest.skip("no build present (run `npm run build`)")
    for f in os.listdir(assets):
        if not f.endswith(".js"):
            continue
        text = open(os.path.join(assets, f), encoding="utf-8", errors="replace").read()
        for token in bundle_tokens:
            assert token not in text, f"{token!r} shipped in {f}"
