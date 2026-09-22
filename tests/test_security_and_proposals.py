from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.db import Base
from app.schemas import ProposalCreate
from app.security import hash_value, make_approval_token, parse_and_verify_approval_token
from app.services import ServiceError, approve_proposal, create_proposal


def test_approval_token_round_trip(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("APPROVAL_SIGNING_KEY", "test-signing-key")
    get_settings.cache_clear()
    token = make_approval_token("proposal-1", 1, "nonce")
    assert parse_and_verify_approval_token(token, "proposal-1", 1, hash_value("nonce"))
    assert not parse_and_verify_approval_token(token, "proposal-1", 2, hash_value("nonce"))
    assert not parse_and_verify_approval_token(token, "proposal-1", 1, hash_value("other"))


def test_expired_datetime_is_timezone_aware():
    value = datetime.now(timezone.utc)
    assert value.tzinfo is not None


def test_approval_is_single_use(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("APPROVAL_SIGNING_KEY", "test-signing-key")
    get_settings.cache_clear()

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    proposal, token = create_proposal(
        session,
        ProposalCreate(
            action_type="CREATE_EVENT",
            payload={"summary": "Review"},
            preview="Create event: Review",
            confidence=0.9,
            idempotency_key="test-event-0001",
        ),
    )

    approved = approve_proposal(session, proposal.id, 1, token)
    assert approved.status == "approved"
    assert approved.version == 2

    with pytest.raises(ServiceError) as replay:
        approve_proposal(session, proposal.id, 1, token)
    assert replay.value.status_code == 409
