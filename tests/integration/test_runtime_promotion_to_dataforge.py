from __future__ import annotations

import os
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import psycopg
import pytest
import requests


# ============================================================
# Runtime proof scaffold
# ------------------------------------------------------------
# This test is intentionally integration-only.
# It verifies the already-proven seam:
#
# local queued artifact
#   -> worker claims artifact
#   -> worker POSTs to DataForge
#   -> local row becomes delivered
#   -> DataForge receipt row exists
#
# Assumptions:
# - Forge Local Runtime DB is reachable via RUNTIME_PROMOTION_DATABASE_URL
#   or DATABASE_URL
# - DataForge is running on http://127.0.0.1:8001 by default
# - The worker can still be launched with:
#     PYTHONPATH=. python scripts/run_runtime_promotion_worker.py
#
# You may need to align column names or table names if your repo differs.
# This is the first repo-native proof harness, not the final hardened version.
# ============================================================


@pytest.mark.integration
@pytest.mark.runtime_promotion
class TestRuntimePromotionToDataForge:
    def test_runtime_promotion_delivery_end_to_end(self) -> None:
        cfg = IntegrationConfig.from_env()

        ensure_dataforge_health(cfg.dataforge_base_url)

        artifact = seed_test_artifact(cfg)

        worker_result = run_runtime_promotion_worker(cfg)
        assert worker_result.returncode == 0, (
            "Runtime promotion worker failed.\n\n"
            f"STDOUT:\n{worker_result.stdout}\n\n"
            f"STDERR:\n{worker_result.stderr}"
        )

        local_row = fetch_local_artifact_row(cfg, artifact.artifact_id)
        assert local_row is not None, f"Artifact not found locally: {artifact.artifact_id}"

        assert local_row["status"] == "delivered", (
            "Expected local artifact to be delivered after worker run, "
            f"but got status={local_row['status']!r}"
        )
        assert local_row["delivery_attempt_count"] >= 1
        assert local_row["acknowledged_at"] is not None

        receipt_row = fetch_dataforge_receipt_by_dedupe_key(
            cfg=cfg,
            dedupe_key=artifact.dedupe_key,
        )
        assert receipt_row is not None, (
            "Expected matching DataForge receipt row to exist for "
            f"dedupe_key={artifact.dedupe_key!r}"
        )

        assert receipt_row["dedupe_key"] == artifact.dedupe_key
        assert receipt_row["envelope_type"] == "local_failure_pattern"
        assert receipt_row["ingest_status"] == "accepted"
        assert receipt_row["source"] == "forge_local_runtime"


@dataclass(frozen=True)
class IntegrationConfig:
    runtime_db_url: str
    dataforge_base_url: str
    dataforge_db_url: str | None
    repo_root: str

    @classmethod
    def from_env(cls) -> "IntegrationConfig":
        runtime_db_url = (
            os.getenv("RUNTIME_PROMOTION_DATABASE_URL")
            or os.getenv("DATABASE_URL")
            or ""
        ).strip()

        if not runtime_db_url:
            raise RuntimeError(
                "Missing runtime DB URL. Set RUNTIME_PROMOTION_DATABASE_URL "
                "or DATABASE_URL before running this integration test."
            )

        dataforge_base_url = os.getenv("DATAFORGE_BASE_URL", "http://127.0.0.1:8001").strip()
        dataforge_db_url = os.getenv("DATAFORGE_DATABASE_URL")
        repo_root = os.getcwd()

        return cls(
            runtime_db_url=runtime_db_url,
            dataforge_base_url=dataforge_base_url,
            dataforge_db_url=dataforge_db_url.strip() if dataforge_db_url else None,
            repo_root=repo_root,
        )


@dataclass(frozen=True)
class SeededArtifact:
    artifact_id: str
    dedupe_key: str
    created_at: datetime


def ensure_dataforge_health(dataforge_base_url: str) -> None:
    health_url = f"{dataforge_base_url.rstrip('/')}/health"
    response = requests.get(health_url, timeout=10)
    assert response.status_code == 200, (
        f"DataForge health check failed at {health_url}. "
        f"status={response.status_code} body={response.text}"
    )


