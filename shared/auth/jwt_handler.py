"""
JWT Authentication Handler for STRATUM PROTOCOL
Handles token generation, validation, and user authentication
"""

import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class JWTHandler:
    """Handles JWT token operations"""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a new JWT access token
        
        Args:
            data: Payload data to encode in token
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """
        Create a new JWT refresh token
        
        Args:
            data: Payload data to encode in token
            
        Returns:
            Encoded JWT refresh token string
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT token
        
        Args:
            token: JWT token string to verify
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    @staticmethod
    def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
        """
        Extract current user from JWT token
        
        Args:
            credentials: HTTP authorization credentials from request
            
        Returns:
            User data from token payload
            
        Raises:
            HTTPException: If token is invalid
        """
        token = credentials.credentials
        payload = JWTHandler.verify_token(token)
        
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        return payload
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)


class RoleChecker:
    """Check user roles and permissions"""
    
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles
    
    def __call__(self, user: Dict[str, Any] = Security(JWTHandler.get_current_user)):
        """
        Verify user has required role
        
        Args:
            user: User data from JWT token
            
        Raises:
            HTTPException: If user doesn't have required role
        """
        user_role = user.get("role", "user")
        
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"User with role '{user_role}' is not authorized for this operation"
            )
        
        return user


# Example usage in FastAPI endpoints:
"""
from shared.auth.jwt_handler import JWTHandler, RoleChecker

# Protect endpoint with authentication
@app.get("/api/v1/protected")
async def protected_route(user: dict = Security(JWTHandler.get_current_user)):
    return {"message": f"Hello {user['username']}"}

# Protect endpoint with role-based access control
@app.post("/api/v1/admin")
async def admin_route(user: dict = Security(RoleChecker(["admin", "superadmin"]))):
    return {"message": "Admin access granted"}
"""
