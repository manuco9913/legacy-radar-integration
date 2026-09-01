# Legacy Radar Integration

Fictional exercise: bring an existing legacy radar sensor, sitting in a restricted
on-prem/air-gapped network, into a modern backend and operator UI — the way a field engineer
integrates a customer's existing hardware into a new platform.

Pipeline: sensor simulator → UDP (legacy device protocol) → Python adapter
(parse/validate/normalize) → gRPC/protobuf → backend → WebSocket → React operator UI.
Packaged with Docker Compose, designed to run without internet access.

## Status

Early-stage. See [`PRD.md`](PRD.md) for scope/requirements and [`plan.md`](plan.md) for
working notes. Build-out is tracked via GitHub Issues.

## Customer framing

This repo uses a fictional customer ("Customer A") and a generic "Legacy Radar Unit" — no
real product, company, or proprietary interface is referenced or reverse-engineered.
