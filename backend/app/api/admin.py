import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_user, hash_password, require_roles
from app.database import get_db
from app.models import User
from app.schemas import Page, PasswordReset, TemporaryPassword, UserAdminUpdate, UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["user administration"])


@router.get("", response_model=Page[UserResponse])
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Admin")),
):
    total = db.scalar(select(func.count()).select_from(User)) or 0
    items = db.scalars(select(User).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=UserResponse, status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Admin")),
):
    if db.scalar(select(User).where(func.lower(User.email) == payload.email)):
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email is already registered") from error
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin")),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    changes = payload.model_dump(exclude_unset=True)
    if "email" in changes:
        duplicate = db.scalar(select(User).where(func.lower(User.email) == changes["email"], User.id != user_id))
        if duplicate:
            raise HTTPException(status_code=409, detail="Email is already registered")
    removing_admin = user.role == "Admin" and user.is_active and (
        changes.get("role", user.role) != "Admin" or changes.get("is_active", user.is_active) is False
    )
    if removing_admin:
        active_admins = db.scalar(
            select(func.count()).select_from(User).where(User.role == "Admin", User.is_active.is_(True))
        ) or 0
        if active_admins <= 1:
            raise HTTPException(status_code=400, detail="The final active administrator cannot be deactivated or downgraded")
    for key, value in changes.items():
        setattr(user, key, value)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email is already registered") from error
    return user


@router.post("/{user_id}/reset-password", response_model=TemporaryPassword)
def reset_password(
    user_id: int,
    payload: PasswordReset,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Admin")),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    temporary_password = payload.password or secrets.token_urlsafe(18)
    user.password_hash = hash_password(temporary_password)
    db.commit()
    return {"temporary_password": temporary_password}


@router.delete("/{user_id}", status_code=204)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Admin")),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "Admin" and user.is_active:
        active_admins = db.scalar(
            select(func.count()).select_from(User).where(User.role == "Admin", User.is_active.is_(True))
        ) or 0
        if active_admins <= 1:
            raise HTTPException(status_code=400, detail="The final active administrator cannot be deactivated")
    user.is_active = False
    db.commit()
