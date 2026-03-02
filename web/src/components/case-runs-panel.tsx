import { useEffect, useMemo, useState } from 'react'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { flexRender, getCoreRowModel, useReactTable, type ColumnDef } from '@tanstack/react-table'
import { Workflow } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import {
  getCaseRun,
  getCaseRunTimeline,
  listCaseRuns,
  runInvestigation,
  type CaseRunDetail,
  type CaseRunTimeline,
  type CaseRunSummary,
  type InvestigationRequest,
} from '@/lib/api/client'
import { useUiStore } from '@/lib/store/ui-store'

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

type HypothesisItem = NonNullable<CaseRunDetail['hypotheses']>[number]
type EvidenceItem = NonNullable<CaseRunDetail['evidence_records']>[number]
type CognitionItem = NonNullable<CaseRunDetail['cognition_records']>[number]
type TerminationItem = NonNullable<CaseRunDetail['termination_snapshots']>[number]
type TimelineEventItem = NonNullable<CaseRunTimeline['events']>[number]
type DetailTab = 'overview' | 'timeline' | 'flow' | 'tasks' | 'hypotheses' | 'evidence' | 'cognition' | 'outputs'

function cognitionLabel(recordType: string): string {
  if (recordType === 'observation_record') return 'Observation'
  if (recordType === 'decision_record') return 'Decision'
  if (recordType === 'feedback_record') return 'Feedback'
  if (recordType === 'insight_record') return 'Insight'
  return recordType
}

function cognitionSummary(record: CognitionItem): string {
  if (record.record_type === 'decision_record') {
    const action = record.decision_action ? `Action: ${record.decision_action}.` : 'Decision recorded.'
    const reason = record.decision_reason ? ` Reason: ${record.decision_reason}` : ''
    return `${action}${reason}`
  }
  if (record.record_type === 'feedback_record') {
    const replan = record.feedback_requires_replan === null ? 'n/a' : String(record.feedback_requires_replan)
    const novelty = record.feedback_novelty_score === null ? 'n/a' : String(record.feedback_novelty_score)
    const drift = record.feedback_drift_score === null ? 'n/a' : String(record.feedback_drift_score)
    const reason = record.feedback_reason ? ` Reason: ${record.feedback_reason}` : ''
    return `Replan: ${replan}. Novelty: ${novelty}. Drift: ${drift}.${reason}`
  }
  if (record.record_type === 'insight_record') {
    return record.insight_text ?? 'Insight captured.'
  }
  return 'Observation captured for current case context.'
}

function objectiveBlockers(detail: CaseRunDetail, latest: TerminationItem | null): string[] {
  const blockers: string[] = []
  const checks = detail.final_report?.checks ?? []
  for (const check of checks) {
    if (!check.passed) {
      blockers.push(`${check.description}: ${check.reason}`)
    }
  }

  if (latest) {
    if (!latest.objective_satisfied) blockers.push('Objective not yet satisfied by current evidence.')
    if (!latest.evidence_completeness_sufficient) blockers.push('Evidence completeness threshold not met.')
    if (!latest.confidence_sufficient) blockers.push('Confidence threshold not met.')
    if (latest.timeout_reached) blockers.push('Run hit timeout before closure.')
    if (latest.expected_value_below_threshold) blockers.push('Next-step expected value dropped below threshold.')
    if (latest.no_novel_signal) blockers.push('No novel signal was detected in recent loop(s).')
  }
  return Array.from(new Set(blockers))
}

function timelineEventLabel(eventType: TimelineEventItem['event_type']): string {
  if (eventType === 'case_started') return 'Case'
  if (eventType === 'task_upserted') return 'Task'
  if (eventType === 'tool_execution') return 'Tool'
  if (eventType === 'evidence_recorded') return 'Evidence'
  if (eventType === 'cognition_recorded') return 'Cognition'
  if (eventType === 'termination_evaluated') return 'Termination'
  if (eventType === 'final_report_stored') return 'Report'
  return eventType
}

function truncateText(value: string | null | undefined, maxChars: number): string {
  if (!value) return ''
  if (value.length <= maxChars) return value
  return `${value.slice(0, maxChars - 1)}…`
}

