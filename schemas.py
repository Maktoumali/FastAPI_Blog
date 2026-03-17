from datetime import datetime
from typing import Optional,List
from pydantic import BaseModel, EmailStr, Field


# ─── User Schemas ─────────────────────────────────────────────


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=6)
    profile_photo: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    profile_photo: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuthorResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


# ─── Token Schemas ────────────────────────────────────────────


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


# ─── Blog Schemas ─────────────────────────────────────────────


class BlogCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)


class BlogUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)


class ImageResponse(BaseModel):
    id: int
    url: str

    class Config:
        from_attributes = True


class BlogAuthor(BaseModel):
    id: int
    username: str
    profile_photo: Optional[str] = None

    class Config:
        from_attributes = True


class BlogResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    author: BlogAuthor
    images: List[ImageResponse] = []
    comments: List["CommentResponse"] = []
    like_count: int = 0

    class Config:
        from_attributes = True

class CommentAuthor(BaseModel):
    id: int
    username: str
    profile_photo: Optional[str] = None

    class Config:
        from_attributes = True

class CommentResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    is_approved: Optional[bool]
    time_ago: Optional[str] = None
    author: CommentAuthor

    class Config:
        from_attributes = True

class LikeResponse(BaseModel):
    id: int
    user_id: int
    blog_id: int
    created_at: datetime

    class Config:
        from_attributes = True

BlogResponse.model_rebuild()

class BlogFilter(BaseModel):
    search: Optional[str] = None
    author_id: Optional[int] = None
    page: Optional[int] = 1
    per_page: Optional[int] = 10

class PaginationMeta(BaseModel):
    page: int
    per_page: int
    total_count: int
    total_pages: int
    has_next: bool
    has_prev: bool

class BlogListResponse(BaseModel):
    items: List[BlogResponse]
    pagination: PaginationMeta
