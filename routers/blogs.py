from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from typing import List, Optional
from auth import get_current_user
from datetime import datetime, timezone
from database import get_db
from models import Blog, User, Image, Comment, Like
from schemas import BlogResponse, BlogFilter, BlogListResponse, CommentResponse, LikeResponse
from utils import apply_dynamic_filters, build_pagination_meta, save_upload_file, delete_file, format_relative_time
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form

router = APIRouter(prefix="/blogs", tags=["Blogs"])



@router.get("/list", response_model=BlogListResponse)
def list_blogs(
    db: Session = Depends(get_db),
    filters: BlogFilter = Depends()
):
    """List all blog posts with search and filtering. No authentication required."""
    
    page = filters.page or 1
    per_page = filters.per_page or 10

    query = db.query(Blog)
    
    # Author filter
    filter_map = {
        "author_id": Blog.author_id,
    }
    query = apply_dynamic_filters(query, Blog, filters, filter_map)

    # Search filter
    if filters.search:
        search_attr = f"%{filters.search}%"
        query = query.filter(
            or_(
                Blog.title.ilike(search_attr)
            )
        )

    from sqlalchemy import func
    query = query.outerjoin(Like).group_by(Blog.id).add_columns(func.count(Like.id).label("like_count"))

    qs_count = query.count()
    
    results = (
        query.options(selectinload(Blog.author), selectinload(Blog.images))
        .order_by(Blog.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    items = []
    for blog, like_count in results:
        blog.like_count = like_count
        items.append(blog)

    return {
        "items": items,
        "pagination": build_pagination_meta(
            page,
            per_page,
            qs_count
        )
    }

@router.get("/{blog_id}", response_model=BlogResponse)
def get_blog(blog_id: int, db: Session = Depends(get_db)):
    """View a single blog post. No authentication required."""
    
    blog = (
        db.query(Blog)
        .options(
            selectinload(Blog.author),
            selectinload(Blog.images),
            selectinload(Blog.comments).selectinload(Comment.author)
        )
        .filter(Blog.id == blog_id)
        .first()
    )

    if not blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found",
        )

    blog.like_count = db.query(Like).filter(Like.blog_id == blog_id).count()

    return blog

from fastapi import Request

@router.post("/", response_model=BlogResponse, status_code=status.HTTP_201_CREATED)
async def create_blog(
    request:Request,
    title: str = Form(..., min_length=1, max_length=200),
    content: str = Form(..., min_length=1),
    images: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    form_data = await request.form()

    print("FULL PAYLOAD:", form_data)
    """Create a new blog post. Requires authentication. Supports multiple image uploads."""
    # Create blog
    new_blog = Blog(
        title=title,
        content=content,
        author_id=current_user.id,
    )
    db.add(new_blog)
    db.flush()
    print(request)  # Get the blog ID before committing
    print("hi",images)
    print(title)
    # Save images if provided
    if images:
        for image_file in images:
            if image_file.filename:  # Ensure there's a file
                image_url = save_upload_file(image_file)
                new_image = Image(url=image_url, blog_id=new_blog.id)
                db.add(new_image)
                
                
                
    
    db.commit()
    db.refresh(new_blog)
    return new_blog


@router.put("/{blog_id}", response_model=BlogResponse)
def update_blog(
    blog_id: int,
    title: Optional[str] = Form(None, min_length=1, max_length=200),
    content: Optional[str] = Form(None, min_length=1),
    images: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a blog post. Authors can update text and add new images."""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found",
        )

    if blog.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own posts",
        )

    if title is not None:
        blog.title = title
    if content is not None:
        blog.content = content

    # Add new images if provided
    if images:
        for image_file in images:
            if image_file.filename:
                image_url = save_upload_file(image_file)
                new_image = Image(url=image_url, blog_id=blog.id)
                db.add(new_image)

    db.commit()
    db.refresh(blog)
    return blog


@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a blog post. Only the author can delete their own post."""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found",
        )

    if blog.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own posts",
        )

    # Delete associated image files from disk
    for image in blog.images:
        delete_file(image.url)

    db.delete(blog)
    db.commit()
    return None


@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a specific image from a blog post."""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    # Check if the user is the author of the blog post
    blog = db.query(Blog).filter(Blog.id == image.blog_id).first()
    if blog.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete images from your own posts",
        )

    # Delete file from disk
    delete_file(image.url)

    # Delete from database
    db.delete(image)
    db.commit()
    return None

@router.post("/{blog_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    blog_id: int,
    content: str = Form(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    comment = Comment(
        content=content,
        blog_id=blog_id,
        author_id=current_user.id,
        created_at=datetime.now(timezone.utc),
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return comment


@router.get("/{blog_id}/comments", response_model=List[CommentResponse])
def get_comments(
    blog_id: int,
    db: Session = Depends(get_db),
):
    """Get comments for a specific blog post. Returns comment, author info, and timestamps."""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    comments = (
        db.query(Comment)
        .options(selectinload(Comment.author))
        .filter(Comment.blog_id == blog_id)
        .order_by(Comment.created_at.desc())
        .all()
    )

    # Annotate each comment with a short relative time string for UI
    for c in comments:
        try:
            c.time_ago = format_relative_time(c.created_at)
        except Exception:
            c.time_ago = ""

    return comments


@router.post("/{blog_id}/toggle-like", status_code=status.HTTP_200_OK)
def toggle_like(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Toggle a like on a blog post for the current user."""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    existing_like = db.query(Like).filter(
        Like.blog_id == blog_id,
        Like.user_id == current_user.id
    ).first()

    if existing_like:
        db.delete(existing_like)
        message = "Like removed"
    else:
        new_like = Like(blog_id=blog_id, user_id=current_user.id)
        db.add(new_like)
        message = "Blog liked"

    db.commit()
    
    like_count = db.query(Like).filter(Like.blog_id == blog_id).count()
    
    return {"message": message, "like_count": like_count}

