from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from pydantic.networks import EmailStr
from typing import Optional, Union, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from dependencies import get_query_token
import sys
import os
import logging
import uuid
import time
import re

# Configure logging
logger = logging.getLogger(__name__)

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import the db module and config
from db import get_db_connection
from db.token_blacklist import add_to_blacklist, is_blacklisted, get_blacklist_stats
from db.secure_access import get_secure_db
from config import Config
from utils.password_validator import validate_password_strength, get_password_strength_feedback, get_password_requirements

# JWT settings
SECRET_KEY = Config.JWT_SECRET
ALGORITHM = Config.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = Config.JWT_EXPIRATION
REFRESH_TOKEN_EXPIRE_DAYS = Config.get("REFRESH_TOKEN_EXPIRE_DAYS", 7)  # Default to 7 days

# Registration settings
SIGNUPS_ENABLED = Config.SIGNUPS_ENABLED
logger.info(f"Signups enabled: {SIGNUPS_ENABLED}")

# Password security settings
MIN_PASSWORD_LENGTH = Config.get("MIN_PASSWORD_LENGTH", 8)
REQUIRE_SPECIAL_CHARS = Config.get("REQUIRE_SPECIAL_CHARS", True)
REQUIRE_NUMBERS = Config.get("REQUIRE_NUMBERS", True)
REQUIRE_UPPERCASE = Config.get("REQUIRE_UPPERCASE", True)
REQUIRE_LOWERCASE = Config.get("REQUIRE_LOWERCASE", True)
MAX_LOGIN_ATTEMPTS = Config.get("MAX_LOGIN_ATTEMPTS", 5)
LOCKOUT_DURATION_MINUTES = Config.get("LOCKOUT_DURATION_MINUTES", 15)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)

# Cookie names
ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"
CSRF_TOKEN_COOKIE = "csrf_token"

# Function to get token from either header or cookie
async def get_token_from_header_or_cookie(
    request: Request,
    token: str = Depends(oauth2_scheme),
    access_token: Optional[str] = Cookie(None, alias=ACCESS_TOKEN_COOKIE)
) -> Optional[str]:
    """Get token from either Authorization header or cookie."""
    # First try the OAuth2 scheme (Authorization header)
    if token:
        return token

    # Then try the cookie
    if access_token:
        return access_token

    # Finally, try to get it from the query parameters (for backward compatibility)
    query_params = request.query_params
    if "token" in query_params:
        return query_params["token"]

    return None

# Function to get refresh token from cookie
async def get_refresh_token_from_cookie(
    refresh_token: Optional[str] = Cookie(None, alias=REFRESH_TOKEN_COOKIE)
) -> Optional[str]:
    """Get refresh token from cookie."""
    return refresh_token

# Function to validate CSRF token
async def validate_csrf_token(
    request: Request,
    csrf_token_cookie: Optional[str] = Cookie(None, alias=CSRF_TOKEN_COOKIE)
) -> bool:
    """Validate CSRF token."""
    if not csrf_token_cookie:
        return False

    # Get CSRF token from header
    csrf_token_header = request.headers.get("X-CSRF-Token")
    if not csrf_token_header:
        return False

    # Compare tokens
    return csrf_token_cookie == csrf_token_header

# Models
class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    user: dict
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    user_role: Optional[str] = None
    jti: Optional[str] = None
    token_type: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: Optional[str] = None

