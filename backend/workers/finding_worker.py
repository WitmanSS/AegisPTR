"""Simple background worker that subscribes to Redis `finding.created` channel,
loads the Finding, enriches it (mock enrichment), updates DB, and publishes
`finding.enriched`.

Run with: `python -m backend.workers.finding_worker` or `python backend/workers/finding_worker.py`
"""
import os
import json
import logging
import time
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.events.publisher import Publisher

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def get_db_session() -> Session:
    from app.core.database import SessionLocal

    return SessionLocal()


def enrich_finding(db: Session, finding_id: str) -> Dict[str, Any]:
    """Perform simple enrichment: set a derived risk_score and add an enrichment note."""
    from app.models.finding import Finding

    f = db.query(Finding).filter(Finding.id == finding_id).first()
    if not f:
        return {"error": "not_found"}

    # mock enrichment logic: bump risk_score based on severity
    severity_map = {"CRITICAL": 90, "HIGH": 70, "MEDIUM": 50, "LOW": 20}
    base = severity_map.get(f.severity.upper(), 30)
    f.risk_score = base + (f.confidence if hasattr(f, "confidence") else 0)
    # append enrichment note to remediation field
    note = f"Enriched at {time.strftime('%Y-%m-%dT%H:%M:%SZ')}: risk_score set to {f.risk_score}"
    f.remediation = (f.remediation or "") + "\n" + note
    db.add(f)
    db.commit()
    db.refresh(f)
    return {"id": f.id, "risk_score": f.risk_score}


def run_worker():
    redis_url = os.environ.get("REDIS_URL")
    if not redis_url:
        logger.error("REDIS_URL not configured — worker requires Redis to subscribe")
        return

    pub = Publisher(redis_url)
    r = pub._ensure_redis()
    if r is None:
        logger.error("Unable to connect to Redis")
        return

    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe("finding.created")
    logger.info("Subscribed to finding.created — waiting for messages...")

    for message in pubsub.listen():
        try:
            if message is None:
                time.sleep(0.1)
                continue
            data = json.loads(message.get("data") or "{}")
            logger.info("Received message: %s", data)
            finding_ref = data.get("data")
            # our publisher sent either internal id or object; if object, try to extract id
            finding_id = None
            if isinstance(finding_ref, dict):
                finding_id = finding_ref.get("id")
            elif isinstance(finding_ref, str):
                finding_id = finding_ref

            if not finding_id:
                logger.warning("No finding id found in message: %s", data)
                continue

            db = get_db_session()
            result = enrich_finding(db, finding_id)
            logger.info("Enrichment result: %s", result)
            pub.publish("finding.enriched", {"type": "finding.enriched", "data": result})
        except Exception as e:
            logger.exception("Worker error: %s", e)


if __name__ == "__main__":
    run_worker()
