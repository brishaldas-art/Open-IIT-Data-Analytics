/**
 * One query hook for the whole app.
 *
 * Live first, always. A captured response may stand in for a demo case **only when the build
 * explicitly enables fixtures** (`config/product.FIXTURES_ENABLED` — development, or an offline
 * demo build). In a production build that branch does not exist: an unreachable service produces an
 * error state, which is the honest rendering. A fixture is never presented as live telemetry.
 */
import { useQuery, type UseQueryResult } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { FIXTURES_ENABLED } from '../config/product'
import { useApp } from '../state/appState'

type Case = { status: number; response: unknown }

interface Captured {
  note: string
  captured_from: string
  captured_on: string
  cases: Record<string, Case>
}

/**
 * The captured dump is loaded through a dynamic import and only when fixtures are enabled, so a
 * production build never carries captured responses in its main bundle and can never reach them.
 */
async function loadCaptured(): Promise<Captured | null> {
  if (!FIXTURES_ENABLED) return null
  const mod = await import('../fixtures/demo')
  return mod.CAPTURED as unknown as Captured
}

export async function capturedCase(key: string): Promise<unknown | null> {
  const captured = await loadCaptured()
  const c = captured?.cases[key]
  return c ? c.response : null
}

export async function capturedMeta() {
  const captured = await loadCaptured()
  if (!captured) return null
  return { note: captured.note, from: captured.captured_from, on: captured.captured_on,
           keys: Object.keys(captured.cases) }
}

export interface Sourced<T> { data: T; fixture: boolean; fixtureKey?: string }

export function useApi<T>(opts: {
  key: (string | null)[]
  live: () => Promise<T>
  fixtureKey?: string
  enabled?: boolean
}): UseQueryResult<Sourced<T>, Error> {
  const { setApiReachable } = useApp()
  const q = useQuery<Sourced<T>, Error>({
    queryKey: opts.key,
    enabled: opts.enabled !== false,
    retry: 0,
    staleTime: 30_000,
    // Deliberately NOT keepPreviousData: holding the previous key's payload on screen would let one
    // address's answers appear under another address's heading. A skeleton between addresses is the
    // honest rendering. (Caught by the browser smoke test on 2026-10-08: the replay strip carried
    // AD003067's columns under AD002936.)
    queryFn: async () => {
      try {
        const data = await opts.live()
        setApiReachable(true)
        return { data, fixture: false }
      } catch (err) {
        const fb = opts.fixtureKey ? await capturedCase(opts.fixtureKey) : null
        if (fb) {
          setApiReachable(false)
          return { data: fb as T, fixture: true, fixtureKey: opts.fixtureKey }
        }
        setApiReachable(false)
        throw err as Error
      }
    },
  })
  useEffect(() => {
    if (q.isSuccess && q.data && !q.data.fixture) setApiReachable(true)
  }, [q.isSuccess, q.data, setApiReachable])
  return q
}

/** React hook form of {@link capturedMeta}: null in a production build. */
export function useCapturedMeta() {
  const [meta, setMeta] = useState<Awaited<ReturnType<typeof capturedMeta>>>(null)
  useEffect(() => { let live = true; capturedMeta().then((m) => { if (live) setMeta(m) }); return () => { live = false } }, [])
  return meta
}
