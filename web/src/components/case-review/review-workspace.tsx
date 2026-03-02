import { useEffect } from 'react'

import { useQuery, useQueryClient } from '@tanstack/react-query'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  getCaseRun,
  getCaseRunTimeline,
  listCaseRuns,
  type CaseRunDetail,
  type CaseRunSummary,
  type CaseRunTimeline,
} from '@/lib/api/client'
import { useUiStore } from '@/lib/store/ui-store'

export interface ReviewWorkspaceData {
  caseRuns: CaseRunSummary[]
  selectedCaseId: string | null
  detail: CaseRunDetail | undefined
  timeline: CaseRunTimeline | undefined
  loadingDetail: boolean
  loadingTimeline: boolean
  detailError: string | null
  timelineError: string | null
}

interface ReviewWorkspaceProps {
  title: string
  subtitle: string
  children: (data: ReviewWorkspaceData) => React.JSX.Element
}

function fmtDate(value: string): string {
  return new Date(value).toLocaleString()
}

function statusTone(status: string): string {
  if (status === 'completed') return 'bg-emerald-100 text-emerald-700'
  if (status === 'running') return 'bg-cyan-100 text-cyan-700'
  if (status === 'timed_out') return 'bg-amber-100 text-amber-700'
  if (status === 'escalated') return 'bg-red-100 text-red-700'
  return 'bg-slate-100 text-slate-700'
}

export function truncateText(value: string | null | undefined, maxChars: number): string {
  if (!value) return ''
  if (value.length <= maxChars) return value
  return `${value.slice(0, maxChars - 1)}…`
}

export function ReviewWorkspace({
  title,
  subtitle,
  children,
}: ReviewWorkspaceProps): React.JSX.Element {
  const selectedCaseId = useUiStore((state) => state.selectedCaseId)
  const setSelectedCaseId = useUiStore((state) => state.setSelectedCaseId)
  const caseRunLimit = useUiStore((state) => state.caseRunLimit)
  const queryClient = useQueryClient()

  const caseRunsQuery = useQuery({
    queryKey: ['case-runs', caseRunLimit],
    queryFn: () => listCaseRuns(caseRunLimit),
    refetchInterval: 30_000,
  })

  const caseDetailQuery = useQuery({
    queryKey: ['case-run', selectedCaseId],
    queryFn: () => getCaseRun(selectedCaseId ?? ''),
    enabled: selectedCaseId !== null,
    refetchInterval: false,
    staleTime: 30_000,
  })

  const timelineQuery = useQuery({
    queryKey: ['case-run-timeline', selectedCaseId],
    queryFn: () => getCaseRunTimeline(selectedCaseId ?? ''),
    enabled: selectedCaseId !== null,
    refetchInterval: false,
    staleTime: 30_000,
  })

  const caseRuns = caseRunsQuery.data ?? []

  useEffect(() => {
    if (!selectedCaseId && caseRuns.length > 0) {
      setSelectedCaseId(caseRuns[0].case_id)
    }
  }, [caseRuns, selectedCaseId, setSelectedCaseId])

  return (
    <div className="grid gap-4 xl:grid-cols-[24rem_minmax(0,1fr)]">
      <Card className="xl:sticky xl:top-4 xl:h-[calc(100vh-5.5rem)]">
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{subtitle}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm text-slate-600">Showing latest {caseRunLimit} cases.</p>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => void queryClient.invalidateQueries({ queryKey: ['case-runs'] })}
            >
              Refresh
            </Button>
          </div>

          {caseRunsQuery.isLoading ? <p className="text-sm text-slate-500">Loading recent cases...</p> : null}
          {caseRunsQuery.isError ? (
            <p className="text-sm text-red-600">Failed to load cases: {String(caseRunsQuery.error)}</p>
          ) : null}

          <div className="space-y-2 xl:max-h-[calc(100vh-14.5rem)] xl:overflow-auto xl:pr-1">
            {caseRuns.map((run) => (
              <button
                key={run.case_id}
                type="button"
                className={
                  selectedCaseId === run.case_id
                    ? 'w-full rounded-md border border-cyan-300 bg-cyan-50 p-3 text-left'
                    : 'w-full rounded-md border border-slate-200 bg-white p-3 text-left'
                }
                onClick={() => setSelectedCaseId(run.case_id)}
              >
                <div className="mb-2 flex items-center justify-between gap-2">
                  <span className="font-mono text-xs text-slate-600">{run.case_id.slice(0, 8)}</span>
                  <Badge className={statusTone(run.status)}>{run.status.replaceAll('_', ' ')}</Badge>
                </div>
                <p className="mb-1 line-clamp-2 text-sm text-slate-900">{run.objective}</p>
                <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                  <span>{run.case_class}</span>
                  <span>loops: {run.loop_count}</span>
                  <span>{fmtDate(run.updated_at)}</span>
                </div>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {children({
        caseRuns,
        selectedCaseId,
        detail: caseDetailQuery.data,
        timeline: timelineQuery.data,
        loadingDetail: caseDetailQuery.isLoading,
        loadingTimeline: timelineQuery.isLoading,
        detailError: caseDetailQuery.isError ? String(caseDetailQuery.error) : null,
        timelineError: timelineQuery.isError ? String(timelineQuery.error) : null,
      })}
    </div>
  )
}
