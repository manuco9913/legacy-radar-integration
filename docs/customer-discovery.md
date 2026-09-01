# Customer Discovery & Success Criteria

> Fictional exercise. "Customer A" and the "Legacy Radar Unit" described below are invented
> for this project and do not reference any real organization, product, or proprietary
> protocol.

## Customer profile

**Customer A** operates a perimeter-monitoring site (e.g. a critical-infrastructure facility
or remote outpost) that has relied on a **Legacy Radar Unit ("LRU-2100")** for several years.
The radar itself is reliable at its core job — detecting and ranging objects — but its data
output was never designed to feed a modern monitoring stack: no structured API, no health
reporting, just a raw broadcast on the local network that a purpose-built legacy console used
to consume.

Customer A wants to keep the radar hardware in place (replacing/recertifying physical sensor
hardware is expensive and operationally disruptive) while modernizing everything downstream:
a proper backend, a live operator dashboard, and the reliability/observability that the old
console never had.

## Environment & network constraints

- **Restricted, on-prem, air-gapped network.** No outbound internet access is available or
  permitted at runtime. Whatever is deployed must run entirely on the local network.
- All services (radar, adapter, backend, operator UI) sit on a single internal subnet for
  this exercise; in a real deployment the adapter would typically run on an edge host close
  to the radar, with the backend reachable elsewhere on the same restricted network.
- Because the network is locked down by a security team, every port and protocol the
  integration uses must be **documented explicitly** so firewall rules can be configured
  without guesswork. Planned ports (confirmed/finalized in the tracer-bullet issue, #3):
  - UDP — radar → adapter (raw legacy broadcast)
  - TCP — adapter → backend (gRPC)
  - TCP — backend → operator UI (WebSocket) and `/health` (HTTP)

## Assumed device characteristics

- **Device:** Legacy Radar Unit, model LRU-2100 (fictional).
- **Transport:** broadcasts fixed-length binary UDP frames on the local network — no
  handshake, no acknowledgment, no request/response; it just emits.
- **Cadence:** one reading per second under normal operation.
- **Frame quirk:** like a lot of hardware from this device's era, the frame isn't internally
  consistent — most fields are encoded big-endian, but one field (range) is encoded
  little-endian, a known idiosyncrasy of this device generation. Getting this wrong is a
  quiet, realistic way to produce plausible-looking-but-wrong data rather than an obvious
  crash, which is exactly the kind of bug worth documenting when the adapter is built.
- **Known failure modes** (informed by the fault-injection scope already agreed in
  `plan.md`):
  - **Malformed frames** — electrical interference or a partial send can corrupt bytes or
    fail the checksum.
  - **Duplicate frames** — the radar's firmware occasionally retransmits the same reading.
  - **Out-of-order frames** — rare, but a buffered retransmit can arrive after a newer
    reading.
  - **Silence** — brief power flicker or an internal self-test cycle stops the broadcast
    for a period before it resumes on its own.

## Success criteria (from the operator's perspective)

1. **Primary — feed health is unambiguous.** The operator can tell at a glance whether the
   display reflects a live, current reading or a stale/disconnected feed. A frozen screen
   that still "looks fine" is the worst-case failure — it's the one operators most want to
   avoid.
2. **Secondary — displayed data is correct.** No duplicate or out-of-order readings are ever
   shown as if they were new; a malformed frame from the radar never crashes the adapter or
   corrupts what's shown.
3. **Operational — deployable and documented for a restricted network.** The full stack runs
   via a single `docker compose up` with no runtime internet access, and the ports/protocols
   involved are documented clearly enough for a network admin to configure firewall rules.

## Explicit assumptions & open questions

- Assumed the radar's own internal detection/ranging logic is out of scope and already
  correct — this project only concerns the data path from "radar broadcasts a reading" to
  "operator sees it."
- Assumed one radar unit for this exercise (no multi-sensor fusion — matches PRD's Out of
  Scope).
- Assumed a 3-second staleness threshold (3x the normal 1-second cadence) is a reasonable,
  defensible default for "feed may be down" — this is a starting point, not a customer-
  confirmed SLA, and may be revisited once the tracer-bullet pipeline (#3) is running.
- Open question: exact checksum/validation scheme for the legacy frame is left to be
  finalized when the protobuf contract and wire format are defined in #3, informed by the
  quirk described above.
- Open question: whether the adapter or the backend is the better place to enforce the
  staleness window is left to the backend/health issue (#6) to decide.
