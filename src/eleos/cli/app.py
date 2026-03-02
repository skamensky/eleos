import json

import typer
from rich.console import Console

from eleos.core.runtime import InvestigationRuntime
from eleos.models.case import InvestigationRequest
from eleos.models.enums import Mode, PlaybookPolicy

app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)
console = Console()
_runtime: InvestigationRuntime | None = None


def get_runtime() -> InvestigationRuntime:
    global _runtime
    if _runtime is None:
        _runtime = InvestigationRuntime()
    return _runtime


@app.callback()
def main() -> None:
    """Run autonomous operational investigation workflows."""


@app.command("investigate")
def investigate(
    objective: str = typer.Argument(..., help="Top-level investigation objective"),
    mode: Mode = typer.Option(Mode.DEEP_INVESTIGATION, "--mode", help="Runtime investigation mode"),
    policy: PlaybookPolicy = typer.Option(
        PlaybookPolicy.SUGGESTIVE,
        "--policy",
        help="Playbook enforcement mode",
    ),
    timeout_minutes: int = typer.Option(120, "--timeout-minutes", min=1, help="Timeout budget"),
) -> None:
    request = InvestigationRequest(
        objective=objective,
        mode=mode,
        playbook_policy=policy,
        timeout_minutes=timeout_minutes,
    )
    report = get_runtime().run(request)
    console.print_json(json.dumps(report.model_dump(mode="json")))


if __name__ == "__main__":
    app()
