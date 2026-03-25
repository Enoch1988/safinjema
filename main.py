"""
╔══════════════════════════════════════════════════════╗
║  SaFi Njema Cleaning Services – Python Backend API  ║
║  FastAPI + SQLite (aiosqlite) + JWT + SMTP           ║
║  Run:  uvicorn main:app --reload --port 8000         ║
╚══════════════════════════════════════════════════════╝
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from config import settings
from database import close_db, init_db
from routes import admin, auth, bookings, contact, quotes

# ── Rate limiter ──────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["100/15minutes"])


# ── Lifespan (startup / shutdown) ────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n🌿  SaFi Njema Backend starting up…")
    await init_db()
    print(f"📡  Listening on http://{settings.HOST}:{settings.PORT}")
    print(f"📖  API docs:  http://localhost:{settings.PORT}/docs\n")
    yield
    await close_db()
    print("👋  SaFi Njema Backend shut down.")


# ── FastAPI app ───────────────────────────────────────────────
app = FastAPI(
    title="SaFi Njema Cleaning Services API",
    description="Backend API for SaFi Njema eco-friendly cleaning services — Cape Town.",
    version="1.0.0",
    contact={"name": "SaFi Njema", "email": "safinjema@outlook.com"},
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Rate limiting ─────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include routers ───────────────────────────────────────────
app.include_router(auth.router)
app.include_router(bookings.router)
app.include_router(contact.router)
app.include_router(quotes.router)
app.include_router(admin.router)

# ── Static frontend files ─────────────────────────────────────
PUBLIC_DIR = Path("public")
if PUBLIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=PUBLIC_DIR), name="static")


# ── Health check ──────────────────────────────────────────────
@app.get("/api/health", tags=["System"])
async def health():
    return {
        "success": True,
        "service": "SaFi Njema Backend API",
        "version": "1.0.0",
        "status":  "running",
        "framework": "FastAPI + Python",
    }


# ── Root API map ──────────────────────────────────────────────
@app.get("/api", tags=["System"])
async def api_map():
    return {
        "success": True,
        "message": "SaFi Njema Cleaning Services — Backend API v1.0.0",
        "docs": f"http://localhost:{settings.PORT}/docs",
        "endpoints": {
            "auth": {
                "register":        "POST /api/auth/register",
                "login":           "POST /api/auth/login",
                "me":              "GET  /api/auth/me  🔒",
                "profile":         "PUT  /api/auth/profile  🔒",
                "change_password": "PUT  /api/auth/change-password  🔒",
                "forgot_password": "POST /api/auth/forgot-password",
                "reset_password":  "POST /api/auth/reset-password",
            },
            "bookings": {
                "create": "POST /api/bookings",
                "my":     "GET  /api/bookings/my  🔒",
                "get":    "GET  /api/bookings/{ref}  🔒",
                "cancel": "PUT  /api/bookings/{ref}/cancel  🔒",
            },
            "contact": {"send": "POST /api/contact"},
            "quotes": {
                "services":  "GET  /api/quotes/services",
                "service":   "GET  /api/quotes/services/{id}",
                "estimate":  "GET  /api/quotes/estimate/{id}",
                "submit":    "POST /api/quotes",
                "my_quotes": "GET  /api/quotes/my  🔒",
            },
            "admin": {
                "dashboard":      "GET    /api/admin/dashboard  🔒👑",
                "bookings":       "GET    /api/admin/bookings  🔒👑",
                "update_booking": "PUT    /api/admin/bookings/{id}  🔒👑",
                "delete_booking": "DELETE /api/admin/bookings/{id}  🔒👑",
                "messages":       "GET    /api/admin/messages  🔒👑",
                "users":          "GET    /api/admin/users  🔒👑",
                "audit_log":      "GET    /api/admin/audit  🔒👑",
                "quotes":         "GET    /api/admin/quotes  🔒👑",
            },
        },
        "legend": {"🔒": "requires JWT Bearer token", "👑": "admin role required"},
    }


# ── Global error handler ──────────────────────────────────────
@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    if settings.DEBUG:
        raise exc
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error."},
    )


# ── SPA fallback – serve index.html for unknown routes ────────
@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    index = PUBLIC_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse(
        status_code=404,
        content={"success": False, "message": "Not found."},
    )


# ── Dev server ────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
