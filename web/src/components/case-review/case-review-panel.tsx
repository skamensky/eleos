import { useMemo, useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { CaseRunDetail, CaseRunTimeline } from '@/lib/api/client'

import { ReviewWorkspace, truncateText } from './review-workspace'

type TimelineEvent = NonNullable<CaseRunTimeline['events']>[number]
type ToolExecution = NonNullable<CaseRunDetail['tool_executions']>[number]
type ToolOutput = NonNullable<CaseRunDetail['tool_outputs']>[number]
type TaskRow = NonNullable<CaseRunDetail['tasks']>[number]

interface LoopBucket {
  loopKey: string
  label: string
  summary: string
  events: TimelineEvent[]
}

function fmtDate(value: string): string {
  return new Date(value).toLocaleString()
}

function outcomeLabel(status: string): string {
  if (status === 'completed') return 'Resolved'
  if (status === 'escalated') return 'Escalated'
  if (status === 'timed_out') return 'Timed Out'
  if (status === 'running') return 'In Progress'
  return status
}

function topFindings(detail: CaseRunDetail, limit: number): string[] {
  const scored = [...(detail.evidence_records ?? [])]
  scored.sort((a, b) => {
    const aScore = Math.abs(a.confidence_impact) + a.novelty_signal
    const bScore = Math.abs(b.confidence_impact) + b.novelty_signal
    return bScore - aScore
  })
  return scored.slice(0, limit).map((item) => item.finding_summary)
}

function isDecisionEvent(event: TimelineEvent): boolean {
  return (
    event.event_type === 'cognition_recorded' ||
    event.event_type === 'termination_evaluated' ||
    event.event_type === 'task_upserted' ||
    event.event_type === 'final_report_stored'
  )
}

function decisionTone(eventType: TimelineEvent['event_type']): string {
  if (eventType === 'termination_evaluated') return 'bg-amber-100 text-amber-700'
  if (eventType === 'final_report_stored') return 'bg-emerald-100 text-emerald-700'
  if (eventType === 'task_upserted') return 'bg-cyan-100 text-cyan-700'
  return 'bg-slate-100 text-slate-700'
}

function decisionLabel(eventType: TimelineEvent['event_type']): string {
  if (eventType === 'cognition_recorded') return 'Cognition'
  if (eventType === 'termination_evaluated') return 'Termination'
  if (eventType === 'task_upserted') return 'Task Update'
  if (eventType === 'final_report_stored') return 'Final Report'
  return eventType
}

function buildLoops(timeline: CaseRunTimeline | undefined): LoopBucket[] {
  const events = timeline?.events ?? []
  const loops: LoopBucket[] = []
  let currentEvents: TimelineEvent[] = []
  let loopIndex = 0

  for (const event of events) {
    currentEvents.push(event)
    if (event.event_type === 'termination_evaluated') {
      const labelMatch = event.title.match(/Loop\\s+(\\d+)/)
      const label = labelMatch ? `Loop ${labelMatch[1]}` : `Loop ${loopIndex}`
      loops.push({
        loopKey: `loop-${loops.length}`,
        label,
        summary: event.summary,
        events: currentEvents,
      })
      loopIndex += 1
      currentEvents = []
    }
  }

  if (currentEvents.length > 0) {
    loops.push({
      loopKey: `loop-${loops.length}`,
      label: `Loop ${loopIndex}`,
      summary: 'in progress',
      events: currentEvents,
    })
  }

  return loops
}

function parseTaskIdFromInputHandle(inputHandle: string): string | null {
  const match = inputHandle.match(/^input:\/\/([^/]+)\//)
  return match?.[1] ?? null
}

function resolveToolExecutionId(
  event: TimelineEvent,
  eventById: Map<string, TimelineEvent>,
  depth = 0,
): string | null {
  if (depth > 4) return null

  const directRef = (event.references ?? []).find((item) => item.reference_type === 'tool_execution')
  if (directRef) return directRef.reference_id

  if (event.event_type === 'tool_execution') {
    if (event.event_id.startsWith('tool_started:')) return event.event_id.replace('tool_started:', '')
    if (event.event_id.startsWith('tool_finished:')) return event.event_id.replace('tool_finished:', '')
  }

  if (event.caused_by_event_id) {
    const parent = eventById.get(event.caused_by_event_id)
    if (parent) return resolveToolExecutionId(parent, eventById, depth + 1)
  }

  return null
}

export function CaseReviewPanel(): React.JSX.Element {
  return (
    <ReviewWorkspace
      title="Case Review"
      subtitle="Progressive story-first flow with fast decision navigation and optional tool I/O drill-down."
    >
      {(data) => (
        <HybridBody
          detail={data.detail}
          timeline={data.timeline}
          loading={data.loadingDetail}
          timelineError={data.timelineError}
        />
      )}
    </ReviewWorkspace>
  )
}

function HybridBody({
  detail,
  timeline,
  loading,
  timelineError,
}: {
  detail: CaseRunDetail | undefined
  timeline: CaseRunTimeline | undefined
  loading: boolean
  timelineError: string | null
}): React.JSX.Element {
  const loops = useMemo(() => buildLoops(timeline), [timeline])
  const eventById = useMemo(
    () => new Map((timeline?.events ?? []).map((event) => [event.event_id, event])),
    [timeline?.events],
  )
  const decisionEvents = useMemo(
    () => (timeline?.events ?? []).filter(isDecisionEvent),
    [timeline?.events],
  )

  const [expandedLoops, setExpandedLoops] = useState<Set<string>>(new Set())
  const [expandedEventIds, setExpandedEventIds] = useState<Set<string>>(new Set())
  const [selectedDecisionId, setSelectedDecisionId] = useState<string | null>(null)
  const [toolDrawerExecutionId, setToolDrawerExecutionId] = useState<string | null>(null)

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Hybrid Review</CardTitle>
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
          <CardTitle>Hybrid Review</CardTitle>
          <CardDescription>Select a case to inspect the hybrid story + decision workflow.</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  const selectedDecision =
    decisionEvents.find((item) => item.event_id === selectedDecisionId) ?? decisionEvents[0] ?? null

  const blockers = timeline?.unresolved_blockers ?? []
  const findings = topFindings(detail, 3)

  const toolExecutionById = new Map<string, ToolExecution>(
    (detail.tool_executions ?? []).map((item) => [item.tool_execution_id, item]),
  )
  const toolOutputByExecutionId = new Map<string, ToolOutput>(
    (detail.tool_outputs ?? []).map((item) => [item.tool_execution_id, item]),
  )
  const taskById = new Map<string, TaskRow>((detail.tasks ?? []).map((item) => [item.task_id, item]))

  const openToolDrawerFromEvent = (event: TimelineEvent): void => {
    const toolExecutionId = resolveToolExecutionId(event, eventById)
    if (!toolExecutionId) return
    setToolDrawerExecutionId(toolExecutionId)
  }

  const activeExecution = toolDrawerExecutionId
    ? toolExecutionById.get(toolDrawerExecutionId) ?? null
    : null
  const activeOutput = toolDrawerExecutionId
    ? toolOutputByExecutionId.get(toolDrawerExecutionId) ?? null
    : null
  const activeTask = activeExecution
    ? taskById.get(parseTaskIdFromInputHandle(activeExecution.input_handle) ?? '')
    : null

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base sm:text-lg">{detail.summary.objective}</CardTitle>
          <CardDescription>
            Story-first brief and progression with a linked decision rail and optional tool I/O deep inspection.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Badge>{outcomeLabel(detail.summary.status)}</Badge>
            <Badge>{detail.summary.case_class}</Badge>
            <Badge>loops: {detail.summary.loop_count}</Badge>
            <Badge>updated: {fmtDate(detail.summary.updated_at)}</Badge>
          </div>

          <section className="grid gap-3 lg:grid-cols-2">
            <div className="rounded-md border border-slate-200 p-3">
              <h4 className="mb-1 text-sm font-semibold text-slate-900">Why This Outcome</h4>
              {blockers.length > 0 ? (
                <div className="space-y-1 text-sm text-slate-700">
                  {blockers.slice(0, 4).map((item) => (
                    <p key={item}>- {item}</p>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-600">No unresolved blockers recorded.</p>
              )}
            </div>
            <div className="rounded-md border border-slate-200 p-3">
              <h4 className="mb-1 text-sm font-semibold text-slate-900">Top Findings</h4>
              {findings.length > 0 ? (
                <div className="space-y-1 text-sm text-slate-700">
                  {findings.map((item) => (
                    <p key={item}>- {truncateText(item, 220)}</p>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-600">No evidence findings recorded.</p>
              )}
            </div>
          </section>
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.7fr)_minmax(24rem,1fr)]">
        <Card>
          <CardHeader>
            <CardTitle>Loop Story</CardTitle>
            <CardDescription>
              Default shows loop summaries only. Expand loop or event details only when needed.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {timelineError ? <p className="text-sm text-red-600">Failed to load timeline: {timelineError}</p> : null}
            {loops.length === 0 ? <p className="text-sm text-slate-600">No loop data available.</p> : null}

            {loops.map((loop) => {
              const isExpanded = expandedLoops.has(loop.loopKey)
              return (
                <div key={loop.loopKey} className="rounded-md border border-slate-200 p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{loop.label}</p>
                      <p className="text-xs text-slate-600">{truncateText(loop.summary, 140)}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className="bg-slate-100 text-slate-700">events: {loop.events.length}</Badge>
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        onClick={() =>
                          setExpandedLoops((previous) => {
                            const next = new Set(previous)
                            if (next.has(loop.loopKey)) next.delete(loop.loopKey)
                            else next.add(loop.loopKey)
                            return next
                          })
                        }
                      >
                        {isExpanded ? 'Collapse' : 'Expand'}
                      </Button>
                    </div>
                  </div>

                  {isExpanded ? (
                    <div className="mt-3 space-y-2">
                      {loop.events.map((event) => {
                        const eventExpanded = expandedEventIds.has(event.event_id)
                        const highlighted = selectedDecision?.event_id === event.event_id
                        const toolExecutionId = resolveToolExecutionId(event, eventById)
                        return (
                          <div
                            key={event.event_id}
                            className={
                              highlighted
                                ? 'rounded border border-cyan-300 bg-cyan-50 p-2'
                                : 'rounded border border-slate-200 bg-slate-50 p-2'
                            }
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="min-w-0">
                                <p className="text-sm font-medium text-slate-900">{event.title}</p>
                                <p className="text-xs text-slate-600">{truncateText(event.summary, 180)}</p>
                              </div>
                              <span className="shrink-0 text-[11px] text-slate-500">{fmtDate(event.occurred_at)}</span>
                            </div>
                            <div className="mt-1 flex flex-wrap gap-2">
                              <Button
                                type="button"
                                size="sm"
                                variant="ghost"
                                onClick={() =>
                                  setExpandedEventIds((previous) => {
                                    const next = new Set(previous)
                                    if (next.has(event.event_id)) next.delete(event.event_id)
                                    else next.add(event.event_id)
                                    return next
                                  })
                                }
                              >
                                {eventExpanded ? 'Hide details' : 'Show details'}
                              </Button>
                              {toolExecutionId ? (
                                <Button
                                  type="button"
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => openToolDrawerFromEvent(event)}
                                >
                                  View Tool Call I/O
                                </Button>
                              ) : null}
                            </div>
                            {eventExpanded ? (
                              <div className="mt-2 border-t border-slate-200 pt-2 text-xs text-slate-700">
                                {event.detail ? (
                                  <p className="whitespace-pre-wrap break-words">
                                    {truncateText(event.detail, 1800)}
                                  </p>
                                ) : null}
                                {(event.references ?? []).slice(0, 8).map((reference) => (
                                  <p key={`${event.event_id}-${reference.reference_type}-${reference.reference_id}`}>
                                    - {reference.reference_type}: {reference.label ?? reference.reference_id}
                                  </p>
                                ))}
                              </div>
                            ) : null}
                          </div>
                        )
                      })}
                    </div>
                  ) : null}
                </div>
              )
            })}
          </CardContent>
        </Card>

        <Card className="xl:sticky xl:top-4 xl:h-fit">
          <CardHeader>
            <CardTitle>Decision Table</CardTitle>
            <CardDescription>
              Fast decision navigation. Click a row to inspect rationale and jump in the story.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="max-h-[22rem] overflow-auto rounded-md border border-slate-200">
              <div className="space-y-1 p-2">
                {decisionEvents.map((event) => (
                  <button
                    key={event.event_id}
                    type="button"
                    className={
                      selectedDecision?.event_id === event.event_id
                        ? 'w-full rounded border border-cyan-300 bg-cyan-50 p-2 text-left'
                        : 'w-full rounded border border-slate-200 bg-white p-2 text-left'
                    }
                    onClick={() => {
                      setSelectedDecisionId(event.event_id)
                      const loop = loops.find((candidate) =>
                        candidate.events.some((candidateEvent) => candidateEvent.event_id === event.event_id),
                      )
                      if (loop) {
                        setExpandedLoops((previous) => {
                          const next = new Set(previous)
                          next.add(loop.loopKey)
                          return next
                        })
                      }
                    }}
                  >
                    <div className="mb-1 flex items-center gap-2">
                      <Badge className={decisionTone(event.event_type)}>{decisionLabel(event.event_type)}</Badge>
                      <span className="text-[11px] text-slate-500">{fmtDate(event.occurred_at)}</span>
                    </div>
                    <p className="text-xs text-slate-700">{truncateText(event.summary, 150)}</p>
                  </button>
                ))}
              </div>
            </div>

            {selectedDecision ? (
              <div className="rounded-md border border-slate-200 p-3">
                <p className="text-sm font-medium text-slate-900">{selectedDecision.title}</p>
                <p className="mt-1 text-sm text-slate-700">{truncateText(selectedDecision.summary, 240)}</p>
                {selectedDecision.detail ? (
                  <p className="mt-2 whitespace-pre-wrap break-words text-xs text-slate-600">
                    {truncateText(selectedDecision.detail, 900)}
                  </p>
                ) : null}
                {resolveToolExecutionId(selectedDecision, eventById) ? (
                  <Button
                    className="mt-2"
                    type="button"
                    size="sm"
                    variant="secondary"
                    onClick={() => openToolDrawerFromEvent(selectedDecision)}
                  >
                    View Tool Call I/O
                  </Button>
                ) : null}
              </div>
            ) : (
              <p className="text-sm text-slate-600">Select a decision event to inspect it.</p>
            )}
          </CardContent>
        </Card>
      </div>

      <Dialog open={toolDrawerExecutionId !== null} onOpenChange={(open) => (!open ? setToolDrawerExecutionId(null) : null)}>
        <DialogContent className="left-0 top-0 h-screen w-screen max-w-none -translate-x-0 -translate-y-0 rounded-none p-4 lg:left-auto lg:right-0 lg:w-[52rem] lg:p-5">
          <DialogHeader>
            <DialogTitle>Tool Call I/O</DialogTitle>
            <DialogDescription className="sr-only">
              Inspect tool execution input context, output payload, and raw execution JSON.
            </DialogDescription>
          </DialogHeader>

          {!activeExecution ? (
            <p className="text-sm text-slate-600">Tool execution record not found.</p>
          ) : (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                <Badge>{activeExecution.tool_name}</Badge>
                <Badge className="bg-slate-100 text-slate-700">{activeExecution.status}</Badge>
                <Badge className="bg-slate-100 text-slate-700">
                  {activeExecution.duration_ms ?? 'n/a'}ms
                </Badge>
              </div>

              <Tabs defaultValue="input">
                <TabsList>
                  <TabsTrigger value="input">Input</TabsTrigger>
                  <TabsTrigger value="output">Output</TabsTrigger>
                  <TabsTrigger value="raw">Raw JSON</TabsTrigger>
                </TabsList>

                <TabsContent value="input" className="space-y-2">
                  <div className="rounded-md border border-slate-200 p-3">
                    <p className="text-xs text-slate-500">input_handle</p>
                    <p className="break-words font-mono text-xs text-slate-700">{activeExecution.input_handle}</p>
                  </div>

                  {activeTask ? (
                    <div className="rounded-md border border-slate-200 p-3">
                      <p className="mb-1 text-sm font-semibold text-slate-900">Resolved Task Context</p>
                      <div className="space-y-1 text-sm text-slate-700">
                        <p>- intent: {activeTask.intent}</p>
                        <p>- objective: {activeTask.tool_input_objective}</p>
                        <p>- step: {activeTask.tool_input_step ?? 'n/a'}</p>
                        <p>- reason: {activeTask.tool_input_reason ?? 'n/a'}</p>
                        <p>- evidence_id: {activeTask.tool_input_evidence_id ?? 'n/a'}</p>
                        <p>- expected evidence: {activeTask.expected_evidence}</p>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-slate-600">No task context was resolved from input handle.</p>
                  )}
                </TabsContent>

                <TabsContent value="output">
                  <div className="rounded-md border border-slate-200 p-3">
                    {activeOutput ? (
                      <pre className="max-h-[50vh] overflow-auto rounded bg-slate-900 p-3 text-xs text-slate-100">
                        {JSON.stringify(activeOutput.payload_json, null, 2)}
                      </pre>
                    ) : (
                      <p className="text-sm text-slate-600">No tool output payload stored for this execution.</p>
                    )}
                  </div>
                </TabsContent>

                <TabsContent value="raw" className="space-y-2">
                  <div className="rounded-md border border-slate-200 p-3">
                    <p className="mb-1 text-xs text-slate-500">execution</p>
                    <pre className="max-h-[22vh] overflow-auto rounded bg-slate-900 p-3 text-xs text-slate-100">
                      {JSON.stringify(activeExecution, null, 2)}
                    </pre>
                  </div>
                  <div className="rounded-md border border-slate-200 p-3">
                    <p className="mb-1 text-xs text-slate-500">output</p>
                    <pre className="max-h-[22vh] overflow-auto rounded bg-slate-900 p-3 text-xs text-slate-100">
                      {JSON.stringify(activeOutput?.payload_json ?? null, null, 2)}
                    </pre>
                  </div>
                </TabsContent>
              </Tabs>
            </div>
          )}

          <div className="mt-4">
            <DialogClose asChild>
              <Button type="button" variant="secondary">
                Close
              </Button>
            </DialogClose>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