export function CaseRunsPanel(): React.JSX.Element {
  const [objective, setObjective] = useState('')
  const [activeDetailTab, setActiveDetailTab] = useState<DetailTab>('overview')
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
    refetchInterval: activeDetailTab === 'timeline' ? false : 15_000,
  })

  const caseTimelineQuery = useQuery({
    queryKey: ['case-run-timeline', selectedCaseId],
    queryFn: () => getCaseRunTimeline(selectedCaseId ?? ''),
    enabled: selectedCaseId !== null && activeDetailTab === 'timeline',
    refetchInterval: false,
    staleTime: 30_000,
  })

  const runMutation = useMutation({
    mutationFn: (payload: InvestigationRequest) => runInvestigation(payload),
    onSuccess: async (response) => {
      setSelectedCaseId(response.case_id)
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['case-runs'] }),
        queryClient.invalidateQueries({ queryKey: ['case-run', response.case_id] }),
      ])
    },
  })

  const columns = useMemo<ColumnDef<CaseRunSummary>[]>(
    () => [
      {
        accessorKey: 'case_id',
        header: 'Case',
        cell: ({ row }) => <span className="font-mono text-xs">{row.original.case_id.slice(0, 8)}</span>,
      },
      {
        accessorKey: 'case_class',
        header: 'Class',
      },
      {
        accessorKey: 'status',
        header: 'Status',
        cell: ({ row }) => (
          <Badge className={statusTone(row.original.status)}>{row.original.status.replaceAll('_', ' ')}</Badge>
        ),
      },
      {
        accessorKey: 'loop_count',
        header: 'Loops',
      },
      {
        accessorKey: 'updated_at',
        header: 'Updated',
        cell: ({ row }) => <span className="text-xs text-slate-600">{fmtDate(row.original.updated_at)}</span>,
      },
      {
        accessorKey: 'objective',
        header: 'Objective',
        cell: ({ row }) => <span className="line-clamp-1 max-w-[26rem]">{row.original.objective}</span>,
      },
    ],
    [],
  )

  const table = useReactTable({
    data: caseRunsQuery.data ?? [],
    columns,
    getCoreRowModel: getCoreRowModel(),
  })

  useEffect(() => {
    if (!selectedCaseId && caseRunsQuery.data && caseRunsQuery.data.length > 0) {
      setSelectedCaseId(caseRunsQuery.data[0].case_id)
    }
  }, [caseRunsQuery.data, selectedCaseId, setSelectedCaseId])

  function submitRun(event: React.FormEvent<HTMLFormElement>): void {
    event.preventDefault()
    if (!objective.trim()) return
    runMutation.mutate({
      objective,
      mode: 'fast_mode',
      timeout_minutes: 8,
      playbook_policy: 'suggestive',
    })
    setObjective('')
  }

  const caseDetail = caseDetailQuery.data
  const caseRuns = caseRunsQuery.data ?? []

  return (
    <div className="grid gap-4 2xl:grid-cols-[1fr_1.3fr]">
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Start Investigation</CardTitle>
            <CardDescription>Kick off a new case run against the live API runtime.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-3" onSubmit={submitRun}>
              <Textarea
                placeholder="Investigate outage in profile sync with permission denied errors"
                value={objective}
                onChange={(event) => setObjective(event.target.value)}
              />
              <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
                <Button className="w-full sm:w-auto" type="submit" disabled={runMutation.isPending}>
                  <Workflow className="mr-2 size-4" />
                  {runMutation.isPending ? 'Launching...' : 'Launch Case'}
                </Button>
                {runMutation.isError ? (
                  <span className="text-sm text-red-600">{String(runMutation.error)}</span>
                ) : null}
              </div>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Previous Runs</CardTitle>
            <CardDescription>Inspect case flow from summary to granular execution traces.</CardDescription>
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

            <div className="space-y-2 lg:hidden">
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

            {caseRunsQuery.isLoading ? <p className="text-sm text-slate-500">Loading recent cases...</p> : null}
            {caseRunsQuery.isError ? (
              <p className="text-sm text-red-600">
                Failed to load cases: {String(caseRunsQuery.error)}
              </p>
            ) : null}
            {!caseRunsQuery.isLoading && !caseRunsQuery.isError && caseRuns.length === 0 ? (
              <p className="text-sm text-slate-500">No cases yet. Launch one above and it will appear here.</p>
            ) : null}

            <div className="hidden max-h-[24rem] overflow-auto rounded-md border border-slate-200 lg:block">
              <Table>
                <TableHeader>
                  {table.getHeaderGroups().map((headerGroup) => (
                    <TableRow key={headerGroup.id}>
                      {headerGroup.headers.map((header) => (
                        <TableHead key={header.id}>
                          {header.isPlaceholder
                            ? null
                            : flexRender(header.column.columnDef.header, header.getContext())}
                        </TableHead>
                      ))}
                    </TableRow>
                  ))}
                </TableHeader>
                <TableBody>
                  {table.getRowModel().rows.map((row) => (
                    <TableRow
                      key={row.id}
                      className="cursor-pointer"
                      data-state={selectedCaseId === row.original.case_id ? 'selected' : undefined}
                      onClick={() => setSelectedCaseId(row.original.case_id)}
                    >
                      {row.getVisibleCells().map((cell) => (
                        <TableCell key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>

      <CaseRunDetailPanel
        detail={caseDetail}
        loading={caseDetailQuery.isLoading}
        timeline={caseTimelineQuery.data}
        timelineLoading={caseTimelineQuery.isLoading}
        timelineError={caseTimelineQuery.isError ? String(caseTimelineQuery.error) : null}
        activeTab={activeDetailTab}
        onTabChange={setActiveDetailTab}
      />
    </div>
  )
}

function CaseRunDetailPanel({
  detail,
  loading,
  timeline,
  timelineLoading,
  timelineError,
  activeTab,
  onTabChange,
}: {
  detail: CaseRunDetail | undefined
  loading: boolean
  timeline: CaseRunTimeline | undefined
  timelineLoading: boolean
  timelineError: string | null
  activeTab: DetailTab
  onTabChange: (value: DetailTab) => void
}): React.JSX.Element {
  const [expandedTimelineEventIds, setExpandedTimelineEventIds] = useState<Set<string>>(new Set())

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Case Detail</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-600">Loading case detail...</p>
        </CardContent>
      </Card>
    )
  }

  if (!detail) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Case Detail</CardTitle>
          <CardDescription>Select a case run to inspect full flow.</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  const terminationSnapshots = detail.termination_snapshots ?? []
  const mandatoryChecks = detail.mandatory_checks ?? []
  const tasks = detail.tasks ?? []
  const taskHypothesisLinks = detail.task_hypothesis_links ?? {}
  const taskEvidenceLinks = detail.task_evidence_links ?? {}
  const evidenceRecords = detail.evidence_records ?? []
  const cognitionRecords = detail.cognition_records ?? []
  const toolOutputs = detail.tool_outputs ?? []
  const hypotheses = detail.hypotheses ?? []
  const hypothesisEvidenceLinks = detail.hypothesis_evidence_links ?? []

  const hypothesisById = new Map<string, HypothesisItem>(
    hypotheses.map((item) => [String(item.hypothesis_id), item]),
  )
  const evidenceById = new Map<string, EvidenceItem>(evidenceRecords.map((item) => [item.evidence_id, item]))

  const evidenceIdsByHypothesis = new Map<string, string[]>()
  for (const link of hypothesisEvidenceLinks) {
    const key = String(link.hypothesis_id)
    const existing = evidenceIdsByHypothesis.get(key) ?? []
    existing.push(link.evidence_id)
    evidenceIdsByHypothesis.set(key, existing)
  }

  const latestTermination = terminationSnapshots.length > 0 ? terminationSnapshots[terminationSnapshots.length - 1] : null
  const timelineBlockers = timeline?.unresolved_blockers ?? []
  const timelineEvents = (timeline?.events ?? []).slice(-60)
  const blockers =
    timelineBlockers.length > 0
      ? timelineBlockers
      : objectiveBlockers(detail, latestTermination)

  function toggleTimelineEvent(eventId: string): void {
    setExpandedTimelineEventIds((previous) => {
      const next = new Set(previous)
      if (next.has(eventId)) next.delete(eventId)
      else next.add(eventId)
      return next
    })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base leading-6 sm:text-lg">{detail.summary.objective}</CardTitle>
        <CardDescription className="break-all text-xs sm:text-sm">
          Case <span className="font-mono">{detail.summary.case_id}</span> · updated {fmtDate(detail.summary.updated_at)}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={(value) => onTabChange(value as DetailTab)}>
          <TabsList className="w-full">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="timeline">Timeline</TabsTrigger>
            <TabsTrigger value="flow">Flow</TabsTrigger>
            <TabsTrigger value="tasks">Tasks</TabsTrigger>
            <TabsTrigger value="hypotheses">Hypotheses</TabsTrigger>
            <TabsTrigger value="evidence">Evidence</TabsTrigger>
            <TabsTrigger value="cognition">Cognition</TabsTrigger>
            <TabsTrigger value="outputs">Tool Outputs</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <Badge className={statusTone(detail.summary.status)}>{detail.summary.status}</Badge>
              <Badge>{detail.summary.case_class}</Badge>
              <Badge>loops: {detail.summary.loop_count}</Badge>
            </div>
            {detail.final_report ? (
              <div className="space-y-2">
                <h4 className="font-semibold text-slate-900">Final Assessment</h4>
                <p className="whitespace-pre-wrap text-sm text-slate-700">{detail.final_report.final_assessment}</p>
                <div className="text-sm text-slate-600">
                  confidence: {detail.final_report.confidence_label} ({detail.final_report.confidence_score})
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-600">No final report persisted yet.</p>
            )}
          </TabsContent>

          <TabsContent value="timeline" className="space-y-3 overflow-x-hidden">
            <section className="rounded-md border border-slate-200 p-3 text-sm">
              <div className="font-medium text-slate-900">
                {timeline?.objective_satisfied ? 'Objective currently satisfied' : 'Objective not yet satisfied'}
              </div>
              <div className="mt-1 text-slate-600">
                Latest stop reason: {timeline?.latest_stop_reason ?? latestTermination?.reason ?? 'n/a'}
              </div>
              {blockers.length > 0 ? (
                <div className="mt-2 space-y-1">
                  {blockers.map((item) => (
                    <div key={item} className="text-xs text-slate-600">
                      - {item}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="mt-2 text-xs text-slate-500">No unresolved blockers found.</div>
              )}
            </section>

            {timelineLoading ? <p className="text-sm text-slate-500">Loading timeline...</p> : null}
            {timelineError ? <p className="text-sm text-red-600">Failed to load timeline: {timelineError}</p> : null}
            {!timelineLoading && !timelineError && timelineEvents.length === 0 ? (
              <p className="text-sm text-slate-500">No timeline events recorded yet.</p>
            ) : null}
            {!timelineLoading && !timelineError && (timeline?.events?.length ?? 0) > 60 ? (
              <p className="text-xs text-slate-500">
                Showing most recent 60 events for mobile performance.
              </p>
            ) : null}

            <div className="space-y-2">
              {timelineEvents.map((event) => (
                <div
                  key={event.event_id}
                  className="rounded-md border border-slate-200 bg-white p-3 text-sm [overflow-wrap:anywhere]"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 space-y-1">
                      <div className="font-medium text-slate-900">{event.title}</div>
                      <div className="break-words text-xs text-slate-600">
                        {truncateText(event.summary, 220)}
                      </div>
                    </div>
                    <div className="flex shrink-0 flex-col items-end gap-1">
                      <Badge className="bg-slate-100 text-slate-700">{timelineEventLabel(event.event_type)}</Badge>
                      <span className="text-[11px] text-slate-500">{fmtDate(event.occurred_at)}</span>
                    </div>
                  </div>
                  <div className="mt-2">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleTimelineEvent(event.event_id)}
                    >
                      {expandedTimelineEventIds.has(event.event_id) ? 'Hide details' : 'Show details'}
                    </Button>
                  </div>
                  {expandedTimelineEventIds.has(event.event_id) ? (
                    <div className="mt-2 space-y-2 border-t border-slate-100 pt-2">
                      {event.detail ? (
                        <p className="whitespace-pre-wrap break-words text-xs text-slate-700">
                          {truncateText(event.detail, 2000)}
                        </p>
                      ) : null}
                      {event.caused_by_event_id ? (
                        <p className="text-[11px] text-slate-500">
                          caused by: {event.caused_by_event_id}
                        </p>
                      ) : null}
                      {(event.references ?? []).length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {(event.references ?? []).slice(0, 8).map((reference) => (
                            <Badge
                              key={`${event.event_id}-${reference.reference_type}-${reference.reference_id}`}
                              className="max-w-full bg-slate-100 text-slate-700 [overflow-wrap:anywhere]"
                            >
                              {reference.reference_type}: {truncateText(reference.label ?? reference.reference_id, 120)}
                            </Badge>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="flow" className="space-y-4">
            <section>
              <h4 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">Objective Outcome</h4>
              <div className="rounded-md border border-slate-200 p-3 text-sm">
                <div className="font-medium text-slate-900">
                  {latestTermination?.objective_satisfied ? 'Objective currently satisfied' : 'Objective not yet satisfied'}
                </div>
                <div className="mt-1 text-slate-600">
                  Latest stop reason: {latestTermination?.reason ?? 'n/a'}
                </div>
                {blockers.length > 0 ? (
                  <div className="mt-2 space-y-1">
                    {blockers.map((item) => (
                      <div key={item} className="text-xs text-slate-600">
                        - {item}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="mt-2 text-xs text-slate-500">No unresolved blockers found in persisted checks.</div>
                )}
              </div>
            </section>

            <section>
              <h4 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">Termination snapshots</h4>
              <div className="space-y-2">
                {terminationSnapshots.map((snapshot) => (
                  <div key={`${snapshot.loop_count}-${snapshot.reason}`} className="rounded-md border border-slate-200 p-2 text-sm">
                    <div className="font-medium">Loop {snapshot.loop_count}</div>
                    <div className="text-slate-600">reason: {snapshot.reason}</div>
                    <div className="text-xs text-slate-500">
                      objective: {String(snapshot.objective_satisfied)} · evidence: {String(snapshot.evidence_completeness_sufficient)} · confidence: {String(snapshot.confidence_sufficient)}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section>
              <h4 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">Mandatory checks</h4>
              <div className="space-y-2">
                {mandatoryChecks.map((check) => (
                  <div key={check.check_id} className="rounded-md border border-slate-200 p-2 text-sm">
                    <div className="font-medium">{check.check_id}</div>
                    <div className="text-slate-600">{check.description}</div>
                    <div className="text-xs text-slate-500">
                      passed: {String(check.passed)} · reason: {check.reason ?? 'n/a'}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </TabsContent>

          <TabsContent value="tasks" className="space-y-2">
            {tasks.map((task) => (
              <div key={task.task_id} className="rounded-md border border-slate-200 p-2 text-sm">
                <div className="font-medium">{task.intent}</div>
                <div className="text-slate-600">tool: {task.tool_name} · status: {task.status}</div>
                <div className="text-xs text-slate-500">expected: {task.expected_evidence}</div>
                <div className="text-xs text-slate-500">
                  hypotheses:{' '}
                  {(taskHypothesisLinks[task.task_id] ?? [])
                    .map((id) => {
                      const hypothesis = hypothesisById.get(String(id))
                      return hypothesis ? `${id} (${hypothesis.statement})` : id
                    })
                    .join(', ') || 'none'}
                </div>
                <div className="text-xs text-slate-500">
                  evidence: {(taskEvidenceLinks[task.task_id] ?? []).join(', ') || 'none'}
                </div>
              </div>
            ))}
          </TabsContent>

          <TabsContent value="hypotheses" className="space-y-2">
            {hypotheses.map((hypothesis) => {
              const hypothesisId = String(hypothesis.hypothesis_id)
              const linkedEvidenceIds = evidenceIdsByHypothesis.get(hypothesisId) ?? []
              return (
                <details key={hypothesisId} className="rounded-md border border-slate-200 p-2 text-sm">
                  <summary className="cursor-pointer font-medium text-slate-900">
                    {hypothesis.statement}
                  </summary>
                  <div className="mt-2 space-y-1 text-xs text-slate-600">
                    <div>
                      id: <span className="font-mono">{hypothesisId}</span>
                    </div>
                    <div>status: {hypothesis.status}</div>
                    <div>confidence: {hypothesis.confidence_score}</div>
                    <div>updated: {fmtDate(hypothesis.last_updated_at)}</div>
                    <div>linked evidence: {linkedEvidenceIds.length}</div>
                    {linkedEvidenceIds.map((evidenceId) => {
                      const evidence = evidenceById.get(evidenceId)
                      return (
                        <div key={`${hypothesisId}-${evidenceId}`} className="rounded border border-slate-200 bg-slate-50 p-2">
                          <div className="font-mono text-[11px]">{evidenceId}</div>
                          <div className="text-[11px] text-slate-700">
                            {evidence?.finding_summary ?? 'evidence summary unavailable'}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </details>
              )
            })}
          </TabsContent>

          <TabsContent value="evidence" className="space-y-2">
            {evidenceRecords.map((evidence) => (
              <div key={evidence.evidence_id} className="rounded-md border border-slate-200 p-2 text-sm">
                <div className="font-medium">{evidence.source}</div>
                <div className="text-slate-700">{evidence.finding_summary}</div>
                <div className="text-xs text-slate-500">
                  novelty: {evidence.novelty_signal} · confidence impact: {evidence.confidence_impact}
                </div>
              </div>
            ))}
          </TabsContent>

          <TabsContent value="cognition" className="space-y-2">
            {cognitionRecords.map((record) => (
              <div key={record.record_id} className="rounded-md border border-slate-200 p-2 text-sm">
                <div className="font-medium">{cognitionLabel(record.record_type)}</div>
                <div className="text-xs text-slate-500">{fmtDate(record.timestamp)}</div>
                <p className="mt-1 text-sm text-slate-700">{cognitionSummary(record)}</p>

                <details className="mt-2 rounded border border-slate-200 bg-slate-50 p-2 text-xs">
                  <summary className="cursor-pointer font-medium text-slate-700">
                    Linked Hypotheses ({(record.linked_hypothesis_ids ?? []).length})
                  </summary>
                  <div className="mt-2 space-y-2">
                    {(record.linked_hypothesis_ids ?? []).length === 0 ? (
                      <div className="text-slate-500">No hypothesis links</div>
                    ) : (
                      (record.linked_hypothesis_ids ?? []).map((hypothesisId) => {
                        const hypothesis = hypothesisById.get(String(hypothesisId))
                        const linkedEvidenceIds = evidenceIdsByHypothesis.get(String(hypothesisId)) ?? []
                        return (
                          <div key={`${record.record_id}-${hypothesisId}`} className="rounded border border-slate-200 bg-white p-2">
                            <div className="font-mono text-[11px]">{String(hypothesisId)}</div>
                            <div className="text-slate-700">
                              {hypothesis?.statement ?? 'hypothesis statement unavailable'}
                            </div>
                            <div className="text-slate-500">
                              status: {hypothesis?.status ?? 'n/a'} · confidence: {hypothesis?.confidence_score ?? 'n/a'}
                            </div>
                            {linkedEvidenceIds.length > 0 ? (
                              <div className="mt-1 space-y-1">
                                {linkedEvidenceIds.slice(0, 3).map((evidenceId) => {
                                  const evidence = evidenceById.get(evidenceId)
                                  return (
                                    <div key={`${record.record_id}-${hypothesisId}-${evidenceId}`} className="text-[11px] text-slate-600">
                                      [{evidenceId}] {evidence?.finding_summary ?? 'summary unavailable'}
                                    </div>
                                  )
                                })}
                              </div>
                            ) : null}
                          </div>
                        )
                      })
                    )}
                  </div>
                </details>

                <details className="mt-2 rounded border border-slate-200 bg-slate-50 p-2 text-xs">
                  <summary className="cursor-pointer font-medium text-slate-700">
                    Linked Evidence ({(record.linked_evidence_ids ?? []).length})
                  </summary>
                  <div className="mt-2 space-y-1">
                    {(record.linked_evidence_ids ?? []).length === 0 ? (
                      <div className="text-slate-500">No evidence links</div>
                    ) : (
                      (record.linked_evidence_ids ?? []).map((evidenceId) => {
                        const evidence = evidenceById.get(evidenceId)
                        return (
                          <div key={`${record.record_id}-ev-${evidenceId}`} className="rounded border border-slate-200 bg-white p-2">
                            <div className="font-mono text-[11px]">{evidenceId}</div>
                            <div className="text-slate-700">
                              {evidence?.finding_summary ?? 'evidence summary unavailable'}
                            </div>
                          </div>
                        )
                      })
                    )}
                  </div>
                </details>
              </div>
            ))}
          </TabsContent>

          <TabsContent value="outputs" className="space-y-2">
            {toolOutputs.map((output) => (
              <div key={output.tool_execution_id} className="rounded-md border border-slate-200 p-2 text-sm">
                <div className="mb-2 font-medium">{output.tool_name}</div>
                <pre className="max-h-64 overflow-auto rounded bg-slate-900 p-2 text-xs text-slate-100 sm:max-h-80">
                  {JSON.stringify(output.payload_json, null, 2)}
                </pre>
              </div>
            ))}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
