from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import acreate_client

from config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthRequest(BaseModel):
    email: str
    password: str


@router.post("/signup")
async def signup(body: AuthRequest):
    client = await acreate_client(settings.supabase_url, settings.supabase_anon_key)
    try:
        response = await client.auth.sign_up({"email": body.email, "password": body.password})
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "user": {"id": response.user.id, "email": response.user.email} if response.user else None,
        "session": {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
        } if response.session else None,
    }


@router.post("/signin")
async def signin(body: AuthRequest):
    client = await acreate_client(settings.supabase_url, settings.supabase_anon_key)
    try:
        response = await client.auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "user": {"id": response.user.id, "email": response.user.email} if response.user else None,
        "session": {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
        } if response.session else None,
    }


@router.post("/signout")
async def signout():
    # Browser should call _supabase.auth.signOut() to clear the local session.
    # This endpoint calls sign_out() server-side for programmatic/CLI clients,
    # but note: supabase-py auth sign_out() only revokes the refresh token;
    # the access JWT remains valid until its natural expiry (~1 hour by default).
    client = await acreate_client(settings.supabase_url, settings.supabase_anon_key)
    try:
        await client.auth.sign_out()
    except Exception:
        pass  # best-effort; client may already be signed out
    return {"status": "ok"}
