from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy.sql import func
from sqlalchemy import Boolean

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    profile_photo = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    comments = relationship("Comment", back_populates="author", cascade="all, delete")

    blogs = relationship("Blog", back_populates="author", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Blog(Base):
    __tablename__ = "blogs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    author = relationship("User", back_populates="blogs")
    images = relationship("Image", back_populates="blog", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="blog", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="blog", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Blog(id={self.id}, title='{self.title}')>"


class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    blacklisted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<BlacklistedToken(id={self.id}, token='{self.token[:20]}...')>"


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(255), nullable=False)
    blog_id = Column(Integer, ForeignKey("blogs.id"), nullable=False)

    blog = relationship("Blog", back_populates="images")

    def __repr__(self):
        return f"<Image(id={self.id}, url='{self.url}')>"

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
       default=lambda: datetime.now(timezone.utc),
       onupdate=lambda: datetime.now(timezone.utc)
    )
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    blog_id = Column(Integer, ForeignKey("blogs.id"), nullable=False)
    is_approved = Column(Boolean, default=False, nullable=True)

    author = relationship("User", back_populates="comments")
    blog = relationship("Blog", back_populates="comments")

    def __repr__(self):
        return f"<Comment(id={self.id}, content='{self.content}')>"

class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    blog_id = Column(Integer, ForeignKey("blogs.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint('user_id', 'blog_id', name='_user_blog_like_uc'),)

    blog = relationship("Blog", back_populates="likes")

    def __repr__(self):
        return f"<Like(id={self.id}, user_id={self.user_id}, blog_id={self.blog_id})>"
