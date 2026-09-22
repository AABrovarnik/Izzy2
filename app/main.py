from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .db import database_is_ready, get_db, init_db
from .models import Proposal, Source, Task
from .schemas import (
    ApprovalBody,
    ProposalCreate,
    ProposalRead,
    SourceRead,
    TaskCreate,
    TaskRead,
    TelegramUpdate,
)
from .services import (
    ServiceError,
    approve_proposal,
    create_proposal,
    create_task,
    execute_proposal,
    ingest_telegram_update,
    reject_proposal,
    snooze_proposal,
)

settings = get_settings()
bearer = HTTPBearer(auto_error=False)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="AI Secretary API", version="2.0.0", lifespan=lifespan)


def require_api_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    if not settings.api_token:
        if settings.app_env == "development":
            return "development"
        raise HTTPException(status_code=503, detail="API_TOKEN не настроен")
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Bearer token required")
    if not __import__("hmac").compare_digest(credentials.credentials, settings.api_token):
        raise HTTPException(status_code=401, detail="Invalid bearer token")
    return "api"


def service_call(call):
    try:
        return call()
    except ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.get("/health/live")
def live():
    return {"status": "ok"}


@app.get("/health/ready")
def ready():
    if not database_is_ready():
        raise HTTPException(status_code=503, detail="database is not ready")
    return {"status": "ready", "database": "ok"}


@app.get("/api/v1/sources", response_model=list[SourceRead])
def list_sources(
    _: str = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    return db.scalars(select(Source).order_by(Source.created_at.desc()).limit(100)).all()


@app.get("/api/v1/tasks", response_model=list[TaskRead])
def list_tasks(
    _: str = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    return db.scalars(select(Task).order_by(Task.created_at.desc()).limit(100)).all()


@app.post("/api/v1/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def add_task(
    data: TaskCreate,
    _: str = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    return create_task(db, data)


@app.get("/api/v1/proposals", response_model=list[ProposalRead])
def list_proposals(
    _: str = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    return db.scalars(select(Proposal).order_by(Proposal.created_at.desc()).limit(100)).all()


@app.post("/api/v1/proposals", response_model=ProposalRead, status_code=status.HTTP_201_CREATED)
def add_proposal(
    data: ProposalCreate,
    response: Response,
    _: str = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    proposal, approval_token = service_call(lambda: create_proposal(db, data))
    # Token is returned only at creation time. It is never persisted in plaintext.
    response.headers["X-Approval-Token"] = approval_token
    return proposal


@app.post("/api/v1/proposals/{proposal_id}/approve", response_model=ProposalRead)
def approve(
    proposal_id: str,
    body: ApprovalBody,
    _: str = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    return service_call(lambda: approve_proposal(db, proposal_id, body.version, body.approval_token))


@app.post("/api/v1/proposals/{proposal_id}/reject", response_model=ProposalRead)
def reject(
    proposal_id: str,
    body: ApprovalBody,
    _: str = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    return service_call(
        lambda: reject_proposal(db, proposal_id, body.version, body.approval_token)
    )


@app.post("/api/v1/proposals/{proposal_id}/snooze", response_model=ProposalRead)
def snooze(
    proposal_id: str,
    body: ApprovalBody,
    _: str = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    return service_call(
        lambda: snooze_proposal(db, proposal_id, body.version, body.approval_token)
    )


@app.post("/api/v1/proposals/{proposal_id}/execute", response_model=ProposalRead)
def execute(
    proposal_id: str,
    _: str = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    return service_call(lambda: execute_proposal(db, proposal_id))


@app.post("/api/v1/webhooks/telegram")
def telegram_webhook(
    update: TelegramUpdate,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if not settings.telegram_webhook_secret or not x_telegram_bot_api_secret_token:
        raise HTTPException(status_code=401, detail="Telegram webhook secret is not configured")
    if not __import__("hmac").compare_digest(
        x_telegram_bot_api_secret_token, settings.telegram_webhook_secret
    ):
        raise HTTPException(status_code=401, detail="Invalid Telegram webhook secret")
    sender_id = str(((update.message or {}).get("from") or {}).get("id") or "")
    if settings.telegram_owner_user_id and sender_id != settings.telegram_owner_user_id:
        raise HTTPException(status_code=403, detail="Telegram user is not allowed")
    source = ingest_telegram_update(db, update.update_id, update.model_dump())
    return {"ok": True, "source_id": source.id}
