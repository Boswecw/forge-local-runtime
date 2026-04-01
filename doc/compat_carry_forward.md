# Forge Local Runtime Promotion — Carry-Forward Context (Compact)

## Current state

The first runtime-promotion proving slice is now materially working end to end.

A real local Postgres-backed path has now been proven for:

- candidate signal creation
- promotion envelope normalization
- policy gate review
- queue-plan creation
- DB write planning
- persistence into local Postgres
- safe queue claim behavior
- worker delivery success transition
- worker retry scheduling transition
- durable DB verification for both worker branches

---

## What is now proven

### 1. Local persistence path

Already proven:

- artifact queue writes persist into `runtime_promotion.outbound_artifacts`
- policy events persist into `runtime_promotion.policy_events`
- direct DB verification confirmed queued records were real, not inferred

### 2. Worker typing blocker resolved

Resolved:

- `runtime_promotion/worker.py` was updated so `WorkerCursor` is `@runtime_checkable`
- worker mypy now passes for:
  - `runtime_promotion/connection.py`
  - `runtime_promotion/worker.py`
  - `scripts/run_runtime_promotion_worker.py`

### 3. Worker success-path proof completed

Proven flow:

- queued artifact claimed safely
- row moved into `delivery_in_progress`
- `delivery_attempt_count` incremented
- worker marked artifact `delivered`
- Postgres verification confirmed:
  - `status = delivered`
  - non-null `last_attempted_at`
  - non-null `acknowledged_at`

### 4. Worker retry-path proof completed

Proven flow:

- queued artifact with `simulate_delivery_failure = true` claimed safely
- row moved into `delivery_in_progress`
- `delivery_attempt_count` incremented
- worker scheduled retry through `release_claim_for_retry(...)`
- Postgres verification confirmed:
  - `status = retry_scheduled`
  - non-null `last_attempted_at`
  - non-null `next_attempt_at`
  - null `acknowledged_at`
  - `rejection_reason_class = simulated_delivery_failure`

### 5. Automated worker tests added

Worker-focused pytest coverage now exists for:

- claim row → `ClaimedArtifact` mapping
- default delivered path
- simulated retry path

---

## Current immediate next step

The next correct step is:

## Harden the worker slice with broader proof and then move to the next operational layer

Recommended order:

1. run the full runtime-promotion pytest group together
2. preserve this milestone in carry-forward context
3. choose the next bounded slice:
   - retry/backoff policy refinement
   - queue observability
   - dead-letter / terminal-failure posture

---

## Important posture to preserve

Keep these boundaries intact:

- normalization does not do policy
- policy does not do DB persistence
- persistence does not decide policy
- worker does not redefine queue meaning
- active dedupe remains limited to pre-delivery active states
- local proving slice stays DF Local-oriented and bounded

---

## Compact summary

You now have:

- doctrine
- reviewed schemas
- local Postgres queue schema
- Python promotion package boundaries
- policy and persistence tests
- worker tests
- real persistence proof
- real success-path worker proof
- real retry-path worker proof
- direct DB confirmation for both worker branches

The queue-consumer / delivery-worker proof is now complete for the first slice.