def run_runtime_promotion_worker(cfg: IntegrationConfig) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "."

    return subprocess.run(
        ["python", "scripts/run_runtime_promotion_worker.py"],
        cwd=cfg.repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def seed_test_artifact(cfg: IntegrationConfig) -> SeededArtifact:
    """
    Inserts one queueable artifact directly into the local runtime table.

    This is preferred for the first proof harness because it avoids coupling
    the test to a separate CLI proof utility before the test itself exists.

    Align the insert column list if your actual table shape differs.
    """
    artifact_id = f"artifact-{uuid.uuid4()}"
    dedupe_key = f"it-dedupe-{uuid.uuid4()}"
    created_at = datetime.now()

    envelope_payload: dict[str, Any] = {
        "pattern_id": f"pattern-{uuid.uuid4()}",
        "service": "df_local_foundation",
        "failure_pattern_type": "integration_test_delivery_proof",
        "frequency_window": "15m",
        "occurrence_count": 3,
        "severity": "moderate",
        "affected_contract_or_capability": "runtime_promotion_transport",
        "supporting_examples": [
            {
                "summary": "Integration proof artifact created by pytest scaffold",
                "source": "pytest",
            }
        ],
        "observed_at": created_at.isoformat(),
    }

    with psycopg.connect(cfg.runtime_db_url) as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                """
                INSERT INTO runtime_promotion.outbound_artifacts (
                    artifact_id,
                    envelope_type,
                    payload,
                    dedupe_key,
                    status,
                    delivery_attempt_count,
                    created_at
                )
                VALUES (
                    %(artifact_id)s,
                    %(envelope_type)s,
                    %(payload)s::jsonb,
                    %(dedupe_key)s,
                    %(status)s,
                    %(delivery_attempt_count)s,
                    %(created_at)s
                )
                """,
                {
                    "artifact_id": artifact_id,
                    "envelope_type": "local_failure_pattern",
                    "payload": json_dumps(envelope_payload),
                    "dedupe_key": dedupe_key,
                    "status": "queued",
                    "delivery_attempt_count": 0,
                    "created_at": created_at,
                },
            )
        conn.commit()

    return SeededArtifact(
        artifact_id=artifact_id,
        dedupe_key=dedupe_key,
        created_at=created_at,
    )


def fetch_local_artifact_row(
    cfg: IntegrationConfig,
    artifact_id: str,
) -> dict[str, Any] | None:
    with psycopg.connect(cfg.runtime_db_url) as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                """
                SELECT
                    artifact_id,
                    status,
                    delivery_attempt_count,
                    acknowledged_at,
                    rejection_reason_class
                FROM runtime_promotion.outbound_artifacts
                WHERE artifact_id = %(artifact_id)s
                """,
                {"artifact_id": artifact_id},
            )
            row = cur.fetchone()
            return dict(row) if row else None


def fetch_dataforge_receipt_by_dedupe_key(
    cfg: IntegrationConfig,
    dedupe_key: str,
) -> dict[str, Any] | None:
    """
    Preferred path:
    - direct DB verification against DataForge Postgres if DATAFORGE_DATABASE_URL is set

    Fallback:
    - fail loudly, because direct DB verification is part of the proof posture
    """
    if not cfg.dataforge_db_url:
        raise RuntimeError(
            "Missing DATAFORGE_DATABASE_URL. "
            "Set it so this test can verify the receipt directly in DataForge Postgres."
        )

    with psycopg.connect(cfg.dataforge_db_url) as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                """
                SELECT
                    receipt_id,
                    dedupe_key,
                    envelope_type,
                    service,
                    ingest_status,
                    source
                FROM runtime_promotion_receipts
                WHERE dedupe_key = %(dedupe_key)s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                {"dedupe_key": dedupe_key},
            )
            row = cur.fetchone()
            return dict(row) if row else None


def json_dumps(value: dict[str, Any]) -> str:
    import json

    return json.dumps(value, separators=(",", ":"), sort_keys=True)