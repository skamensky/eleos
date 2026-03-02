import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface DashboardPanelProps {
  onOpenCaseReview: () => void
  onOpenPlaybooks: () => void
}

export function DashboardPanel({ onOpenCaseReview, onOpenPlaybooks }: DashboardPanelProps): React.JSX.Element {
  return (
    <section className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Case Review</CardTitle>
          <CardDescription>
            Review completed or in-flight cases with story-first flow, decision trace, and optional tool I/O details.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button type="button" onClick={onOpenCaseReview}>
            Open Case Review
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Playbooks</CardTitle>
          <CardDescription>
            Create and inspect playbooks, including category applicability and required/suggested tools.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button type="button" variant="secondary" onClick={onOpenPlaybooks}>
            Open Playbooks
          </Button>
        </CardContent>
      </Card>
    </section>
  )
}
