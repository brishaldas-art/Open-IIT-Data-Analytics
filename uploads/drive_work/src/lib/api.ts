/* ------------------------------------------------------------------ *
 * DATA ACCESS SEAM
 * Every view reads through these async fetchers. Today they resolve
 * local fixtures after a simulated network delay; to go live, replace
 * each body with the documented HTTP call and keep the return types.
 * ------------------------------------------------------------------ */

import { useEffect, useRef, useState } from "react";
import { CASES, OVERVIEW, PLACES, SCENARIOS, SCENE, VISITS } from "./fixtures";
import type {
  FieldVisit,
  Place,
  Scenario,
  Scene,
  SystemOverview,
  VerifyCase,
} from "./types";

const net = (ms = 150) => new Promise<void>((r) => setTimeout(r, ms));

/** @backend GET /v1/overview */
export async function fetchOverview(): Promise<SystemOverview> {
  await net(120);
  return OVERVIEW;
}

/** @backend GET /v1/scene  (base cartography, local plane metres) */
export async function fetchScene(): Promise<Scene> {
  await net(60);
  return SCENE;
}

/** @backend GET /v1/resolver/scenarios — in production this is
 *  POST /v1/resolve with the raw address; fixtures are pre-baked
 *  resolve traces so the UI can replay the pipeline deterministically. */
export async function fetchScenarios(): Promise<Scenario[]> {
  await net(140);
  return SCENARIOS;
}

/** @backend GET /v1/places */
export async function fetchPlaces(): Promise<Place[]> {
  await net(120);
  return PLACES;
}

/** @backend GET /v1/evidence?window=14d */
export async function fetchVisits(): Promise<FieldVisit[]> {
  await net(120);
  return VISITS;
}

/** @backend GET /v1/verify/cases?state=open */
export async function fetchCases(): Promise<VerifyCase[]> {
  await net(120);
  return CASES;
}

/* ---------------- tiny async hook ---------------- */

export function useQuery<T>(fn: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const seq = useRef(0);
  useEffect(() => {
    const id = ++seq.current;
    setLoading(true);
    fn().then((d) => {
      if (seq.current === id) {
        setData(d);
        setLoading(false);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return { data, loading };
}
