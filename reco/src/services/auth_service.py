from datetime import datetime, timedelta
from typing import Optional, Dict
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import logging
from sqlalchemy.orm import Session
from src.data.database import User, get_session

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, config: Dict):
        self.secret_key = config['auth']['secret_key']
        self.algorithm = config['auth']['algorithm']
        self.access_token_expire_minutes = config['auth']['access_token_expire_minutes']
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.db = get_session()
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
        
    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return self.pwd_context.hash(password)
        
    def create_access_token(self, data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + (
            expires_delta or timedelta(minutes=self.access_token_expire_minutes)
        )
        to_encode.update({"exp": expire})
        try:
            encoded_jwt = jwt.encode(
                to_encode, 
                self.secret_key, 
                algorithm=self.algorithm
            )
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating access token: {str(e)}")
            raise
            
    def decode_token(self, token: str) -> Dict:
        """Decode and validate JWT token."""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
            
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user."""
        try:
            user = self.db.query(User).filter(User.username == username).first()
            if not user:
                return None
            if not self.verify_password(password, user.hashed_password):
                return None
            return user
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return None
            
    def create_user(self, username: str, email: str, password: str) -> User:
        """Create a new user."""
        try:
            # Check if user exists
            if self.db.query(User).filter(User.username == username).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already registered"
                )
                
            # Create new user
            hashed_password = self.get_password_hash(password)
            user = User(
                username=username,
                email=email,
                hashed_password=hashed_password
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            return user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise
            
    def get_current_user(self, token: str) -> User:
        """Get current user from token."""
        try:
            payload = self.decode_token(token)
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials"
                )
            user = self.db.query(User).filter(User.username == username).first()
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            return user
        except Exception as e:
            logger.error(f"Error getting current user: {str(e)}")
            raise
            
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Change user password."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
                
            if not self.verify_password(old_password, user.hashed_password):
                return False
                
            user.hashed_password = self.get_password_hash(new_password)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error changing password: {str(e)}")
            return False
            
    def close(self):
        """Close database session."""
        self.db.close() 