import hmac
import hashlib
from fastapi import HTTPException


def verify_signature(payload: bytes, signature: str, secret: str):
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")

    expected = "sha256=" + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    