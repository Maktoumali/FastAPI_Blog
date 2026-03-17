from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import engine, Base
from routers import users, blogs

# Create uploads directory if it doesn't exist
if not os.path.exists("uploads/profile_photos"):
    os.makedirs("uploads/profile_photos", exist_ok=True)

# ─── Create Tables ────────────────────────────────────────────



# ─── App ──────────────────────────────────────────────────────

app = FastAPI()


# ─── CORS (allow all origins for development) ────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────

app.include_router(users.router)
app.include_router(blogs.router)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

