from fastapi import Header, HTTPException
from firebase_admin import auth

def verify_firebase_token(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication token")
    try:
        return auth.verify_id_token(authorization[len("Bearer "):].strip())
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired Firebase token") from exc
