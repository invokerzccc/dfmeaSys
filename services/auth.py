"""认证、会话与用户管理。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Request, Response, status

import config
from db.database import get_db

SESSION_COOKIE = "dfmea_session"
HASH_NAME = "pbkdf2_sha256"
ITERATIONS = 260000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return "{}${}${}${}".format(
        HASH_NAME,
        ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        alg, iterations, salt_b64, digest_b64 = stored.split("$", 3)
        if alg != HASH_NAME:
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def authenticate(username: str, password: str):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM user_account WHERE username = ? AND is_active = 1",
            (username.strip(),),
        ).fetchone()
        if not row or not verify_password(password, row["password_hash"]):
            return None
        return _public_user(row)
    finally:
        conn.close()


def create_session(response: Response, user_id: int) -> None:
    token = secrets.token_urlsafe(32)
    expires = datetime.now() + timedelta(days=config.SESSION_DAYS)
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO auth_session (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
            (_hash_token(token), user_id, expires.strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
    finally:
        conn.close()
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        max_age=config.SESSION_DAYS * 24 * 3600,
    )


def clear_session(request: Request, response: Response) -> None:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        conn = get_db()
        try:
            conn.execute("DELETE FROM auth_session WHERE token_hash = ?", (_hash_token(token),))
            conn.commit()
        finally:
            conn.close()
    response.delete_cookie(SESSION_COOKIE)


def get_current_user_from_request(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    conn = get_db()
    try:
        row = conn.execute(
            """SELECT u.*
               FROM auth_session s
               JOIN user_account u ON s.user_id = u.id
               WHERE s.token_hash = ?
                 AND s.expires_at > datetime('now', 'localtime')
                 AND u.is_active = 1""",
            (_hash_token(token),),
        ).fetchone()
        return _public_user(row) if row else None
    finally:
        conn.close()


def require_current_user(request: Request):
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    return user


def require_admin(user=Depends(require_current_user)):
    if not user["is_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user


def list_users():
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT id, username, display_name, is_admin, is_active, created_at, updated_at
               FROM user_account ORDER BY id"""
        ).fetchall()
        return [_public_user(row) for row in rows]
    finally:
        conn.close()


def create_user(username: str, password: str, display_name: str = "", is_admin: bool = False):
    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO user_account (username, password_hash, display_name, is_admin)
               VALUES (?, ?, ?, ?)""",
            (username.strip(), hash_password(password), display_name.strip(), 1 if is_admin else 0),
        )
        conn.commit()
        return get_user(cur.lastrowid)
    finally:
        conn.close()


def update_user(user_id: int, **kwargs):
    allowed = {"display_name", "is_admin", "is_active"}
    updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if kwargs.get("password"):
        updates["password_hash"] = hash_password(kwargs["password"])
    if not updates:
        return get_user(user_id)
    conn = get_db()
    try:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = [1 if isinstance(v, bool) and v else 0 if isinstance(v, bool) else v for v in updates.values()]
        cur = conn.execute(
            f"UPDATE user_account SET {set_clause}, updated_at = datetime('now','localtime') WHERE id = ?",
            values + [user_id],
        )
        conn.commit()
        return get_user(user_id) if cur.rowcount else None
    finally:
        conn.close()


def get_user(user_id: int):
    conn = get_db()
    try:
        row = conn.execute(
            """SELECT id, username, display_name, is_admin, is_active, created_at, updated_at
               FROM user_account WHERE id = ?""",
            (user_id,),
        ).fetchone()
        return _public_user(row) if row else None
    finally:
        conn.close()


def _public_user(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"] or row["username"],
        "is_admin": bool(row["is_admin"]),
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
