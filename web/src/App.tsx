import { CaseReviewPanel } from '@/components/case-review/case-review-panel'
import { DashboardPanel } from '@/components/dashboard-panel'
import { PlaybooksPanel } from '@/components/playbooks-panel'
import { Button } from '@/components/ui/button'
import { useUiStore } from '@/lib/store/ui-store'

function App(): React.JSX.Element {
  const activeView = useUiStore((state) => state.activeView)
  const setActiveView = useUiStore((state) => state.setActiveView)

  const title =
    activeView === 'dashboard'
      ? 'Eleos Operations Console'
      : activeView === 'case-review'
        ? 'Case Review'
        : 'Playbooks'

  const subtitle =
    activeView === 'dashboard'
      ? 'Open case review or playbook management from a single desktop and mobile entry point.'
      : activeView === 'case-review'
        ? 'Progressive story-first case review with decision navigation and on-demand tool I/O.'
        : 'Create and inspect playbooks used by investigations.'

  return (
    <main className="min-h-screen bg-slate-50 px-3 py-4 text-slate-900 sm:px-5 sm:py-6">
      <div className="mx-auto max-w-[1600px] space-y-4 sm:space-y-6">
        <header className="space-y-2">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-2">
              <h1 className="text-xl font-semibold tracking-tight sm:text-2xl">{title}</h1>
              <p className="text-sm leading-relaxed text-slate-600">{subtitle}</p>
            </div>
            {activeView !== 'dashboard' ? (
              <Button type="button" variant="secondary" onClick={() => setActiveView('dashboard')}>
                Back To Dashboard
              </Button>
            ) : null}
          </div>
        </header>

        {activeView === 'dashboard' ? (
          <DashboardPanel
            onOpenCaseReview={() => setActiveView('case-review')}
            onOpenPlaybooks={() => setActiveView('playbooks')}
          />
        ) : null}
        {activeView === 'case-review' ? <CaseReviewPanel /> : null}
        {activeView === 'playbooks' ? <PlaybooksPanel /> : null}
      </div>
    </main>
  )
}

export default App
