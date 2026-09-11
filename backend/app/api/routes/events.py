from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any, Dict

from backend.app.api.deps import require_permission
from backend.app.core.database import get_db
from backend.app.handlers.event_handlers import handle_event

router = APIRouter(prefix="/api/events", tags=["events"])


class EventPayload(BaseModel):
    type: str
    timestamp: str | None = None
    data: Dict[str, Any] | None = None


@router.post("/", summary="Receive an event webhook and dispatch to handlers")
def receive_event(payload: EventPayload, db: Session = Depends(get_db), _=Depends(require_permission("write"))):
    try:
        result = handle_event(db, payload.dict())
        return {"status": "ok", **(result or {})}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
