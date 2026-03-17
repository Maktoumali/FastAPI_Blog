from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os
import uuid
import shutil
from typing import Optional, Annotated, List

from auth import hash_password, verify_password, create_access_token, get_current_user, bearer_scheme
from database import get_db
from models import User, BlacklistedToken
from schemas import UserCreate, UserLogin, UserResponse, Token, AuthorResponse

router = APIRouter(prefix="/users", tags=["Users"])

UPLOAD_DIR = "uploads/profile_photos"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    username: Annotated[str, Form(description="Enter a unique username")],
    email: Annotated[str, Form(description="Enter a valid email address")],
    password: Annotated[str, Form(description="Enter a secure password")],
    profile_photo: Annotated[Optional[UploadFile], File(description="Upload an optional profile photo")] = None,
    db: Session = Depends(get_db)
):
    """Create a new user account with an optional profile photo."""
    # Check if username already exists
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Check if email already exists
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    photo_path = None
    if profile_photo:
        # Create unique filename
        file_extension = os.path.splitext(profile_photo.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        photo_path = f"{UPLOAD_DIR}/{unique_filename}"
        
        # Save file
        with open(photo_path, "wb") as buffer:
            shutil.copyfileobj(profile_photo.file, buffer)
        
    
        photo_path = f"/uploads/profile_photos/{unique_filename}"

    new_user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        profile_photo=photo_path,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
   



@router.post("/login", response_model=Token)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db),
):
    """Authenticate with username & password and receive a JWT access token."""
    user = db.query(User).filter(User.username == login_data.username).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


# ─── Current User Profile ────────────────────────────────────


@router.get("/userprofile", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get the profile of the currently authenticated user."""
    return current_user


@router.get("/authors", response_model=List[AuthorResponse])
def list_authors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve a list of all authors (users). Requires authentication."""
    authors = db.query(User).all()
    return authors


# ─── Logout ───────────────────────────────────────────────────


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Invalidate the current token by blacklisting it.
    Requires authentication.
    """
    token = credentials.credentials
    # Check if already blacklisted
    exists = db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first()
    if not exists:
        new_blacklist = BlacklistedToken(token=token)
        db.add(new_blacklist)
        db.commit()
    return {"message": "Logout successful"}
