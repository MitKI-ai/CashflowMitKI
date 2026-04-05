import re
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.jwt import create_access_token
from app.core.security import hash_password, verify_password
from app.database import get_db
from app.dependencies import get_current_user
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Helper for SSO (used by tests) ────────────────────────────────────────────

def fetch_google_profile(code: str) -> dict | None:  # pragma: no cover
    """Exchange Google auth code for user profile. Overridable in tests."""
    import httpx

    from app.config import settings
    token_resp = httpx.post("https://oauth2.googleapis.com/token", data={
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": "postmessage",
        "grant_type": "authorization_code",
    })
    if token_resp.status_code != 200:
        return None
    access_token = token_resp.json().get("access_token")
    info_resp = httpx.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if info_resp.status_code != 200:
        return None
    return info_resp.json()


def fetch_microsoft_profile(code: str) -> dict | None:  # pragma: no cover
    """Exchange Microsoft auth code for user profile. Overridable in tests."""
    import httpx

    from app.config import settings
    token_resp = httpx.post(
        "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        data={
            "code": code,
            "client_id": settings.microsoft_client_id,
            "client_secret": settings.microsoft_client_secret,
            "redirect_uri": "postmessage",
            "grant_type": "authorization_code",
            "scope": "openid email profile",
        },
    )
    if token_resp.status_code != 200:
        return None
    access_token = token_resp.json().get("access_token")
    info_resp = httpx.get(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if info_resp.status_code != 200:
        return None
    data = info_resp.json()
    return {
        "sub": data.get("id"),
        "email": data.get("mail") or data.get("userPrincipalName"),
        "name": data.get("displayName"),
    }


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text


@router.post("/register")
def register(data: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    slug = _slugify(data.tenant_name)
    if db.query(Tenant).filter(Tenant.slug == slug).first():
        raise HTTPException(status_code=400, detail="Tenant name already taken")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    tenant = Tenant(name=data.tenant_name, slug=slug)
    db.add(tenant)
    db.flush()

    user = User(
        tenant_id=tenant.id,
        email=data.email,
        password_hash=hash_password(data.password),
        display_name=data.display_name,
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    request.session["user_id"] = user.id
    request.session["tenant_id"] = tenant.id
    return {"message": "Registration successful", "user_id": user.id, "tenant_id": tenant.id}


@router.post("/login")
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email, User.is_active == True).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user.last_login_at = datetime.now(UTC)
    db.commit()

    request.session["user_id"] = user.id
    request.session["tenant_id"] = user.tenant_id
    return {"message": "Login successful", "user_id": user.id, "role": user.role}


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out"}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "display_name": current_user.display_name,
        "role": current_user.role,
        "tenant_id": current_user.tenant_id,
        "locale": current_user.locale,
    }


# ── JWT Token endpoint (OAuth2 password flow) ─────────────────────────────────

@router.post("/token")
def token(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == username, User.is_active == True).first()  # noqa: E712
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token, expires_in = create_access_token(
        user_id=user.id, tenant_id=user.tenant_id, role=user.role
    )
    return {"access_token": access_token, "token_type": "bearer", "expires_in": expires_in}


# ── SSO — Google ──────────────────────────────────────────────────────────────

@router.get("/sso/google")
def sso_google_redirect():
    from app.config import settings
    if not settings.google_client_id:
        raise HTTPException(status_code=501, detail="Google SSO not configured")
    params = (
        "response_type=code"
        f"&client_id={settings.google_client_id}"
        "&redirect_uri=postmessage"
        "&scope=openid%20email%20profile"
        "&state=google"
    )
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@router.get("/sso/google/callback")
def sso_google_callback(
    code: str | None = None,
    state: str | None = None,
    request: Request = None,
    db: Session = Depends(get_db),
):
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")
    profile = fetch_google_profile(code)
    if not profile:
        raise HTTPException(status_code=400, detail="Failed to fetch Google profile")
    return _sso_login(db, request, provider="google", profile=profile)


# ── SSO — Microsoft ───────────────────────────────────────────────────────────

@router.get("/sso/microsoft")
def sso_microsoft_redirect():
    from app.config import settings
    if not settings.microsoft_client_id:
        raise HTTPException(status_code=501, detail="Microsoft SSO not configured")
    params = (
        "response_type=code"
        f"&client_id={settings.microsoft_client_id}"
        "&redirect_uri=postmessage"
        "&scope=openid%20email%20profile"
        "&state=microsoft"
    )
    from fastapi.responses import RedirectResponse
    return RedirectResponse(
        url=f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{params}"
    )


@router.get("/sso/microsoft/callback")
def sso_microsoft_callback(
    code: str | None = None,
    state: str | None = None,
    request: Request = None,
    db: Session = Depends(get_db),
):
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")
    profile = fetch_microsoft_profile(code)
    if not profile:
        raise HTTPException(status_code=400, detail="Failed to fetch Microsoft profile")
    return _sso_login(db, request, provider="microsoft", profile=profile)


# ── SSO shared login helper ───────────────────────────────────────────────────

def _sso_login(db: Session, request: Request, provider: str, profile: dict):
    email = profile.get("email")
    oauth_sub = str(profile.get("sub", ""))
    name = profile.get("name", email)

    if not email:
        raise HTTPException(status_code=400, detail="No email in OAuth profile")

    # Find existing user by email
    user = db.query(User).filter(User.email == email, User.is_active == True).first()  # noqa: E712

    if user:
        # Update SSO fields
        user.oauth_provider = provider
        user.oauth_sub = oauth_sub
        db.commit()
    else:
        # Auto-register: create new tenant + admin user
        slug = re.sub(r"[^\w]", "-", email.split("@")[0].lower()) + "-sso"
        tenant = Tenant(name=name or email, slug=slug)
        db.add(tenant)
        db.flush()
        user = User(
            tenant_id=tenant.id,
            email=email,
            password_hash="",
            display_name=name or email,
            role="admin",
            oauth_provider=provider,
            oauth_sub=oauth_sub,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if request:
        request.session["user_id"] = user.id
        request.session["tenant_id"] = user.tenant_id

    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard", status_code=302)
