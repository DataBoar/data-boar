"""
JSON endpoints for vendor-neutral WebAuthn (Phase 1). Mounted under ``/auth/webauthn``.

Disabled unless ``api.webauthn.enabled`` is true. Session cookie feeds the Phase 1b HTML gate when
credentials exist (#86); RBAC remains future work.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.structs import PublicKeyCredentialDescriptor

from core.webauthn_rp import challenges, session_cookie
from core.webauthn_rp.settings import (
    expected_origins,
    resolve_token_secret,
    user_id_bytes,
    webauthn_block,
)
from core.forwarded_headers import forwarded_proto_posture

router = APIRouter(prefix="/auth/webauthn", tags=["webauthn"])


def _cookie_secure(request: Request) -> bool:
    posture = forwarded_proto_posture(request, _get_config())
    return posture.get("effective_scheme") == "https"


def _get_config() -> dict[str, Any]:
    from api.routes import _get_config as gc

    return gc()


def _get_engine():
    from api.routes import _get_engine as ge

    return ge()


def _wa_secret_or_raise() -> tuple[dict[str, Any], str]:
    wa = webauthn_block(_get_config())
    if wa is None:
        raise HTTPException(status_code=404, detail="WebAuthn is not enabled.")
    secret = resolve_token_secret(wa)
    if not secret:
        raise HTTPException(
            status_code=503,
            detail="WebAuthn token secret is not configured (set DATA_BOAR_WEBAUTHN_TOKEN_SECRET or api.webauthn.token_secret_from_env).",
        )
    return wa, secret


def _wa_or_404() -> dict[str, Any]:
    wa, _s = _wa_secret_or_raise()
    return wa


@router.post("/registration/options")
async def registration_options() -> JSONResponse:
    """Return PublicKeyCredentialCreationOptions JSON plus opaque ``state`` for the verify step."""
    wa, _secret = _wa_secret_or_raise()
    dbm = _get_engine().db_manager
    if dbm.webauthn_credential_count() > 0:
        raise HTTPException(
            status_code=403,
            detail="A passkey is already registered. Use authentication or wipe credentials.",
        )
    uid = user_id_bytes(wa)
    rp_id = str(wa.get("rp_id") or "localhost")
    rp_name = str(wa.get("rp_name") or "Data Boar")
    user_name = str(wa.get("user_display_name") or "operator")
    exclude = []
    for row in dbm.webauthn_list_credentials():
        cid = row["credential_id"]
        if isinstance(cid, (bytes, memoryview)):
            exclude.append(
                PublicKeyCredentialDescriptor(
                    id=bytes(cid),
                    type="public-key",
                )
            )
    options = generate_registration_options(
        rp_id=rp_id,
        rp_name=rp_name,
        user_name=user_name,
        user_id=uid,
        user_display_name=user_name,
        exclude_credentials=exclude or None,
    )
    chal_raw = options.challenge
    chal = bytes(chal_raw) if not isinstance(chal_raw, bytes) else chal_raw
    token = challenges.new_state_token()
    challenges.put_pending(token=token, kind="reg", challenge=chal)
    payload = json.loads(options_to_json(options))
    resp = JSONResponse(content={"options": payload, "state": token})
    return resp


@router.post("/registration/verify")
async def registration_verify(request: Request) -> JSONResponse:
    wa, secret = _wa_secret_or_raise()
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Expected JSON object.")
    state = str(body.get("state") or "").strip()
    cred = body.get("credential")
    if not state or cred is None:
        raise HTTPException(status_code=400, detail="Missing state or credential.")
    pending = challenges.pop_pending(state)
    if pending is None or pending.kind != "reg":
        raise HTTPException(status_code=400, detail="Invalid or expired state.")
    rp_id = str(wa.get("rp_id") or "localhost")
    origins = expected_origins(wa)
    try:
        verified = verify_registration_response(
            credential=cred,
            expected_challenge=pending.challenge,
            expected_rp_id=rp_id,
            expected_origin=origins,
        )
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Verification failed: {e!s}"
        ) from e
    uid = user_id_bytes(wa)
    dbm = _get_engine().db_manager
    dbm.webauthn_save_credential(
        user_id=uid,
        credential_id=verified.credential_id,
        public_key=verified.credential_public_key,
        sign_count=verified.sign_count,
    )
    cookie = session_cookie.sign_session(secret, uid)
    r = JSONResponse(content={"ok": True, "registered": True})
    r.set_cookie(
        key=session_cookie.COOKIE_NAME,
        value=cookie,
        max_age=session_cookie.MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(request),
        path="/",
    )
    return r


@router.post("/authentication/options")
async def authentication_options() -> JSONResponse:
    wa, _secret = _wa_secret_or_raise()
    dbm = _get_engine().db_manager
    rows = dbm.webauthn_list_credentials()
    if not rows:
        raise HTTPException(
            status_code=404, detail="No passkey registered yet. Use registration first."
        )
    rp_id = str(wa.get("rp_id") or "localhost")
    allow = [
        PublicKeyCredentialDescriptor(id=bytes(r["credential_id"]), type="public-key")
        for r in rows
    ]
    options = generate_authentication_options(
        rp_id=rp_id,
        allow_credentials=allow,
    )
    chal_raw = options.challenge
    chal = bytes(chal_raw) if not isinstance(chal_raw, bytes) else chal_raw
    token = challenges.new_state_token()
    challenges.put_pending(token=token, kind="auth", challenge=chal)
    payload = json.loads(options_to_json(options))
    return JSONResponse(content={"options": payload, "state": token})


@router.post("/authentication/verify")
async def authentication_verify(request: Request) -> JSONResponse:
    wa, secret = _wa_secret_or_raise()
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Expected JSON object.")
    state = str(body.get("state") or "").strip()
    cred = body.get("credential")
    if not state or cred is None:
        raise HTTPException(status_code=400, detail="Missing state or credential.")
    pending = challenges.pop_pending(state)
    if pending is None or pending.kind != "auth":
        raise HTTPException(status_code=400, detail="Invalid or expired state.")
    rp_id = str(wa.get("rp_id") or "localhost")
    origins = expected_origins(wa)
    dbm = _get_engine().db_manager
    rows = dbm.webauthn_list_credentials()
    raw_id = cred.get("rawId") if isinstance(cred, dict) else None
    if not raw_id:
        raise HTTPException(status_code=400, detail="credential.rawId missing.")
    from webauthn.helpers import base64url_to_bytes

    try:
        cid = base64url_to_bytes(raw_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid rawId.") from e
    match = None
    for r in rows:
        if bytes(r["credential_id"]) == cid:
            match = r
            break
    if match is None:
        raise HTTPException(status_code=400, detail="Unknown credential.")
    try:
        verified = verify_authentication_response(
            credential=cred,
            expected_challenge=pending.challenge,
            expected_rp_id=rp_id,
            expected_origin=origins,
            credential_public_key=bytes(match["public_key"]),
            credential_current_sign_count=int(match["sign_count"]),
        )
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Verification failed: {e!s}"
        ) from e
    dbm.webauthn_update_sign_count(cid, verified.new_sign_count)
    uid = bytes(match["user_id"])
    cookie = session_cookie.sign_session(secret, uid)
    r = JSONResponse(content={"ok": True, "authenticated": True})
    r.set_cookie(
        key=session_cookie.COOKIE_NAME,
        value=cookie,
        max_age=session_cookie.MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(request),
        path="/",
    )
    return r


@router.get("/status")
async def webauthn_status(request: Request) -> JSONResponse:
    _wa, secret = _wa_secret_or_raise()
    dbm = _get_engine().db_manager
    n = dbm.webauthn_credential_count()
    raw = request.cookies.get(session_cookie.COOKIE_NAME)
    authed = False
    if raw:
        uid = session_cookie.verify_session_cookie(secret, raw)
        authed = uid is not None
    return JSONResponse(
        {
            "enabled": True,
            "registered_credentials": n,
            "session_authenticated": authed,
        }
    )


@router.post("/logout")
async def webauthn_logout() -> JSONResponse:
    _wa_or_404()
    r = JSONResponse(content={"ok": True})
    r.delete_cookie(session_cookie.COOKIE_NAME, path="/")
    return r


def register_webauthn_routes(app: Any) -> None:
    """Attach WebAuthn router to the FastAPI app."""
    app.include_router(router)
