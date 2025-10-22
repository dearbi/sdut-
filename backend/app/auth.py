from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import List
from fastapi.security import OAuth2PasswordBearer

from .db import SessionLocal
from .models import User, Role, Department, UserRole
from .schemas import UserCreate, LoginRequest, Token, UserOut

SECRET_KEY = "change_this_in_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/auth/login")
router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])

# Dependency

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Utils

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Minimum role enforcement decorator

def require_roles(required: List[str]):
    def dependency(user: User = Depends(get_current_user)):
        user_roles = {r.name for r in user.roles}
        if not set(required).intersection(user_roles):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency

@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # If no users exist, allow first admin creation automatically
    existing_user = db.query(User).filter(User.username == user_in.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    user_count = db.query(User).count()
    hashed = get_password_hash(user_in.password)
    user = User(username=user_in.username, email=user_in.email, hashed_password=hashed, department_id=user_in.department_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    # Assign admin role for first user
    if user_count == 0:
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            admin_role = Role(name="admin")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
        db.add(UserRole(user_id=user.id, role_id=admin_role.id))
        db.commit()
    roles = [r.name for r in user.roles]
    return UserOut(id=user.id, username=user.username, email=user.email, is_active=user.is_active, department_id=user.department_id, roles=roles)

@router.post("/login", response_model=Token)
def login(login_in: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_in.username).first()
    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token({"sub": str(user.id), "roles": [r.name for r in user.roles]})
    return Token(access_token=token)