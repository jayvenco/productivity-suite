from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.session import read_session_token
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.services.api_tokens import hash_api_token


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    user_id = read_session_token(token)
    if user_id is None:
        return None
    return db.get(User, user_id)


def require_user(user: User | None = Depends(get_current_user)) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
    return user


def require_api_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Auth voor /api/v1/...: een los token in de Authorization-header i.p.v. de
    sessie-cookie, zodat een extern script/agent geen browser-login nodig heeft."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ontbrekend of ongeldig API-token")

    token = auth_header[len("Bearer ") :].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ontbrekend of ongeldig API-token")

    token_hash = hash_api_token(token)
    user = db.query(User).filter(User.api_token_hash == token_hash).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ontbrekend of ongeldig API-token")
    return user
