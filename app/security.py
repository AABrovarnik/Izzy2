import hashlib
import hmac
import secrets

from .config import get_settings


def hash_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def make_approval_token(proposal_id: str, version: int, nonce: str) -> str:
    settings = get_settings()
    message = f"{proposal_id}:{version}:{nonce}".encode("utf-8")
    signature = hmac.new(
        settings.approval_signing_key.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()
    return f"{version}.{nonce}.{signature}"


def parse_and_verify_approval_token(token: str, proposal_id: str, version: int, nonce_hash: str) -> bool:
    try:
        token_version, nonce, signature = token.split(".", 2)
        if int(token_version) != version or not hmac.compare_digest(hash_value(nonce), nonce_hash):
            return False
    except (ValueError, TypeError):
        return False
    expected = make_approval_token(proposal_id, version, nonce)
    return hmac.compare_digest(expected, token)


def new_approval_nonce() -> str:
    return secrets.token_urlsafe(32)
