from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from pydantic.networks import EmailStr
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from dependencies import get_query_token
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import the db module
from db import conn
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Registration settings
SIGNUPS_ENABLED = os.getenv("SIGNUPS_ENABLED", "true").lower() == "true"
print(f"Signups enabled: {SIGNUPS_ENABLED}")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Models
class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    avatar_url: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

# Router
router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={401: {"description": "Unauthorized"}},
)

# Helper functions
def verify_password(plain_password, hashed_password):
    print(f"Verifying password: {plain_password[:2]}*** against hash: {hashed_password[:10]}...")
    try:
        result = pwd_context.verify(plain_password, hashed_password)
        print(f"Password verification result: {result}")
        return result
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(username: str):
    if conn is None:
        # Mock user for development/testing
        if username == "admin":
            return {
                "id": 1,
                "username": "admin",
                "email": "admin@example.com",
                "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # password: admin123
                "full_name": "Admin User",
                "role": "admin",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "last_login": None,
                "avatar_url": None
            }
        return None

    try:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, username, email, password_hash, full_name, role, is_active, created_at, last_login, avatar_url
                FROM users
                WHERE username = %s
            """, (username,))

            user = cursor.fetchone()
            if not user:
                return None

            return {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "password_hash": user[3],
                "full_name": user[4],
                "role": user[5],
                "is_active": user[6],
                "created_at": user[7],
                "last_login": user[8],
                "avatar_url": user[9]
            }
        except Exception as e:
            print(f"Error retrieving user: {e}")
            return None
        finally:
            cursor.close()
    except Exception as e:
        print(f"Error with database connection: {e}")
        return None

def authenticate_user(username: str, password: str):
    print(f"Authenticating user: {username}")
    user = get_user(username)
    if not user:
        print(f"User not found: {username}")
        return False
    print(f"Verifying password for user: {username}")
    if not verify_password(password, user["password_hash"]):
        print(f"Password verification failed for user: {username}")
        return False
    print(f"Authentication successful for user: {username}")
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user = Depends(get_current_user)):
    if not current_user["is_active"]:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Endpoints
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"Login attempt for user: {form_data.username}")
    print(f"Password provided: {form_data.password[:2]}***")
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        print(f"Authentication failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    print(f"Authentication successful for user: {form_data.username}")

    # Update last login time if database connection is available
    if conn is not None:
        try:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE users
                    SET last_login = now()
                    WHERE username = %s
                """, (user["username"],))
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"Error updating last login: {e}")
            finally:
                cursor.close()
        except Exception as e:
            print(f"Error with database connection: {e}")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )

    # Remove password hash from response
    user_data = {k: v for k, v in user.items() if k != "password_hash"}

    return {"access_token": access_token, "token_type": "bearer", "user": user_data}

@router.get("/signup-status")
async def get_signup_status():
    """Check if signups are currently enabled"""
    return {"signups_enabled": SIGNUPS_ENABLED}

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    # Check if signups are enabled
    if not SIGNUPS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="New user registration is currently disabled"
        )
    if conn is None:
        # Mock registration for development/testing
        if user.username == "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered"
            )

        # Return a mock user
        return {
            "id": 2,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": "user",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None,
            "avatar_url": None
        }

    # Check if username or email already exists
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT username FROM users WHERE username = %s OR email = %s", (user.username, user.email))
            existing_user = cursor.fetchone()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username or email already registered"
                )

            # Hash the password
            hashed_password = get_password_hash(user.password)

            # Insert new user
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name)
                VALUES (%s, %s, %s, %s)
                RETURNING id, username, email, full_name, role, is_active, created_at, last_login, avatar_url
            """, (user.username, user.email, hashed_password, user.full_name))

            new_user = cursor.fetchone()
            conn.commit()

            return {
                "id": new_user[0],
                "username": new_user[1],
                "email": new_user[2],
                "full_name": new_user[3],
                "role": new_user[4],
                "is_active": new_user[5],
                "created_at": new_user[6],
                "last_login": new_user[7],
                "avatar_url": new_user[8]
            }
        except Exception as e:
            conn.rollback()
            print(f"Error registering user: {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error registering user"
            )
        finally:
            cursor.close()
    except Exception as e:
        print(f"Error with database connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error"
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user = Depends(get_current_active_user)):
    # Remove password hash from response
    user_data = {k: v for k, v in current_user.items() if k != "password_hash"}
    return user_data

@router.get("/signup-status")
async def get_signup_status():
    """Check if new user registration is enabled"""
    return {"signups_enabled": SIGNUPS_ENABLED}

@router.post("/change-password")
async def change_password(old_password: str, new_password: str, current_user = Depends(get_current_active_user)):
    # Verify old password
    if not verify_password(old_password, current_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )

    # Hash new password
    hashed_password = get_password_hash(new_password)

    # If database connection is not available, return success for development/testing
    if conn is None:
        return {"message": "Password updated successfully (mock)"}

    # Update password
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE users
                SET password_hash = %s
                WHERE id = %s
            """, (hashed_password, current_user["id"]))
            conn.commit()

            return {"message": "Password updated successfully"}
        except Exception as e:
            conn.rollback()
            print(f"Error changing password: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error changing password"
            )
        finally:
            cursor.close()
    except Exception as e:
        print(f"Error with database connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error"
        )
