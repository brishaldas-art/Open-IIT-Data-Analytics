/** Global, tiny, and deliberately dumb: as-of instant, request purpose, data source mode. */
import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import { ASOF_MOMENT } from '../config/product'

export type SourceMode = 'live' | 'captured'

interface Ctx {
  asOf: string
  setAsOf: (v: string) => void
  purpose: string
  setPurpose: (v: string) => void
  source: SourceMode
  setSource: (v: SourceMode) => void
  apiReachable: boolean | null
  setApiReachable: (v: boolean | null) => void
  /** who is recording decisions — stored by the backend as the observing agent of the adjudication */
  reviewer: string
  setReviewer: (v: string) => void
}

const AppCtx = createContext<Ctx | null>(null)

export function AppProvider({ children }: { children: ReactNode }) {
  const [asOf, setAsOf] = useState(ASOF_MOMENT)
  const [purpose, setPurpose] = useState('FIELD_NAVIGATION')
  const [source, setSource] = useState<SourceMode>('live')
  const [apiReachable, setApiReachable] = useState<boolean | null>(null)
  const [reviewer, setReviewer] = useState('FA004')
  const value = useMemo(
    () => ({ asOf, setAsOf, purpose, setPurpose, source, setSource, apiReachable, setApiReachable,
             reviewer, setReviewer }),
    [asOf, purpose, source, apiReachable, reviewer],
  )
  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>
}

export function useApp(): Ctx {
  const c = useContext(AppCtx)
  if (!c) throw new Error('useApp outside provider')
  return c
}
