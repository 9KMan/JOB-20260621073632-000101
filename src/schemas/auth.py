// src/schemas/auth.py
"""Authentication schemas."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    """JWT token response."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """JWT token payload."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    sub: str
    exp: datetime
    iat: Optional[datetime] = None
    role: Optional[str] = None
