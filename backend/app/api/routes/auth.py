
from authlib.integrations.httpx_client import AsyncOAuth2Client
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession, CurrentUser
from app.core.config import get_settings
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.models.user import User
from app.schemas.user import UserRead, TokenResponse

router = APIRouter()
settings = get_settings()


@router.get("/google/authorize")
async def google_authorize():
    client = AsyncOAuth2Client(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        redirect_uri=settings.oauth_redirect_uri,
    )
    authorization_url, _ = client.create_authorization_url(
        "https://accounts.google.com/o/oauth2/v2/auth",
        scope="openid email profile",
    )
    return {"authorization_url": authorization_url}


@router.post("/google/callback", response_model=TokenResponse)
async def google_callback(code: str, db: DbSession):
    client = AsyncOAuth2Client(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        redirect_uri=settings.oauth_redirect_uri,
    )

    try:
        await client.fetch_token(
            "https://oauth2.googleapis.com/token",
            code=code,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange code for token",
        )

    userinfo_response = await client.get(
        "https://www.googleapis.com/oauth2/v3/userinfo"
    )
    userinfo = userinfo_response.json()

    result = await db.execute(
        select(User).where(
            User.oauth_provider == "google",
            User.oauth_id == userinfo["sub"],
        )
    )
    user = result.scalar_one_or_none()

    if user is None:
        # Check if user exists by email
        result = await db.execute(select(User).where(User.email == userinfo["email"]))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                email=userinfo["email"],
                name=userinfo.get("name", ""),
                avatar_url=userinfo.get("picture"),
                oauth_provider="google",
                oauth_id=userinfo["sub"],
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            user.oauth_provider = "google"
            user.oauth_id = userinfo["sub"]
            if userinfo.get("picture"):
                user.avatar_url = userinfo["picture"]
            await db.commit()
            await db.refresh(user)

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserRead.model_validate(user),
    )


@router.get("/microsoft/authorize")
async def microsoft_authorize():
    client = AsyncOAuth2Client(
        client_id=settings.microsoft_client_id,
        client_secret=settings.microsoft_client_secret,
        redirect_uri=settings.oauth_redirect_uri,
    )
    authorization_url, _ = client.create_authorization_url(
        "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        scope="openid email profile",
    )
    return {"authorization_url": authorization_url}


@router.post("/microsoft/callback", response_model=TokenResponse)
async def microsoft_callback(code: str, db: DbSession):
    client = AsyncOAuth2Client(
        client_id=settings.microsoft_client_id,
        client_secret=settings.microsoft_client_secret,
        redirect_uri=settings.oauth_redirect_uri,
    )

    try:
        await client.fetch_token(
            "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            code=code,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange code for token",
        )

    userinfo_response = await client.get("https://graph.microsoft.com/v1.0/me")
    userinfo = userinfo_response.json()

    result = await db.execute(
        select(User).where(
            User.oauth_provider == "microsoft",
            User.oauth_id == userinfo["id"],
        )
    )
    user = result.scalar_one_or_none()

    if user is None:
        email = userinfo.get("mail") or userinfo.get("userPrincipalName")
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                email=email,
                name=userinfo.get("displayName", ""),
                oauth_provider="microsoft",
                oauth_id=userinfo["id"],
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            user.oauth_provider = "microsoft"
            user.oauth_id = userinfo["id"]
            await db.commit()
            await db.refresh(user)

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserRead.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: DbSession):
    token_data = verify_token(refresh_token, token_type="refresh")
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    new_access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        user=UserRead.model_validate(user),
    )


@router.get("/me", response_model=UserRead)
async def get_current_user_info(current_user: CurrentUser):
    return current_user
