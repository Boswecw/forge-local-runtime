# forge-local-runtime (doctrine) — Claude Code Context

Governance doctrine for the **public-app** local services. This repo governs them; it does not
implement them.

> **Not `forge-local-systems-runtime`.** Near-identical names, and both are doctrine repos that
> implement nothing. This one governs the public-app local services;
> `ecosystem/local-systems/forge-local-systems-runtime` governs the business-side local services.
> Applying one side's doctrine to the other side's services is the failure mode.

Canonical reference: `doc/FOLSYSTEM.md`, assembled from `doc/system/` via `bash doc/system/BUILD.sh`.
Standing doctrine also lives in `BOUNDARIES.md`, `ARCHITECTURE.md`, and `DECISIONS/`.

---

## Boundaries

The doctrine is expressed as schemas, not prose — [`schemas/`](schemas/) defines
`runtime-contract`, `service-status`, `readiness-summary`, `handoff-envelope`, `degraded-state`,
`denial-state`, and `forensic-event-envelope`. A local service that reports readiness,
degradation, or denial does it in these shapes.

- **Degraded and denied are declared states, never silent fallbacks.** `degraded-state` and
  `denial-state` exist so a service cannot quietly pretend to be healthy.
- Runtime promotion is receipted: `runtime_promotion/` and `receipts/` carry the evidence, and
  promotion policy is enforced, not assumed.
- Do not add service implementation here to "make it work" — the boundary is the product.

---

## Verification

```bash
make validate     # validate-schemas + check-boundaries
python -m pytest tests -q
```

`scripts/validate_schemas.py` checks the contract corpus; `scripts/check_boundaries.py` checks that
the declared ownership boundaries hold. The suites under `tests/boundaries/`, `tests/contracts/`,
and `tests/observability/` are where a doctrine change proves itself.

```bash
./scripts/context-bundle.sh --list
```
