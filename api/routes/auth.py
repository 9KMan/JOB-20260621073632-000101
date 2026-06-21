// api/routes/auth.py
"""Authentication routes."""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_current_user
from api.schemas.auth import (
    UserCreate,
    UserResponse,
    UserLogin,
    TokenResponse,
)
from core.config import settings
from core.database import get_db
from core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
)
from models.user import User, UserRole

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
) -> User:
    """
    Register a new user.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        Created user
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Validate role
    try:
        role = UserRole(user_data.role.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {[r.value for r in UserRole]}",
        )
    
    # Create user
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=role,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db),
) -> dict:
    """
    Authenticate user and return JWT token.
    
    Args:
        credentials: User login credentials
        db: Database session
        
    Returns:
        JWT token and user info
    """
    # Find user
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=settings.jwt_expiration_minutes),
        additional_claims={
            "role": user.role.value,
            "email": user.email,
        },
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_expiration_minutes * 60,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current authenticated user info.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User info
    """
    return current_user


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Refresh the current user's access token.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        New JWT token and user info
    """
    access_token = create_access_token(
        subject=str(current_user.id),
        expires_delta=timedelta(minutes=settings.jwt_expiration_minutes),
        additional_claims={
            "role": current_user.role.value,
            "email": current_user.email,
        },
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_expiration_minutes * 60,
        user=UserResponse.model_validate(current_user),
    )