class PasswordStrengthResponse(BaseModel):
    is_strong: bool
    score: int
    feedback: List[str]

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
    logger.debug(f"Verifying password: {plain_password[:2]}*** against hash: {hashed_password[:10]}...")
    try:
        result = pwd_context.verify(plain_password, hashed_password)
        logger.debug(f"Password verification result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(username: str):
    # Try to get a database connection
    try:
        # Use a regular connection since this is for the users table, not subject to RLS
        with get_db_connection() as db_conn:
            if db_conn is None:
                # Mock user for development/testing
                if username == "admin":
                    logger.warning("Database connection not available, using mock admin user")
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
                logger.warning(f"Database connection not available and user {username} not found")
                return None

            cursor = db_conn.cursor()
            try:
                cursor.execute("""
                    SELECT id, username, email, password_hash, full_name, role, is_active, created_at, last_login, avatar_url
                    FROM users
                    WHERE username = %s
                """, (username,))

                user = cursor.fetchone()
                if not user:
                    logger.debug(f"User not found: {username}")
                    return None

                logger.debug(f"User found: {username}")
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
                logger.error(f"Error retrieving user: {e}")
                return None
            finally:
                cursor.close()
    except Exception as e:
        logger.error(f"Error with database connection: {e}")
        # Fall back to mock user for development/testing
        if username == "admin":
            logger.warning("Using mock admin user due to database connection error")
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

def authenticate_user(username: str, password: str):
    logger.info(f"Authenticating user: {username}")
    user = get_user(username)
    if not user:
        logger.warning(f"User not found: {username}")
        return False
    logger.debug(f"Verifying password for user: {username}")
    if not verify_password(password, user["password_hash"]):
        logger.warning(f"Password verification failed for user: {username}")
        return False
    logger.info(f"Authentication successful for user: {username}")
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None, user_id: int = None, user_role: str = None) -> Tuple[str, float, str]:
    """
    Create an access token.

    Args:
        data (dict): The data to encode in the token
        expires_delta (Optional[timedelta], optional): The token expiration time. Defaults to None.
        user_id (int, optional): The user ID. Defaults to None.
        user_role (str, optional): The user role. Defaults to None.

    Returns:
        Tuple[str, float, str]: The encoded token, expiration timestamp, and token JTI
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Convert to timestamp
    expires_at = expire.timestamp()
    to_encode.update({"exp": expires_at})

    # Add user ID and role to the token payload
    if user_id is not None:
        to_encode.update({"user_id": user_id})
    if user_role is not None:
        to_encode.update({"user_role": user_role})

    # Add token type and JTI (JWT ID) for token revocation
    token_jti = str(uuid.uuid4())
    to_encode.update({
        "jti": token_jti,
        "token_type": "access"
    })

    # Add issued at time
    to_encode.update({"iat": datetime.utcnow().timestamp()})

    # Encode the token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt, expires_at, token_jti

def create_refresh_token(data: dict, user_id: int = None, user_role: str = None) -> Tuple[str, float, str]:
    """
    Create a refresh token.

    Args:
        data (dict): The data to encode in the token
        user_id (int, optional): The user ID. Defaults to None.
        user_role (str, optional): The user role. Defaults to None.

    Returns:
        Tuple[str, float, str]: The encoded token, expiration timestamp, and token JTI
    """
    to_encode = data.copy()

    # Set expiration time (longer than access token)
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    expires_at = expire.timestamp()
    to_encode.update({"exp": expires_at})

    # Add user ID and role to the token payload
    if user_id is not None:
        to_encode.update({"user_id": user_id})
    if user_role is not None:
        to_encode.update({"user_role": user_role})

    # Add token type and JTI (JWT ID) for token revocation
    token_jti = str(uuid.uuid4())
    to_encode.update({
        "jti": token_jti,
        "token_type": "refresh"
    })

    # Add issued at time
    to_encode.update({"iat": datetime.utcnow().timestamp()})

    # Encode the token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt, expires_at, token_jti

def create_csrf_token() -> str:
    """
    Create a CSRF token.

    Returns:
        str: The CSRF token
    """
    return str(uuid.uuid4())

async def get_current_user(request: Request, token: Optional[str] = Depends(get_token_from_header_or_cookie)):
    """
    Get the current user from the token.

    Args:
        request (Request): The request object
        token (Optional[str], optional): The token. Defaults to Depends(get_token_from_header_or_cookie).

    Returns:
        dict: The user object

    Raises:
        HTTPException: If the token is invalid or the user is not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        logger.warning("No token found in request")
        raise credentials_exception

    try:
        # Log token for debugging (first 10 chars only for security)
        token_preview = token[:10] + "..." if token and len(token) > 10 else "None"
        logger.debug(f"Validating token: {token_preview}")

        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Extract token data
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        user_role: str = payload.get("user_role")
        jti: str = payload.get("jti")
        token_type: str = payload.get("token_type")

        # Validate token data
        if username is None:
            logger.warning("Token missing 'sub' claim")
            raise credentials_exception

        if jti is None:
            logger.warning("Token missing 'jti' claim")
            raise credentials_exception

        if token_type is None or token_type != "access":
            logger.warning(f"Invalid token type: {token_type}")
            raise credentials_exception

        # Check if token is blacklisted
        if is_blacklisted(jti):
            logger.warning(f"Token {jti[:8]}... is blacklisted")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create token data object
        token_data = TokenData(
            username=username,
            user_id=user_id,
            user_role=user_role,
            jti=jti,
            token_type=token_type
        )

        logger.debug(f"Token decoded successfully for user: {username}")
    except JWTError as e:
        logger.error(f"JWT Error: {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Unexpected error decoding token: {str(e)}")
        raise credentials_exception

    # Get user from database
    user = get_user(username=token_data.username)
    if user is None:
        logger.warning(f"User not found: {token_data.username}")
        raise credentials_exception

    # Check if user is locked out
    if user.get("failed_login_attempts", 0) >= MAX_LOGIN_ATTEMPTS:
        # Check if lockout has expired
        lockout_time = user.get("lockout_time")
        if lockout_time:
            lockout_expiry = datetime.fromisoformat(lockout_time) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            if datetime.utcnow() < lockout_expiry:
                logger.warning(f"User {user['username']} is locked out until {lockout_expiry}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Account is locked due to too many failed login attempts. Try again after {lockout_expiry}",
                    headers={"WWW-Authenticate": "Bearer"},
                )

    # Add token data to user object for use in database connections
    user["token_user_id"] = token_data.user_id
    user["token_user_role"] = token_data.user_role
    user["token_jti"] = token_data.jti

    logger.info(f"Authentication successful for user: {user['username']} (ID: {user['id']}, Role: {user['role']})")
    return user

