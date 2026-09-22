from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import get_settings
from .models import AuditEvent, Proposal, Source, Task
from .schemas import ProposalCreate, TaskCreate
from .security import hash_value, make_approval_token, new_approval_nonce, parse_and_verify_approval_token


class ServiceError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


def as_utc(value: datetime) -> datetime:
    """SQLite may return timezone-aware columns without tzinfo."""
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def audit(db: Session, actor: str, action: str, entity_type: str, entity_id: str, result: dict) -> None:
    db.add(
        AuditEvent(
            actor=actor,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            result=result,
        )
    )


def create_task(db: Session, data: TaskCreate) -> Task:
    task = Task(**data.model_dump())
    db.add(task)
    db.flush()
    audit(db, "api", "task.created", "task", task.id, {"title": task.title})
    db.commit()
    db.refresh(task)
    return task


def create_proposal(db: Session, data: ProposalCreate) -> tuple[Proposal, str]:
    existing = db.scalar(select(Proposal).where(Proposal.idempotency_key == data.idempotency_key))
    if existing:
        raise ServiceError(409, "Idempotency-Key уже использован")

    settings = get_settings()
    nonce = new_approval_nonce()
    proposal = Proposal(
        **data.model_dump(exclude={"idempotency_key"}),
        idempotency_key=data.idempotency_key,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.approval_ttl_hours),
        approval_nonce_hash=hash_value(nonce),
    )
    db.add(proposal)
    db.flush()
    audit(db, "api", "proposal.created", "proposal", proposal.id, {"action_type": proposal.action_type})
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ServiceError(409, "Idempotency-Key уже использован") from exc
    db.refresh(proposal)
    return proposal, make_approval_token(proposal.id, proposal.version, nonce)


def approve_proposal(db: Session, proposal_id: str, body_version: int, approval_token: str) -> Proposal:
    proposal = db.get(Proposal, proposal_id)
    if not proposal:
        raise ServiceError(404, "Proposal не найден")
    now = datetime.now(timezone.utc)
    if proposal.status != "pending":
        raise ServiceError(409, "Proposal уже обработан")
    if as_utc(proposal.expires_at) <= now:
        proposal.status = "expired"
        db.commit()
        raise ServiceError(410, "Approval истёк")
    if body_version != proposal.version or not parse_and_verify_approval_token(
        approval_token, proposal.id, proposal.version, proposal.approval_nonce_hash
    ):
        raise ServiceError(409, "Устаревшая версия или недействительный approval token")

    proposal.status = "approved"
    proposal.approved_at = now
    proposal.version += 1
    audit(db, "owner", "proposal.approved", "proposal", proposal.id, {"version": proposal.version})
    db.commit()
    db.refresh(proposal)
    return proposal


def reject_proposal(db: Session, proposal_id: str, version: int, approval_token: str) -> Proposal:
    proposal = db.get(Proposal, proposal_id)
    if not proposal:
        raise ServiceError(404, "Proposal не найден")
    if proposal.status != "pending" or version != proposal.version:
        raise ServiceError(409, "Proposal уже обработан или версия устарела")
    if not parse_and_verify_approval_token(
        approval_token, proposal.id, proposal.version, proposal.approval_nonce_hash
    ):
        raise ServiceError(409, "Недействительный approval token")
    proposal.status = "rejected"
    proposal.version += 1
    audit(db, "owner", "proposal.rejected", "proposal", proposal.id, {})
    db.commit()
    db.refresh(proposal)
    return proposal


def snooze_proposal(db: Session, proposal_id: str, version: int, approval_token: str) -> Proposal:
    proposal = db.get(Proposal, proposal_id)
    if not proposal:
        raise ServiceError(404, "Proposal не найден")
    if proposal.status != "pending" or version != proposal.version:
        raise ServiceError(409, "Proposal уже обработан или версия устарела")
    if not parse_and_verify_approval_token(
        approval_token, proposal.id, proposal.version, proposal.approval_nonce_hash
    ):
        raise ServiceError(409, "Недействительный approval token")
    proposal.status = "snoozed"
    proposal.version += 1
    audit(db, "owner", "proposal.snoozed", "proposal", proposal.id, {})
    db.commit()
    db.refresh(proposal)
    return proposal


def execute_proposal(db: Session, proposal_id: str) -> Proposal:
    proposal = db.get(Proposal, proposal_id)
    if not proposal:
        raise ServiceError(404, "Proposal не найден")
    if proposal.status == "executed":
        return proposal
    if proposal.status != "approved":
        raise ServiceError(409, "Исполнять можно только approved proposal")
    settings = get_settings()
    if not settings.execution_enabled:
        raise ServiceError(501, "Внешние адаптеры отключены: EXECUTION_ENABLED=false")

    # The flag is not an adapter. Until a real, idempotent adapter/outbox exists,
    # never claim that an external action was executed.
    raise ServiceError(501, "Внешний адаптер ещё не реализован")


def ingest_telegram_update(db: Session, update_id: int, payload: dict) -> Source:
    external_id = f"telegram:{update_id}"
    source = db.scalar(
        select(Source).where(Source.source_type == "telegram", Source.external_id == external_id)
    )
    if source:
        return source
    message = payload.get("message") or {}
    text = str(message.get("text") or "")
    source = Source(
        source_type="telegram",
        external_id=external_id,
        subject="Telegram message",
        content=text[:10000],
        metadata_json={"update_id": update_id, "chat_id": (message.get("chat") or {}).get("id")},
    )
    db.add(source)
    db.flush()
    audit(db, "telegram", "source.ingested", "source", source.id, {"update_id": update_id})
    db.commit()
    db.refresh(source)
    return source
