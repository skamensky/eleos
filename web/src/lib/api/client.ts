import type { components, operations } from '@/lib/api/generated'

type JsonRequestBody<T extends { requestBody?: object }> = T extends {
  requestBody: { content: { 'application/json': infer Body } }
}
  ? Body
  : never

type JsonResponse<T extends { responses: object }, Code extends keyof T['responses']> = T['responses'][Code] extends {
  content: { 'application/json': infer Body }
}
  ? Body
  : never

type RunInvestigationOperation = operations['run_investigation_v1_investigations_post']
type ListCaseRunsOperation = operations['get_case_runs_v1_case_runs_get']
type GetCaseRunOperation = operations['get_case_run_v1_case_runs__case_id__get']
type GetCaseRunTimelineOperation = operations['get_case_run_timeline_route_v1_case_runs__case_id__timeline_get']
type ListPlaybooksOperation = operations['get_playbooks_v1_playbooks_get']
type PlaybookFormOptionsOperation = operations['get_playbook_options_v1_playbook_form_options_get']
type CreatePlaybookOperation = operations['post_playbook_v1_playbooks_post']

export type InvestigationRequest = JsonRequestBody<RunInvestigationOperation>
export type InvestigationRunResponse = JsonResponse<RunInvestigationOperation, 200>
export type PlaybookCreateRequest = JsonRequestBody<CreatePlaybookOperation>
export type PlaybookView = JsonResponse<ListPlaybooksOperation, 200>[number]
export type PlaybookFormOptions = JsonResponse<PlaybookFormOptionsOperation, 200>
export type CaseRunSummary = JsonResponse<ListCaseRunsOperation, 200>[number]
export type CaseRunDetail = JsonResponse<GetCaseRunOperation, 200>
export type CaseRunTimeline = JsonResponse<GetCaseRunTimelineOperation, 200>
export type FinalReport = components['schemas']['FinalReportStoredResponse']

function defaultApiBaseUrl(): string {
  return ''
}

const API_BASE_URL = ((import.meta.env.VITE_API_BASE_URL as string | undefined) ?? defaultApiBaseUrl()).replace(
  /\/$/,
  '',
)

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'content-type': 'application/json',
      ...(init?.headers ?? {}),
    },
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(`API ${response.status}: ${text}`)
  }

  return (await response.json()) as T
}

export function listCaseRuns(limit = 100): Promise<CaseRunSummary[]> {
  return request<CaseRunSummary[]>(`/v1/case-runs?limit=${limit}`)
}

export function getCaseRun(caseId: string): Promise<CaseRunDetail> {
  return request<CaseRunDetail>(`/v1/case-runs/${caseId}`)
}

export function getCaseRunTimeline(caseId: string): Promise<CaseRunTimeline> {
  return request<CaseRunTimeline>(`/v1/case-runs/${caseId}/timeline`)
}

export function listPlaybooks(limit = 100): Promise<PlaybookView[]> {
  return request<PlaybookView[]>(`/v1/playbooks?limit=${limit}`)
}

export function getPlaybookFormOptions(): Promise<PlaybookFormOptions> {
  return request<PlaybookFormOptions>('/v1/playbook-form-options')
}

export function createPlaybook(payload: PlaybookCreateRequest): Promise<PlaybookView> {
  return request<PlaybookView>('/v1/playbooks', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function runInvestigation(payload: InvestigationRequest): Promise<InvestigationRunResponse> {
  return request<InvestigationRunResponse>('/v1/investigations', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
