from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.services.ai_copilot import answer_question, provider_status

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status")
async def ai_status(user=Depends(require_permission("read"))) -> dict:
    return provider_status()


class CopilotQuestion(BaseModel):
    prompt: str = Field(min_length=2, max_length=2000)
    assessment_id: str | None = None
    finding_id: str | None = None


@router.post("/ask")
async def ask_copilot(
    body: CopilotQuestion,
    db: Session = Depends(get_db),
    user=Depends(require_permission("read")),
) -> dict:
    return await answer_question(db, body.model_dump())