async def get_current_active_user(current_user = Depends(get_current_user)):
    if not current_user["is_active"]:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(current_user = Depends(get_current_active_user)):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Endpoints
@router.post("/token", response_model=Token)
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint that returns access and refresh tokens.

    Args:
        response (Response): The response object
        form_data (OAuth2PasswordRequestForm, optional): The login form data. Defaults to Depends().

    Returns:
        Token: The token response

    Raises:
        HTTPException: If authentication fails
    """
    logger.info(f"Login attempt for user: {form_data.username}")
    logger.debug(f"Password provided: {form_data.password[:2]}***")

    # Check if user exists
    user = get_user(form_data.username)
    if not user:
        logger.warning(f"User not found: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is locked out
    if user.get("failed_login_attempts", 0) >= MAX_LOGIN_ATTEMPTS:
        # Check if lockout has expired
        lockout_time = user.get("lockout_time")
        if lockout_time:
            lockout_expiry = datetime.fromisoformat(lockout_time) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            if datetime.utcnow() < lockout_expiry:
                logger.warning(f"User {user['username']} is locked out until {lockout_expiry}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Account is locked due to too many failed login attempts. Try again after {lockout_expiry}",
                    headers={"WWW-Authenticate": "Bearer"},
                )

    # Authenticate user
    if not verify_password(form_data.password, user["password_hash"]):
        logger.warning(f"Password verification failed for user: {form_data.username}")

        # Increment failed login attempts
        try:
            # Use a regular connection since this is for the users table, not subject to RLS
            with get_db_connection() as db_conn:
                if db_conn is None:
                    logger.error("Database connection not available")
                else:
                    cursor = db_conn.cursor()
                    try:
                        # Get current failed login attempts from database
                        cursor.execute("""
                            SELECT failed_login_attempts FROM users WHERE username = %s
                        """, (user["username"],))

                        result = cursor.fetchone()
                        if result:
                            current_attempts = result[0] or 0
                            failed_attempts = current_attempts + 1
                        else:
                            failed_attempts = 1

                        # Update failed login attempts
                        cursor.execute("""
                            UPDATE users
                            SET failed_login_attempts = %s,
                                lockout_time = CASE WHEN %s >= %s THEN now() ELSE lockout_time END
                            WHERE username = %s
                        """, (failed_attempts, failed_attempts, MAX_LOGIN_ATTEMPTS, user["username"]))

                        db_conn.commit()

                        logger.info(f"Updated failed login attempts for user {user['username']}: {failed_attempts}")

                        # Check if user is now locked out
                        if failed_attempts >= MAX_LOGIN_ATTEMPTS:
                            logger.warning(f"User {user['username']} is now locked out")
                    except Exception as column_error:
                        # If the column doesn't exist, log a warning but continue
                        if "column" in str(column_error) and "failed_login_attempts" in str(column_error):
                            logger.warning(f"failed_login_attempts column doesn't exist, skipping update: {column_error}")
                        else:
                            # Re-raise if it's a different error
                            logger.error(f"Error updating failed login attempts: {column_error}")
                    finally:
                        cursor.close()
        except Exception as e:
            logger.error(f"Error updating failed login attempts: {e}")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"Authentication successful for user: {form_data.username}")

    # Reset failed login attempts and update last login time
    try:
        # Use a regular connection since this is for the users table, not subject to RLS
        with get_db_connection() as db_conn:
            if db_conn is None:
                logger.error("Database connection not available")
            else:
                cursor = db_conn.cursor()
                try:
                    # Update last login time and reset failed login attempts
                    cursor.execute("""
                        UPDATE users
                        SET last_login = now(),
                            failed_login_attempts = 0,
                            lockout_time = NULL
                        WHERE username = %s
                    """, (user["username"],))

                    db_conn.commit()

                    logger.debug(f"Updated last login time and reset failed login attempts for user: {user['username']}")
                except Exception as column_error:
                    # If the column doesn't exist, just update the last_login time
                    if "column" in str(column_error) and "failed_login_attempts" in str(column_error):
                        logger.warning(f"failed_login_attempts column doesn't exist, updating only last_login: {column_error}")
                        cursor.execute("""
                            UPDATE users
                            SET last_login = now()
                            WHERE username = %s
                        """, (user["username"],))

                        db_conn.commit()

                        logger.debug(f"Updated last login time for user: {user['username']}")
                    else:
                        # Re-raise if it's a different error
                        logger.error(f"Error updating last login: {column_error}")
                finally:
                    cursor.close()
    except Exception as e:
        logger.error(f"Error updating last login: {e}")

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    logger.debug(f"Creating access token with user_id={user['id']}, role={user['role']}")
    access_token, access_token_expires_at, access_token_jti = create_access_token(
        data={"sub": user["username"]},
        expires_delta=access_token_expires,
        user_id=user["id"],
        user_role=user["role"]
    )

    # Create refresh token
    logger.debug(f"Creating refresh token with user_id={user['id']}, role={user['role']}")
    refresh_token, refresh_token_expires_at, refresh_token_jti = create_refresh_token(
        data={"sub": user["username"]},
        user_id=user["id"],
        user_role=user["role"]
    )

    # Create CSRF token
    csrf_token = create_csrf_token()

    # Log tokens for debugging (first 10 chars only for security)
    access_token_preview = access_token[:10] + "..." if access_token and len(access_token) > 10 else "None"
    refresh_token_preview = refresh_token[:10] + "..." if refresh_token and len(refresh_token) > 10 else "None"
    logger.debug(f"Access token created: {access_token_preview}")
    logger.debug(f"Refresh token created: {refresh_token_preview}")

    # Set the access token in an HTTP-only cookie
    access_cookie_expires = datetime.fromtimestamp(access_token_expires_at)
    access_token_max_age = int(access_token_expires.total_seconds())
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=access_token,
        httponly=True,
        secure=True,  # Requires HTTPS
        samesite="lax",  # Prevents CSRF
        expires=access_cookie_expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
        max_age=access_token_max_age,
        path="/"
    )

    # Set the refresh token in an HTTP-only cookie
    refresh_cookie_expires = datetime.fromtimestamp(refresh_token_expires_at)
    refresh_token_max_age = int((refresh_cookie_expires - datetime.utcnow()).total_seconds())
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=True,  # Requires HTTPS
        samesite="lax",  # Prevents CSRF
        expires=refresh_cookie_expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
        max_age=refresh_token_max_age,
        path="/"
    )

    # Set the CSRF token in a non-HTTP-only cookie
    response.set_cookie(
        key=CSRF_TOKEN_COOKIE,
        value=csrf_token,
        httponly=False,  # Not HTTP-only so JavaScript can read it
        secure=True,  # Requires HTTPS
        samesite="lax",  # Prevents CSRF
        expires=access_cookie_expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
        max_age=access_token_max_age,
        path="/"
    )

    logger.debug(f"Set HTTP-only cookies with tokens and CSRF token")

    # Remove password hash from response
    user_data = {k: v for k, v in user.items() if k != "password_hash"}

    logger.info(f"Login successful for user: {user['username']}")

    # Return tokens in the response
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_data,
        "expires_in": int(access_token_expires.total_seconds())
    }

@router.get("/signup-status", dependencies=[])
async def get_signup_status():
    """Check if signups are currently enabled (public endpoint, no authentication required)"""
    logger.debug("Checking signup status (public endpoint)")
    return {"signups_enabled": SIGNUPS_ENABLED}

@router.post("/check-password-strength", response_model=PasswordStrengthResponse)
async def check_password_strength(password: str):
    """
    Check password strength.

    Args:
        password (str): The password to check

    Returns:
        PasswordStrengthResponse: The password strength response
    """
    feedback = get_password_strength_feedback(password)
    return feedback

@router.get("/password-requirements")
async def get_password_requirements():
    """
    Get password requirements.

    Returns:
        Dict[str, Any]: The password requirements
    """
    requirements = get_password_requirements()
    return requirements

@router.post("/register", response_model=UserResponse, dependencies=[])
async def register_user(response: Response, user: UserCreate):
    """
    Register a new user (public endpoint, no authentication required).

    Args:
        response (Response): The response object
        user (UserCreate): The user registration data

    Returns:
        UserResponse: The new user data

    Raises:
        HTTPException: If registration fails
    """
    logger.info(f"Registration attempt for user: {user.username}")
    # Check if signups are enabled
    if not SIGNUPS_ENABLED:
        logger.warning(f"Registration attempt for user {user.username} when signups are disabled")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="New user registration is currently disabled"
        )

    # Check password strength
    is_strong, score, feedback = validate_password_strength(user.password)
    if not is_strong:
        logger.warning(f"Registration failed: Password not strong enough: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password not strong enough", "feedback": feedback}
        )

    # Check if username or email already exists
    try:
        # Use a secure database connection
        with get_secure_db() as db_conn:
            try:
                # Check if username already exists
                username_check = db_conn.execute_query("SELECT username FROM users WHERE username = %s", (user.username,))
                if username_check:
                    logger.warning(f"Registration attempt for user {user.username} with existing username")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Username '{user.username}' is already registered"
                    )

                # Check if email already exists
                email_check = db_conn.execute_query("SELECT email FROM users WHERE email = %s", (user.email,))
                if email_check:
                    logger.warning(f"Registration attempt with existing email {user.email}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email address is already registered"
                    )

                # Hash the password
                hashed_password = get_password_hash(user.password)

                # Insert new user
                db_conn.execute_command("""
                    INSERT INTO users (username, email, password_hash, full_name)
                    VALUES (%s, %s, %s, %s)
                """, (user.username, user.email, hashed_password, user.full_name))

                # Get the new user
                new_user_data = db_conn.execute_query("""
                    SELECT id, username, email, full_name, role, is_active, created_at, last_login, avatar_url
                    FROM users
                    WHERE username = %s
                """, (user.username,))

                if not new_user_data:
                    logger.error(f"Failed to create user: {user.username}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to create user"
                    )

                new_user = new_user_data[0]

                # Convert datetime objects to ISO format
                if "created_at" in new_user and new_user["created_at"]:
                    new_user["created_at"] = new_user["created_at"].isoformat()
                if "last_login" in new_user and new_user["last_login"]:
                    new_user["last_login"] = new_user["last_login"].isoformat()

                logger.info(f"User {user.username} registered successfully with ID {new_user['id']}")

                # Create access token
                access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token, access_token_expires_at, access_token_jti = create_access_token(
                    data={"sub": new_user["username"]},
                    expires_delta=access_token_expires,
                    user_id=new_user["id"],
                    user_role=new_user["role"]
                )

                # Create refresh token
                refresh_token, refresh_token_expires_at, refresh_token_jti = create_refresh_token(
                    data={"sub": new_user["username"]},
                    user_id=new_user["id"],
                    user_role=new_user["role"]
                )

                # Create CSRF token
                csrf_token = create_csrf_token()

                # Set the access token in an HTTP-only cookie
                access_cookie_expires = datetime.fromtimestamp(access_token_expires_at)
                response.set_cookie(
                    key=ACCESS_TOKEN_COOKIE,
                    value=access_token,
                    httponly=True,
                    secure=True,  # Requires HTTPS
                    samesite="lax",  # Prevents CSRF
                    expires=access_cookie_expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
                    max_age=int(access_token_expires.total_seconds()),
                    path="/"
                )

                # Set the refresh token in an HTTP-only cookie
                refresh_cookie_expires = datetime.fromtimestamp(refresh_token_expires_at)
                refresh_token_max_age = int((refresh_cookie_expires - datetime.utcnow()).total_seconds())
                response.set_cookie(
                    key=REFRESH_TOKEN_COOKIE,
                    value=refresh_token,
                    httponly=True,
                    secure=True,  # Requires HTTPS
                    samesite="lax",  # Prevents CSRF
                    expires=refresh_cookie_expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
                    max_age=refresh_token_max_age,
                    path="/"
                )

                # Set the CSRF token in a non-HTTP-only cookie
                response.set_cookie(
                    key=CSRF_TOKEN_COOKIE,
                    value=csrf_token,
                    httponly=False,  # Not HTTP-only so JavaScript can read it
                    secure=True,  # Requires HTTPS
                    samesite="lax",  # Prevents CSRF
                    expires=access_cookie_expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
                    max_age=int(access_token_expires.total_seconds()),
                    path="/"
                )

                return new_user
            except Exception as e:
                db_conn.rollback()
                logger.error(f"Error registering user: {e}")
                if isinstance(e, HTTPException):
                    raise e

                # Check for specific database errors
                error_str = str(e)
                if "duplicate key" in error_str and "users_pkey" in error_str:
                    logger.error(f"Duplicate primary key error: {error_str}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Database sequence error. Please try again."
                    )
                elif "duplicate key" in error_str and "users_username_key" in error_str:
                    logger.error(f"Duplicate username error: {error_str}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Username '{user.username}' is already registered"
                    )
                elif "duplicate key" in error_str and "users_email_key" in error_str:
                    logger.error(f"Duplicate email error: {error_str}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email address is already registered"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error registering user"
                    )
    except Exception as e:
        logger.error(f"Error with database connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error"
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user = Depends(get_current_active_user)):
    # Remove password hash from response
    user_data = {k: v for k, v in current_user.items() if k != "password_hash"}
    return user_data



@router.post("/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    request: Request,
    refresh_token: Optional[str] = Depends(get_refresh_token_from_cookie),
    refresh_request: Optional[RefreshTokenRequest] = None
):
    """
    Refresh access token using a refresh token.

    Args:
        response (Response): The response object
        request (Request): The request object
        refresh_token (Optional[str], optional): The refresh token from cookie. Defaults to Depends(get_refresh_token_from_cookie).
        refresh_request (Optional[RefreshTokenRequest], optional): The refresh token request body. Defaults to None.

    Returns:
        Token: The new token response

    Raises:
        HTTPException: If the refresh token is invalid
    """
    # Get refresh token from cookie or request body
    if not refresh_token and refresh_request and refresh_request.refresh_token:
        refresh_token = refresh_request.refresh_token

    if not refresh_token:
        logger.warning("No refresh token found in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Log token for debugging (first 10 chars only for security)
    token_preview = refresh_token[:10] + "..." if refresh_token and len(refresh_token) > 10 else "None"
    logger.debug(f"Refreshing token: {token_preview}")

    try:
        # Decode the refresh token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

        # Extract token data
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        user_role: str = payload.get("user_role")
        jti: str = payload.get("jti")
        token_type: str = payload.get("token_type")

        # Validate token data
        if username is None:
            logger.warning("Refresh token missing 'sub' claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if jti is None:
            logger.warning("Refresh token missing 'jti' claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if token_type is None or token_type != "refresh":
            logger.warning(f"Invalid token type: {token_type}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if token is blacklisted
        if is_blacklisted(jti):
            logger.warning(f"Refresh token {jti[:8]}... is blacklisted")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user from database
        user = get_user(username=username)
        if user is None:
            logger.warning(f"User not found: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is active
        if not user["is_active"]:
            logger.warning(f"User {username} is inactive")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        logger.debug(f"Creating new access token with user_id={user_id}, role={user_role}")
        access_token, access_token_expires_at, access_token_jti = create_access_token(
            data={"sub": username},
            expires_delta=access_token_expires,
            user_id=user_id,
            user_role=user_role
        )

        # Create new CSRF token
        csrf_token = create_csrf_token()

        # Log token for debugging (first 10 chars only for security)
        access_token_preview = access_token[:10] + "..." if access_token and len(access_token) > 10 else "None"
        logger.debug(f"New access token created: {access_token_preview}")

        # Set the access token in an HTTP-only cookie
        access_cookie_expires = datetime.fromtimestamp(access_token_expires_at)
        access_token_max_age = int(access_token_expires.total_seconds())
        response.set_cookie(
            key=ACCESS_TOKEN_COOKIE,
            value=access_token,
            httponly=True,
            secure=True,  # Requires HTTPS
            samesite="lax",  # Prevents CSRF
            expires=access_cookie_expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
            max_age=access_token_max_age,
            path="/"
        )

        # Set the CSRF token in a non-HTTP-only cookie
        response.set_cookie(
            key=CSRF_TOKEN_COOKIE,
            value=csrf_token,
            httponly=False,  # Not HTTP-only so JavaScript can read it
            secure=True,  # Requires HTTPS
            samesite="lax",  # Prevents CSRF
            expires=access_cookie_expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
            max_age=access_token_max_age,
            path="/"
        )

        logger.debug(f"Set HTTP-only cookie with new access token and CSRF token")

        # Remove password hash from response
        user_data = {k: v for k, v in user.items() if k != "password_hash"}

        logger.info(f"Token refresh successful for user: {username}")

        # Return tokens in the response
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,  # Return the same refresh token
            "token_type": "bearer",
            "user": user_data,
            "expires_in": int(access_token_expires.total_seconds())
        }
    except JWTError as e:
        logger.error(f"JWT Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error refreshing token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error refreshing token",
        )

@router.post("/revoke")
async def revoke_token(
    request: Request,
    current_user = Depends(get_current_active_user),
    csrf_valid: bool = Depends(validate_csrf_token)
):
    """
    Revoke the current token.

    Args:
        request (Request): The request object
        current_user: The current user
        csrf_valid (bool): Whether the CSRF token is valid

    Returns:
        dict: A message indicating the token was revoked

    Raises:
        HTTPException: If the CSRF token is invalid or the token cannot be revoked
    """
    # Check CSRF token
    if not csrf_valid:
        logger.warning("Invalid CSRF token")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )

    # Get token JTI
    token_jti = current_user.get("token_jti")
    if not token_jti:
        logger.warning("No token JTI found in user object")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No token to revoke",
        )

    # Add token to blacklist
    try:
        # Get token expiration from user object or use a default
        token_exp = current_user.get("token_exp", time.time() + 3600)  # Default to 1 hour from now

        # Add token to blacklist
        success = add_to_blacklist(token_jti, token_exp)
        if not success:
            logger.error(f"Failed to add token {token_jti[:8]}... to blacklist")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke token",
            )

        logger.info(f"Token {token_jti[:8]}... revoked for user {current_user['username']}")
        return {"message": "Token revoked successfully"}
    except Exception as e:
        logger.error(f"Error revoking token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error revoking token",
        )

@router.post("/logout")
async def logout(
    response: Response,
    request: Request,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    csrf_valid: bool = Depends(validate_csrf_token)
):
    """
    Logout user by revoking tokens and clearing cookies.

    Args:
        response (Response): The response object
        request (Request): The request object
        current_user (Optional[Dict[str, Any]], optional): The current user. Defaults to Depends(get_current_user).
        csrf_valid (bool, optional): Whether the CSRF token is valid. Defaults to Depends(validate_csrf_token).

    Returns:
        dict: A message indicating the user was logged out
    """
    # Check CSRF token if user is authenticated
    if current_user and not csrf_valid:
        logger.warning("Invalid CSRF token during logout")
        # Continue with logout anyway for security reasons

    # Revoke token if user is authenticated
    if current_user and "token_jti" in current_user:
        try:
            # Get token expiration from user object or use a default
            token_exp = current_user.get("token_exp", time.time() + 3600)  # Default to 1 hour from now

            # Add token to blacklist
            add_to_blacklist(current_user["token_jti"], token_exp)
            logger.info(f"Token {current_user['token_jti'][:8]}... revoked during logout")
        except Exception as e:
            logger.error(f"Error revoking token during logout: {e}")
            # Continue with logout anyway for security reasons

    # Clear cookies
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE,
        path="/",
        secure=True,
        httponly=True,
        samesite="lax"
    )

    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE,
        path="/",
        secure=True,
        httponly=True,
        samesite="lax"
    )

    response.delete_cookie(
        key=CSRF_TOKEN_COOKIE,
        path="/",
        secure=True,
        httponly=False,
        samesite="lax"
    )

    logger.info(f"User logged out successfully")
    return {"message": "Logged out successfully"}

@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user = Depends(get_current_active_user),
    csrf_valid: bool = Depends(validate_csrf_token)
):
    """
    Change user password.

    Args:
        old_password (str): The old password
        new_password (str): The new password
        current_user: The current user
        csrf_valid (bool): Whether the CSRF token is valid

    Returns:
        dict: A message indicating the password was changed

    Raises:
        HTTPException: If the password change fails
    """
    logger.info(f"Password change attempt for user: {current_user['username']}")

    # Check CSRF token
    if not csrf_valid:
        logger.warning("Invalid CSRF token during password change")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )

    # Verify old password
    if not verify_password(old_password, current_user["password_hash"]):
        logger.warning(f"Password change failed for user {current_user['username']}: incorrect old password")

        # Increment failed login attempts
        try:
            with get_secure_db() as db:
                # Get current failed login attempts
                failed_attempts = current_user.get("failed_login_attempts", 0) + 1

                # Update failed login attempts
                try:
                    db.execute_command("""
                        UPDATE users
                        SET failed_login_attempts = %s,
                            lockout_time = CASE WHEN %s >= %s THEN now() ELSE lockout_time END
                        WHERE id = %s
                    """, (failed_attempts, failed_attempts, MAX_LOGIN_ATTEMPTS, current_user["id"]))

                    logger.info(f"Updated failed login attempts for user {current_user['username']}: {failed_attempts}")

                    # Check if user is now locked out
                    if failed_attempts >= MAX_LOGIN_ATTEMPTS:
                        logger.warning(f"User {current_user['username']} is now locked out")
                except Exception as column_error:
                    # If the column doesn't exist, log a warning but continue
                    if "column" in str(column_error) and "failed_login_attempts" in str(column_error):
                        logger.warning(f"failed_login_attempts column doesn't exist, skipping update: {column_error}")
                    else:
                        # Re-raise if it's a different error
                        raise column_error
        except Exception as e:
            logger.error(f"Error updating failed login attempts: {e}")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )

    # Check password strength
    is_strong, score, feedback = validate_password_strength(new_password)
    if not is_strong:
        logger.warning(f"Password change failed for user {current_user['username']}: password not strong enough")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password not strong enough", "feedback": feedback}
        )

    # Hash new password
    hashed_password = get_password_hash(new_password)

    # Update password
    try:
        with get_secure_db() as db:
            # Update password and reset failed login attempts
            try:
                db.execute_command("""
                    UPDATE users
                    SET password_hash = %s,
                        failed_login_attempts = 0,
                        lockout_time = NULL
                    WHERE id = %s
                """, (hashed_password, current_user["id"]))
            except Exception as column_error:
                # If the column doesn't exist, just update the password
                if "column" in str(column_error) and "failed_login_attempts" in str(column_error):
                    logger.warning(f"failed_login_attempts column doesn't exist, updating only password: {column_error}")
                    db.execute_command("""
                        UPDATE users
                        SET password_hash = %s
                        WHERE id = %s
                    """, (hashed_password, current_user["id"]))
                else:
                    # Re-raise if it's a different error
                    raise column_error

            logger.info(f"Password changed successfully for user: {current_user['username']}")

            # Revoke all tokens for this user
            # This is a security measure to ensure that all sessions are invalidated when the password is changed
            try:
                # Get all active tokens for this user
                # This is a simplified implementation that doesn't actually revoke all tokens
                # In a production environment, you would need to store tokens in a database and revoke them there

                # Revoke the current token
                if "token_jti" in current_user:
                    token_exp = current_user.get("token_exp", time.time() + 3600)  # Default to 1 hour from now
                    add_to_blacklist(current_user["token_jti"], token_exp)
                    logger.info(f"Token {current_user['token_jti'][:8]}... revoked during password change")
            except Exception as e:
                logger.error(f"Error revoking tokens during password change: {e}")

            return {"message": "Password updated successfully"}
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error changing password"
        )
