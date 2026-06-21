"""Authentication service for FlowPilot AI."""

from datetime import datetime, timedelta
from typing import Optional, Tuple
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from src.database.session import get_db_session
from src.models.user import User
from src.models.organization import Organization
from src.services.auth.schemas import TokenPayload
from src.core.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password."""
    db = next(get_db_session())
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if user.is_deleted or not user.is_active:
            return None
        return user
    finally:
        db.close()


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_REFRESH_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str, is_refresh: bool = False) -> TokenPayload:
    """Decode and validate a JWT token."""
    secret_key = settings.JWT_REFRESH_SECRET_KEY if is_refresh else settings.JWT_SECRET_KEY
    
    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        token_type = payload.get("type")
        expected_type = "refresh" if is_refresh else "access"
        
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenPayload(**payload)
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def login_user(email: str, password: str) -> Tuple[str, str, int]:
    """Login a user and return access and refresh tokens."""
    user = authenticate_user(email, password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user roles and permissions
    roles = [role.name for role in user.roles]
    permissions = []
    for role in user.roles:
        permissions.extend([perm.name for perm in role.permissions])
    
    # Create token data
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "organization_id": str(user.organization_id),
        "roles": roles,
        "permissions": list(set(permissions))
    }
    
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)
    
    return access_token, refresh_token, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


async def refresh_access_token(refresh_token: str) -> Tuple[str, str, int]:
    """Refresh an access token using a refresh token."""
    payload = decode_token(refresh_token, is_refresh=True)
    
    db = next(get_db_session())
    try:
        user = db.query(User).filter(User.id == payload.sub).first()
        
        if not user or user.is_deleted or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create new tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "organization_id": str(user.organization_id),
            "roles": [role.name for role in user.roles],
            "permissions": list(set(
                perm.name for role in user.roles for perm in role.permissions
            ))
        }
        
        new_access_token = create_access_token(data=token_data)
        new_refresh_token = create_refresh_token(data=token_data)
        
        return new_access_token, new_refresh_token, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    finally:
        db.close()


async def change_password(user_id: str, current_password: str, new_password: str) -> bool:
    """Change a user's password."""
    db = next(get_db_session())
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        db.refresh(user)
        
        return True
    finally:
        db.close()
