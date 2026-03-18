# SYSTEM.md — Forge Local Runtime

## Constitutional role

Forge Local Runtime is the constitutional and integration authority for the local service layer of the Forge ecosystem.

It governs:

- DF Local Foundation
- NeuronForge Local
- Cortex
- FA Local

These are service-only internal runtime systems.
They are not application-layer products.

## Invariants

1. Service-only classification is mandatory.
2. The local baseline must remain useful without cloud.
3. No service may silently become product authority.
4. Operational visibility is required, but surveillance-by-default is forbidden.
5. Syntax and semantics must remain separated where service roles require it.
6. Policy and admission must precede side effects.
7. Candidate outputs must not silently become canonical truth.
8. Degraded, denied, stale, partial-success, and unavailable states must be truthful and reusable across the runtime layer.
9. Boundaries must be explicit before integration expands.
10. This repo must not become an implementation sink.

## Runtime doctrine

The local runtime layer is governed by:

- local-first
- bounded by hardware reality
- useful offline
- fail-closed
- explicit degraded states
- no stealth authority surfaces
- no fake cloud symmetry
- service-first, UI-second, product-never
- cloud augmentation remains additive only
- operational visibility without privacy collapse
- explicit ownership before integration
- interfaces before implementation volume

## Runtime-wide control obligations

The runtime layer must define shared doctrine or schema posture for:

- service status
- degraded-state classes
- denial classes
- handoff envelopes
- readiness summaries
- requester identity/trust posture
- forensic event minimization
- privacy-preserving embedded diagnostics

## Hard boundary rules

### DF Local Foundation
Owns substrate mechanics.
Does not own app business truth, workflow logic, or semantic authority.

### NeuronForge Local
Owns local inference and candidate production.
Does not own final business authority or hidden autonomous decision loops.

### Cortex
Owns intake, syntax-level extraction, retrieval-preparation support, and packaging handoff support.
Does not own semantic interpretation, inference authority, workflow control, or raw-content surveillance surfaces.

### FA Local
Owns governed execution under trust, policy, and capability admission.
Does not own app semantics, durable semantic memory, inference authority, or open-ended planning.

## Failure posture

When ownership is unclear, execution must narrow or stop.
When trust is insufficient, deny.
When freshness cannot be asserted, mark stale.
When structure is required and invalid, fail closed.
When side effects are in play, policy and admission control the route.

## Repository posture

This repository should primarily contain:

- doctrine
- boundary definitions
- decision records
- shared schemas
- validation posture
- anti-drift tests

Shared implementation should appear only if later justified by real cross-service reuse.