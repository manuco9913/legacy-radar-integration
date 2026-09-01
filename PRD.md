# PRD: Legacy Sensor Integration Reference Project

> Status: draft. To be submitted as the first GitHub Issue once the public repo is created
> (see `plan.md` — repo creation is deferred until the `prototype` spike is done).

## Problem Statement

I have a solid production track record (C#/.NET, Node/NestJS, React/Angular, PostgreSQL,
Docker, distributed/operational systems, on-prem/air-gapped environments, field
integrations), and passed a first-round Forward Deployed Engineer interview at a
defense-tech company whose stack skews toward Python-flavored device/field integration,
gRPC/protobuf, and Linux/networking depth. The interviewers' one concrete concern was stack
mismatch: they can't yet see evidence that my engineering judgment transfers to *their*
tools, only that it works well in mine.

I need a public, reviewable artifact that lets a technical interviewer verify — without
taking my word for it — that I can pick up their stack quickly and still apply the same
discipline (discovery before code, structured fault handling, root-cause debugging,
reusable patterns) that a senior field engineer is expected to bring.

## Solution

Build and publish, as a public GitHub repo with an authentic incremental history, a small
end-to-end integration exercise that mirrors what a Forward Deployed Engineer actually does:
take an existing (fictional) legacy sensor a customer already has, integrate it into a
modern backend/UI, and document the process the way a field engineer would — customer
discovery, architecture decisions, what broke, how it was debugged, and what would be
productized for reuse.

Pipeline: a Python **sensor simulator** emits a legacy device's UDP protocol (including
deliberately realistic quirks) → a Python **adapter** parses, validates, and normalizes
readings → forwards them via **gRPC/protobuf** → a Python **backend** that also exposes a
**WebSocket** feed → a minimal **React** operator UI displays live sensor state. Packaged
with Docker Compose, designed to run fully offline. No Kubernetes in this pass.

The repo itself is the deliverable as much as the running system: ~7-10 GitHub issues,
feature branches, ~3-5 PRs, and short docs (customer discovery, architecture decisions,
troubleshooting runbook, field learnings) that let a reader reconstruct how the problem was
understood and solved — not just look at a finished pile of code.

## User Stories

1. As an interviewer reviewing the repo, I want a customer-discovery doc written before any
   code exists, so that I can see requirements-gathering discipline, not just coding output.
2. As an interviewer, I want the git history to show issues → branches → PRs in a plausible
   order, so that I can tell this was built iteratively rather than uploaded as one final
   commit.
3. As an interviewer, I want to see explicit architecture decisions (and reversals), so that
   I can evaluate technical judgment, not just the final shape of the code.
4. As an interviewer, I want to see at least one real bug that occurred during development
   and how it was root-caused, so that I can assess debugging methodology under a stack
   that's new to the author.
5. As an interviewer, I want a short "field learnings" doc translating what was learned into
   reusable patterns, so that I can see the candidate thinks beyond the single fictional
   customer.
6. As a fictional customer operator, I want a live view of the sensor's current readings and
   connection health, so that I can tell at a glance whether the feed is healthy or stale.
7. As a fictional customer's network admin, I want the system's ports/protocols documented,
   so that I can configure firewall rules in a restricted on-prem network.
8. As the adapter, I want to detect and reject malformed packets without crashing, so that
   one bad frame from the device doesn't take down the integration.
9. As the adapter, I want to detect duplicate readings (retransmitted or replayed), so that
   the operator UI doesn't show phantom updates.
10. As the adapter, I want to detect out-of-order readings (arrived later but timestamped
    earlier than the current latest), so that stale data never overwrites fresher data.
11. As the adapter, I want to detect stale readings (no new data within an expected window),
    so that the operator UI can flag "sensor may be down" instead of silently freezing.
12. As the adapter, I want to reconnect to the backend's gRPC endpoint with backoff if the
    connection drops, so that a transient network blip doesn't require manual restart.
13. As the backend, I want structured (JSON) logs for every significant event (connect,
    disconnect, malformed data, reconnect, forwarded reading), so that a field engineer can
    grep/correlate what happened during an incident.
14. As the backend, I want a `/health` endpoint reporting adapter-connection status and
    last-reading age, so that it can be checked manually or by an orchestrator.
15. As the operator UI, I want to show connection/staleness state distinctly from normal
    operation, so that an operator isn't misled by a frozen "looks fine" screen.
16. As a developer, I want the whole stack runnable via one `docker compose up` with no
    internet access required at runtime, so that it reflects the air-gapped/on-prem
    constraint the fictional customer has.
17. As a developer, I want the protobuf schema to be the single source of truth for the
    normalized data contract, so that the adapter and backend can't silently drift apart.
18. As a future maintainer, I want the adapter's parsing/validation/normalization logic
    isolated from its networking code, so that it can be unit-tested without a live socket
    or gRPC connection.
19. As an interviewer, I want at least 2-3 concrete, documented fault scenarios (e.g. kill
    the adapter mid-stream, feed it a corrupted packet, delay the backend) with the observed
    symptom and root cause written down, so that I can evaluate troubleshooting rigor
    directly instead of taking a claim at face value.
20. As a future FDE-me, I want a short troubleshooting runbook capturing the fault scenarios
    and how to diagnose them, so that this pattern is reusable on the next (real) customer
    integration.
21. As a developer with limited time, I want an explicit, pre-agreed fallback (shrink fault
    scenarios first) if the build runs long, so that scope-cutting under time pressure is a
    pre-made decision, not a panicked one.
22. As an interviewer, I want the README to be honest about what's new-to-the-author (Python,
    gRPC/protobuf) versus pre-existing strength (architecture/process discipline), so that
    the project doesn't misrepresent experience level.

