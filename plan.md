# Kela FDE Interview Prep — Sensor Integration Project

## Context

First-round interview done (went well) for a Forward Deployed Engineer role at Kela
Technologies (Israeli defense-tech, Sequoia-backed, building an open C2/"HUB" platform that
integrates sensors — radar/drone/camera — for border defense). Main concern raised in round
1: stack mismatch. Production background is C#/.NET, Node/NestJS, React/Angular, PostgreSQL,
Docker, distributed/operational systems, on-prem/air-gapped environments, field integrations.
Kela's postings skew Python-flavored device/field integration work, Rust/C++/Go for their HUB
core, gRPC/protobuf, Kubernetes, Linux/networking depth.

Research confirms the FDE role itself (not the HUB Core platform role) is explicitly the
customer-facing integration/bridge job: own technical relationship with customers, translate
customer architecture/constraints into integration plans, be the "get it working"
troubleshooter, build small out-of-band adapters/scripts/prototypes, and turn field work into
reusable reference architectures and patterns. This directly validates the project concept
(legacy sensor → adapter → gRPC HUB-like backend → operator UI) as a generic, non-proprietary
mirror of real FDE work.

The overall goal (multi-session): build a public GitHub repo demonstrating customer
discovery, networking/protocol integration, data validation/normalization, fault handling,
Docker/K8s packaging, troubleshooting discipline, and reusable-pattern thinking — with
authentic incremental git history (issues, feature branches, PRs), not a single
finished-then-uploaded commit.

Today's session is time-boxed to **~1 hour**: a quick spike to get a tactile feel for Python
+ protobuf + gRPC before committing further design effort to the real documented project.
The full project remains targeted at 8–15 focused hours across future sessions.

## Decisions locked (grill-me session, apply to the real project going forward)

1. **Backend + adapter + simulator language: Python end-to-end** (not NestJS). Deliberately
   chosen over leveraging existing NestJS strength — round 1's feedback was about stack
   mismatch, so the project should maximize genuine exposure to closing that specific gap,
   not showcase already-proven strength. React UI stays as originally scoped (minimal,
   display-only — not a target skill either way).
2. **No Kubernetes for now.** Docker Compose only. Add a short "productionization path: K8s
   manifests" note in docs rather than building manifests, to protect time budget.
3. **Preflight/diagnostic CLI is a stretch goal** — its own issue, last in the backlog, first
   thing cut if time runs short.
4. **Repo framing: fully generic**, no resemblance to Kela. Fictional "Customer A," unnamed/
   generic "Legacy Radar Unit" (made-up model number). Candidate repo names:
   `legacy-radar-integration`, `sensor-hub-bridge`, `radar-adapter-lab`.
5. **Fallback cut order if the real build runs long:** shrink fault-injection scenarios to
   2-3 well-documented cases first (malformed packet, stale/duplicate data, adapter
   disconnect) rather than a broad matrix. Frontend and Docker packaging are protected since
   a working demo matters more than an exhaustive fault matrix.
6. **Narrative to defend in the interview:** the language (Python) is the honest new-skill
   signal — no pretending years of experience. The engineering *process* (customer discovery
   before code, ADRs recording why, structured fault injection, troubleshooting runbooks,
   reusable-pattern extraction) is where production experience actually shows through,
   independent of syntax.

## Today: 1-hour gRPC/protobuf spike, on its own branch

**Goal:** first tactile contact with protobuf + gRPC in Python.

**Branching:** this spike lives in this repo but isolated on a `prototype` branch, so `main`
stays clean and the "real," authentically-documented history (customer discovery → issues →
PRs) can start fresh from `main` afterward without this spike's first-contact commits mixed
in. `prototype` stays in the repo as a visible, honestly-labeled exploration branch.

**Git setup:**
1. `git init` in this folder.
2. Minimal root commit on `main` (README stub + `.gitignore`).
3. Create and check out branch `prototype` from `main`.
4. Do the spike's work and commits on `prototype`.
5. When the real project starts, work resumes from `main`; `prototype` stays as reference.
6. GitHub: local repo only for today. Public GitHub repo creation is deferred to when the
   real documented project begins.

**Environment:** Python 3.14.4 + pip confirmed present. `grpcio` / `grpcio-tools` not yet
installed — install via pip into a local venv (`pip install grpcio grpcio-tools protobuf`).
Requires internet, which is fine — only the final product's *runtime* needs to be air-gapped.

**Steps:**
1. Brief teach: `.proto` files (message vs. service vs. rpc), how `grpc_tools.protoc`
   generates Python stubs, how this differs from REST/JSON.
2. Draft a minimal `sensor.proto`: one `SensorReading` message + one `SensorService` with a
   single unary RPC (e.g. `GetLatestReading`).
3. Generate Python stubs via `python -m grpc_tools.protoc`.
4. Write a minimal `server.py` implementing the service (canned/randomized reading).
5. Write a minimal `client.py` calling the RPC and printing the response.
6. Run server + client locally end-to-end; discuss what happened structurally vs. the
   REST/NestJS mental model.
7. Capture 3–5 bullet "first impressions" notes — seeds for the eventual
   `field-learnings.md` in the real project.

**Out of scope today:** UDP sensor simulator, adapter parsing/validation, WebSocket gateway,
React UI, Docker, GitHub repo/issues — deferred to future sessions.

## After this session

Next session starts the real project: create the public GitHub repo, open the initial
~7–10 issues, define feature-branch/PR flow (~3–5 PRs), and begin with the **Customer
Discovery & Success Criteria** document.

## Verification

Spike is complete when `client.py` receives a `SensorReading` from `server.py` over a live
local gRPC call and prints it to console.
