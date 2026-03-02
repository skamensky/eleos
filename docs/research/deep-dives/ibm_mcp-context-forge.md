# IBM/mcp-context-forge

Status: Deep dive draft (pending)
Source: https://github.com/IBM/mcp-context-forge
Date: 2026-02-25

## 1) What It Is (Generic)
- A governance-heavy MCP/A2A/REST gateway and registry layer.
- Normalizes tool access through a central control point (auth, routing, policy hooks, observability).
- Focuses on secure tool federation and operational control, not agent reasoning logic.

## 2) Core Strategies Observed
- Route-level permission mapping and token scoping middleware enforce access boundaries.
- Tool invocation path has explicit phases: lookup, access checks, schema checks, plugin hooks, execution, post-hooks, metrics.
- Plugin framework supports ordered hooks (`tool_pre_invoke`, `tool_post_invoke`, etc.) with `enforce`, `permissive`, and `disabled` modes.
- Plugins can block requests in enforce mode and carry local/global context across hook chains.
- Extensive audit and observability instrumentation around tool calls, including span lifecycle and structured logs.
- Gateway mode separation (`cache` vs `direct_proxy`) with explicit header-based routing plus access validation.

## 3) Requirement Mapping (`R1-R8`)
| Requirement | Score (0-3) | Notes |
|---|---:|---|
| `R1` Goal loop | 1 | Strong execution control for tool calls, but no native goal/hypothesis planning loop. |
| `R2` Dynamic task graph | 0 | No first-class investigative task graph model. |
| `R3` Evidence ledger | 1 | Good telemetry/audit artifacts, but not a hypothesis-linked evidence ledger. |
| `R4` Controlled exploration | 2 | Strong policy/rate/timeout controls at gateway layer; novelty/EV reasoning absent. |
| `R5` Termination criteria | 1 | Per-call timeouts/errors exist; no case-level completion/termination contract. |
| `R6` Tool routing/control | 3 | Very strong: RBAC, scoping, path permissions, hook policies, auth handling. |
| `R7` Meandering control | 0 | No competing-hypothesis or uncertainty-reduction semantics. |
| `R8` Multi-role architecture | 1 | Separation of concerns exists (middleware/service/plugins), but not explicit Router/Planner/Executor/Critic roles. |

## 4) Borrowable Ideas
- Put tool governance outside prompt text via policy middleware + permission maps.
- Use pre/post invoke hooks with enforce/permissive modes for safety/compliance controls.
- Add fail-closed routing defaults for privileged paths.
- Attach structured observability + audit metadata to every tool invocation.
- Keep direct-proxy modes explicitly gated by access checks to avoid bypasses.

## 5) Gaps vs Our Needs
- No native hypothesis tracking, confidence deltas, or investigation task ledger.
- No novelty or expected-value branch gating logic.
- No case-type completion matrix (e.g., IAM/network/log mandatory steps).

## 6) Transfer Risk
- Moderate: patterns are strong but gateway-centric; must be adapted into an investigation-control layer.
- Moderate integration complexity if your current tool stack is not MCP-first.

## 7) Verdict
- Status: `Keep`
- Reason: Best-in-class governance and tool-control patterns for `R6`, useful as a policy shell around your investigative loop.

## 8) Evidence References
- `mcpgateway/services/tool_service.py`
- `mcpgateway/middleware/token_scoping.py`
- `mcpgateway/auth.py`
- `mcpgateway/plugins/framework/manager.py`
- `mcpgateway/plugins/framework/models.py`
- `plugins/config.yaml`
