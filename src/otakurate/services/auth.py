import base64
import hashlib
import hmac
import os
import re

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import User

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,64}$")
PASSWORD_MIN_LENGTH = 8

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SALT_BYTES = 16


class AuthError(ValueError):
    pass


def validate_credentials(username: str, password: str) -> tuple[str, str]:
    username = username.strip()
    if not USERNAME_RE.fullmatch(username):
        raise AuthError(
            "Username must contain 3-64 characters: letters, digits, _, -, or ."
        )
    if len(password) < PASSWORD_MIN_LENGTH:
        raise AuthError(
            f"Password must contain at least {PASSWORD_MIN_LENGTH} characters."
        )
    return username, password


def hash_password(password: str) -> str:
    salt = os.urandom(_SALT_BYTES)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
    )
    encoded_salt = base64.urlsafe_b64encode(salt).decode("ascii")
    encoded_digest = base64.urlsafe_b64encode(digest).decode("ascii")
    return (
        "scrypt$"
        + str(_SCRYPT_N)
        + "$"
        + str(_SCRYPT_R)
        + "$"
        + str(_SCRYPT_P)
        + "$"
        + encoded_salt
        + "$"
        + encoded_digest
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, n, r, p, salt_text, digest_text = encoded.split("$")
        if scheme != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_text.encode("ascii"))
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(n),
            r=int(r),
            p=int(p),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def register_user(session: Session, *, username: str, password: str) -> User:
    username, password = validate_credentials(username, password)
    if session.scalar(select(User).where(User.username == username)) is not None:
        raise AuthError("Username is already registered.")

    user = User(username=username, password_hash=hash_password(password))
    session.add(user)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise AuthError("Username is already registered.") from exc
    return user


def authenticate_user(
    session: Session,
    *,
    username: str,
    password: str,
) -> User | None:
    user = session.scalar(select(User).where(User.username == username.strip()))
    if user is None or not user.is_active or not user.password_hash:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