## Implementation Decisions

**Modules:**
- `sensor-sim/` — Python script emitting a fictional legacy radar's UDP wire format at a
  fixed interval. Config/flags allow injecting the fault conditions the adapter must handle
  (malformed frame, duplicate send, out-of-order timestamp, silence/stale). Shallow module —
  no unit-test suite, verified by manual/integration run.
- `adapter/` — the one **deep module** in this project. Public interface is small and pure:
  `parse(raw_bytes) -> Reading | ParseError`, `validate(reading, last_known_state) ->
  ValidationResult` (ok / duplicate / out-of-order / stale / malformed), `normalize(reading)
  -> SensorReadingProto`. All I/O (UDP socket, gRPC client with retry/timeout/reconnect)
  wraps this pure core rather than being mixed into it — this is what makes the core
  testable in isolation.
- `proto/` — protobuf schema (`SensorReading` message, `SensorService` with the streaming
  RPC the adapter uses to forward normalized readings). Single source of truth for the
  adapter↔backend contract; both sides generate stubs from it, so they cannot silently drift.
- `backend/` — Python gRPC server ingesting the adapter's stream, a WebSocket gateway
  broadcasting current state to the UI, a `/health` endpoint, and structured JSON logging.
  Plumbing/shallow — no dedicated unit-test suite (see Testing Decisions).
- `frontend/` — minimal React UI: current reading(s), connection/staleness indicator. Not a
  target skill for this project; kept intentionally small.
- `deploy/` — Docker Compose wiring all services on a shared network with explicit exposed
  ports (documented for the fictional customer's firewall rules). No Kubernetes in this pass;
  a one-line "productionization path" note in docs instead.
- Stretch, own issue, cut first if short on time: a small **preflight CLI** (checks UDP port
  reachability, gRPC endpoint reachability, protobuf schema-version match between adapter and
  backend) — demonstrates turning one-off manual checks into reusable tooling.

**Repo/process decisions:**
- Git: `main` starts clean (README stub + `.gitignore`); today's throwaway gRPC/protobuf
  spike lives on a separate `prototype` branch and is never merged into the documented
  history. The real project's issues/branches/PRs all build on `main`.
- ~7-10 GitHub issues, one per module/milestone roughly matching the breakdown above
  (customer discovery; protobuf contract; simulator; adapter parsing; adapter
  validation/fault-handling; gRPC bridge; backend + WebSocket + health/logging; frontend;
  Docker Compose packaging; fault-injection scenarios + runbook; field learnings; stretch:
  preflight CLI).
- ~3-5 PRs grouping related issues (e.g. simulator+adapter together, backend+bridge
  together, frontend+Docker together, fault scenarios+docs together), each with a
  description explaining what was built and why.
- Repo name: generic, no resemblance to the target company — candidates
  `legacy-radar-integration`, `sensor-hub-bridge`, `radar-adapter-lab`.
- Fictional framing throughout: customer referred to as "Customer A," device as "Legacy
  Radar Unit" with a made-up model number.

## Testing Decisions

- A good test here exercises **external behavior** of the adapter's pure core (given these
  raw bytes / this sequence of readings, expect this parsed result / validation outcome /
  normalized message) — not internal call counts or mocked socket plumbing.
- **Unit-tested module:** `adapter`'s parse → validate → normalize pipeline only. Test
  cases per requirement: valid packet parses correctly; malformed/corrupt packet returns a
  `ParseError` without raising; duplicate reading (same id/timestamp seen before) is flagged;
  out-of-order reading (older timestamp arriving after a newer one) is flagged; stale
  reading (timestamp older than the allowed window at validation time) is flagged;
  valid reading normalizes to the expected protobuf message shape.
- **Not unit-tested (manual/integration verification instead, documented as a runbook
  procedure):** sensor simulator, backend gRPC/WebSocket/health plumbing, frontend, preflight
  CLI. This is a deliberate scope decision to protect the time budget — see Out of Scope.
- No prior art in this repo to follow (greenfield); test framework choice (`pytest`, plain
  `assert`-based or otherwise) to be made when the adapter issue is picked up.

## Out of Scope

- Kubernetes manifests/deployment (documented as a future productionization step only).
- The preflight/diagnostic CLI, unless time remains after the core pipeline and docs are
  done (stretch goal, explicit last-cut item).
- Any real hardware, real device protocol, or anything resembling a real customer's actual
  system — this is a fully fictional, generic exercise.
- Authentication/authorization, TLS, and other production security hardening for the
  demo services (may be *mentioned* in docs as "what I'd add for production," not built).
- Multi-sensor fusion, historical data storage/persistence, or any analytics beyond the
  live current-state view.
- Broad fault-injection matrix — capped at 2-3 well-documented scenarios; more are cut
  first if the time budget is tight (see Further Notes).
- Cloud deployment, CI/CD pipelines beyond what's trivially useful, and any dependency on
  external services at runtime (the whole point is it runs air-gapped).

## Further Notes

- Time budget: 8-15 focused hours total for the documented project (separate from today's
  ~1hr throwaway spike). Rough per-piece estimates and the agreed fallback order (shrink
  fault-injection scenarios first, frontend/Docker protected) are in `plan.md`.
- Interview narrative to defend: the *language* (Python) is the honest new-skill signal — no
  claim of years of Python/K8s experience. The engineering *process* (discovery before code,
  documented architecture decisions, structured fault injection, troubleshooting runbooks,
  reusable-pattern extraction) is where the pre-existing production experience actually shows
  through, independent of syntax.
- Next concrete step after this PRD: finish today's `prototype` branch spike, then create the
  public GitHub repo from `main`, open the issues enumerated above, and start with the
  Customer Discovery & Success Criteria document as issue #1.
