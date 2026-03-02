import { useMemo, useState } from 'react'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  createPlaybook,
  getPlaybookFormOptions,
  listPlaybooks,
  type PlaybookCreateRequest,
  type PlaybookView,
} from '@/lib/api/client'

type PlaybookState = PlaybookCreateRequest
type PlaybookSteps = NonNullable<PlaybookCreateRequest['steps']>
type PlaybookStepDraft = PlaybookSteps[number]

const defaultPayload: PlaybookCreateRequest = {
  version: '1.0.0',
  title: '',
  status: 'active',
  enforcement_mode: 'suggestive',
  applicable_case_classes: [],
  objective_template: '',
  created_by: 'ui',
  steps: [],
}

const defaultStepDraft: PlaybookStepDraft = {
  step_order: 1,
  step_id: '',
  name: '',
  goal: '',
  tool_selector: '',
  required: true,
  order_constraint: 'sequential',
  preconditions: [],
  expected_evidence: '',
  completion_check: '',
  failure_action: 'retry',
}

function slugifyStepId(value: string): string {
  const slug = value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
  return slug || 'step'
}

export function PlaybooksPanel(): React.JSX.Element {
  const [payload, setPayload] = useState<PlaybookState>(defaultPayload)
  const [stepDraft, setStepDraft] = useState<PlaybookStepDraft>(defaultStepDraft)
  const [preconditionDraft, setPreconditionDraft] = useState('')
  const queryClient = useQueryClient()

  const playbooksQuery = useQuery({
    queryKey: ['playbooks'],
    queryFn: () => listPlaybooks(200),
  })

  const optionsQuery = useQuery({
    queryKey: ['playbook-form-options'],
    queryFn: () => getPlaybookFormOptions(),
  })

  const createMutation = useMutation({
    mutationFn: (body: PlaybookCreateRequest) => createPlaybook(body),
    onSuccess: async () => {
      setPayload(defaultPayload)
      setStepDraft(defaultStepDraft)
      setPreconditionDraft('')
      await queryClient.invalidateQueries({ queryKey: ['playbooks'] })
    },
  })

  const tools = optionsQuery.data?.tools ?? []
  const categories = optionsQuery.data?.categories ?? []
  const enforcementModes = optionsQuery.data?.enforcement_modes ?? ['suggestive', 'mandatory']
  const orderConstraints = optionsQuery.data?.order_constraints ?? ['sequential']
  const failureActions = optionsQuery.data?.failure_actions ?? ['retry', 'branch', 'escalate']
  const statuses = optionsQuery.data?.statuses ?? ['active']

  const fullPlaybooks = useMemo<PlaybookView[]>(() => playbooksQuery.data ?? [], [playbooksQuery.data])

  function toggleCategory(categoryId: string): void {
    const current = new Set(payload.applicable_case_classes ?? [])
    if (current.has(categoryId)) current.delete(categoryId)
    else current.add(categoryId)
    setPayload((previous: PlaybookState) => ({
      ...previous,
      applicable_case_classes: Array.from(current),
    }))
  }

  function addPrecondition(): void {
    const value = preconditionDraft.trim()
    if (!value) return
    if ((stepDraft.preconditions ?? []).includes(value)) return
    setStepDraft((previous: PlaybookStepDraft) => ({
      ...previous,
      preconditions: [...(previous.preconditions ?? []), value],
    }))
    setPreconditionDraft('')
  }

  function removePrecondition(value: string): void {
    setStepDraft((previous: PlaybookStepDraft) => ({
      ...previous,
      preconditions: (previous.preconditions ?? []).filter((item) => item !== value),
    }))
  }

  function addStepToPlaybook(): void {
    if (!stepDraft.name.trim() || !stepDraft.goal.trim() || !stepDraft.tool_selector.trim()) {
      return
    }
    const nextOrder = (payload.steps?.length ?? 0) + 1
    const generatedId = `step_${nextOrder}_${slugifyStepId(stepDraft.name)}`
    const step: PlaybookStepDraft = {
      ...stepDraft,
      step_order: nextOrder,
      step_id: generatedId,
    }
    setPayload((previous: PlaybookState) => ({
      ...previous,
      steps: [...(previous.steps ?? []), step],
    }))
    setStepDraft({
      ...defaultStepDraft,
      step_order: nextOrder + 1,
      tool_selector: stepDraft.tool_selector,
    })
  }

  function removeStep(index: number): void {
    setPayload((previous: PlaybookState) => {
      const remaining = (previous.steps ?? []).filter((_, stepIndex) => stepIndex !== index)
      return {
        ...previous,
        steps: remaining.map((step, stepIndex) => ({
          ...step,
          step_order: stepIndex + 1,
        })),
      }
    })
  }

  function submit(event: React.FormEvent<HTMLFormElement>): void {
    event.preventDefault()
    createMutation.mutate(payload)
  }

  return (
    <div className="grid gap-4 2xl:grid-cols-[1fr_1.4fr]">
      <Card>
        <CardHeader>
          <CardTitle>Playbook Builder</CardTitle>
          <CardDescription>Create playbooks with categories, guided steps, and validated tool selection.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={submit}>
            <div className="space-y-1">
              <Label htmlFor="playbook-title">Title</Label>
              <Input
                id="playbook-title"
                placeholder="Support Investigation Baseline"
                value={payload.title}
                onChange={(event) =>
                  setPayload((previous: PlaybookState) => ({ ...previous, title: event.target.value }))
                }
              />
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1">
                <Label htmlFor="playbook-version">Version</Label>
                <Input
                  id="playbook-version"
                  value={payload.version}
                  onChange={(event) =>
                    setPayload((previous: PlaybookState) => ({ ...previous, version: event.target.value }))
                  }
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="playbook-status">Status</Label>
                <select
                  id="playbook-status"
                  className="flex h-9 w-full rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-900"
                  value={payload.status}
                  onChange={(event) =>
                    setPayload((previous: PlaybookState) => ({ ...previous, status: event.target.value }))
                  }
                >
                  {statuses.map((status) => (
                    <option key={status} value={status}>
                      {status}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="space-y-1">
              <Label htmlFor="playbook-enforcement-mode">Enforcement Mode</Label>
              <select
                id="playbook-enforcement-mode"
                className="flex h-9 w-full rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-900"
                value={payload.enforcement_mode}
                onChange={(event) =>
                  setPayload((previous: PlaybookState) => ({ ...previous, enforcement_mode: event.target.value }))
                }
              >
                {enforcementModes.map((mode) => (
                  <option key={mode} value={mode}>
                    {mode}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <Label>Applicable Cases</Label>
              <div className="flex flex-wrap gap-2">
                {categories.map((category) => {
                  const selected = (payload.applicable_case_classes ?? []).includes(category.category_id)
                  return (
                    <button
                      key={category.category_id}
                      type="button"
                      className={
                        selected
                          ? 'rounded-full border border-cyan-300 bg-cyan-50 px-3 py-1 text-xs text-cyan-700'
                          : 'rounded-full border border-slate-300 bg-white px-3 py-1 text-xs text-slate-700'
                      }
                      onClick={() => toggleCategory(category.category_id)}
                      title={category.description}
                    >
                      {category.category_id}
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="space-y-1">
              <Label htmlFor="playbook-objective-template">Objective Template</Label>
              <Textarea
                id="playbook-objective-template"
                className="min-h-20"
                placeholder="Investigate reported service issue for customer context"
                value={payload.objective_template}
                onChange={(event) =>
                  setPayload((previous: PlaybookState) => ({ ...previous, objective_template: event.target.value }))
                }
              />
            </div>

            <div className="rounded-md border border-slate-200 p-3">
              <div className="mb-3 text-sm font-semibold text-slate-900">Add Step</div>
              <div className="space-y-3">
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-1">
                    <Label htmlFor="step-name">Step Name</Label>
                    <Input
                      id="step-name"
                      value={stepDraft.name}
                      onChange={(event) =>
                        setStepDraft((previous: PlaybookStepDraft) => ({ ...previous, name: event.target.value }))
                      }
                    />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="step-tool">Tool</Label>
                    <select
                      id="step-tool"
                      className="flex h-9 w-full rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-900"
                      value={stepDraft.tool_selector}
                      onChange={(event) =>
                        setStepDraft((previous: PlaybookStepDraft) => ({
                          ...previous,
                          tool_selector: event.target.value,
                        }))
                      }
                    >
                      <option value="">Select tool</option>
                      {tools.map((tool) => (
                        <option key={tool.tool_name} value={tool.tool_name}>
                          {tool.tool_name}
                        </option>
                      ))}
                    </select>
                    {stepDraft.tool_selector ? (
                      <p className="text-xs text-slate-500">
                        {tools.find((tool) => tool.tool_name === stepDraft.tool_selector)?.function_description ?? ''}
                      </p>
                    ) : null}
                  </div>
                </div>

                <div className="space-y-1">
                  <Label htmlFor="step-goal">Goal</Label>
                  <Textarea
                    id="step-goal"
                    className="min-h-16"
                    value={stepDraft.goal}
                    onChange={(event) =>
                      setStepDraft((previous: PlaybookStepDraft) => ({ ...previous, goal: event.target.value }))
                    }
                  />
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-1">
                    <Label htmlFor="step-order-constraint">Order Constraint</Label>
                    <select
                      id="step-order-constraint"
                      className="flex h-9 w-full rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-900"
                      value={stepDraft.order_constraint}
                      onChange={(event) =>
                        setStepDraft((previous: PlaybookStepDraft) => ({
                          ...previous,
                          order_constraint: event.target.value,
                        }))
                      }
                    >
                      {orderConstraints.map((constraint) => (
                        <option key={constraint} value={constraint}>
                          {constraint}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="step-failure-action">Failure Action</Label>
                    <select
                      id="step-failure-action"
                      className="flex h-9 w-full rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-900"
                      value={stepDraft.failure_action}
                      onChange={(event) =>
                        setStepDraft((previous: PlaybookStepDraft) => ({
                          ...previous,
                          failure_action: event.target.value,
                        }))
                      }
                    >
                      {failureActions.map((action) => (
                        <option key={action} value={action}>
                          {action}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-1">
                    <Label htmlFor="step-expected-evidence">Expected Evidence</Label>
                    <Textarea
                      id="step-expected-evidence"
                      className="min-h-16"
                      value={stepDraft.expected_evidence}
                      onChange={(event) =>
                        setStepDraft((previous: PlaybookStepDraft) => ({
                          ...previous,
                          expected_evidence: event.target.value,
                        }))
                      }
                    />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="step-completion-check">Completion Check</Label>
                    <Textarea
                      id="step-completion-check"
                      className="min-h-16"
                      value={stepDraft.completion_check}
                      onChange={(event) =>
                        setStepDraft((previous: PlaybookStepDraft) => ({
                          ...previous,
                          completion_check: event.target.value,
                        }))
                      }
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Preconditions</Label>
                  <div className="flex gap-2">
                    <Input
                      value={preconditionDraft}
                      onChange={(event) => setPreconditionDraft(event.target.value)}
                      placeholder="Add precondition"
                    />
                    <Button type="button" variant="secondary" onClick={addPrecondition}>
                      Add
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {(stepDraft.preconditions ?? []).map((item) => (
                      <button
                        key={item}
                        type="button"
                        className="rounded-full border border-slate-300 bg-slate-50 px-2 py-1 text-xs text-slate-700"
                        onClick={() => removePrecondition(item)}
                      >
                        {item} x
                      </button>
                    ))}
                  </div>
                </div>

                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={stepDraft.required}
                    onChange={(event) =>
                      setStepDraft((previous: PlaybookStepDraft) => ({
                        ...previous,
                        required: event.target.checked,
                      }))
                    }
                  />
                  Required step
                </label>

                <Button type="button" variant="secondary" onClick={addStepToPlaybook}>
                  Add Step To Playbook
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <div className="text-sm font-semibold text-slate-900">Step Preview</div>
              {(payload.steps ?? []).length === 0 ? (
                <p className="text-sm text-slate-500">No steps yet.</p>
              ) : (
                (payload.steps ?? []).map((step, index) => (
                  <div key={`${step.step_id}-${step.step_order}`} className="rounded-md border border-slate-200 p-2 text-sm">
                    <div className="font-medium">
                      {step.step_order}. {step.name}
                    </div>
                    <div className="text-xs text-slate-600">tool: {step.tool_selector}</div>
                    <div className="text-xs text-slate-600">{step.goal}</div>
                    <div className="mt-1">
                      <Button type="button" size="sm" variant="ghost" onClick={() => removeStep(index)}>
                        Remove
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center">
              <Button className="w-full sm:w-auto" type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Creating...' : 'Create Playbook'}
              </Button>
              {createMutation.isError ? (
                <span className="text-sm text-red-600">{String(createMutation.error)}</span>
              ) : null}
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Playbooks</CardTitle>
          <CardDescription>Full playbook definitions, including all configured steps.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {playbooksQuery.isLoading ? <p className="text-sm text-slate-500">Loading playbooks...</p> : null}
          {playbooksQuery.isError ? (
            <p className="text-sm text-red-600">Failed to load playbooks: {String(playbooksQuery.error)}</p>
          ) : null}
          {!playbooksQuery.isLoading && !playbooksQuery.isError && fullPlaybooks.length === 0 ? (
            <p className="text-sm text-slate-500">No playbooks in registry.</p>
          ) : null}

          {fullPlaybooks.map((playbook) => (
            <details key={`${playbook.playbook_id}-${playbook.version}`} className="rounded-md border border-slate-200 p-3">
              <summary className="cursor-pointer">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium text-slate-900">{playbook.title}</span>
                  <Badge>{playbook.version}</Badge>
                  <Badge>{playbook.status}</Badge>
                  <Badge>{playbook.enforcement_mode}</Badge>
                </div>
              </summary>
              <div className="mt-3 space-y-3 text-sm">
                <div className="text-slate-700">{playbook.objective_template}</div>
                <div className="flex flex-wrap gap-2">
                  {(playbook.applicable_case_classes ?? []).map((category) => (
                    <Badge key={`${playbook.playbook_id}-${category}`} className="bg-slate-100 text-slate-700">
                      {category}
                    </Badge>
                  ))}
                </div>
                <div className="space-y-2">
                  {(playbook.steps ?? []).map((step) => (
                    <div key={`${playbook.playbook_id}-${playbook.version}-${step.step_id}`} className="rounded border border-slate-200 p-2">
                      <div className="font-medium text-slate-900">{step.name}</div>
                      <div className="text-xs text-slate-600">
                        id: {step.step_id} · tool: {step.tool_selector} · required: {String(step.required)}
                      </div>
                      <div className="mt-1 text-xs text-slate-700">goal: {step.goal}</div>
                      <div className="mt-1 text-xs text-slate-700">expected evidence: {step.expected_evidence}</div>
                      <div className="mt-1 text-xs text-slate-700">completion check: {step.completion_check}</div>
                      <div className="mt-1 text-xs text-slate-700">failure action: {step.failure_action}</div>
                      <div className="mt-1 text-xs text-slate-700">
                        preconditions: {(step.preconditions ?? []).join(', ') || 'none'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </details>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
