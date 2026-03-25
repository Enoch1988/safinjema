# database.py – Async SQLite with aiosqlite + databases
import os, re, datetime, hashlib, secrets
import aiosqlite
from pathlib import Path
from config import settings

DB_PATH = Path("data/safinjema.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── Schema SQL ────────────────────────────────────────────────
SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    email       TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    phone       TEXT,
    password    TEXT    NOT NULL,
    role        TEXT    NOT NULL DEFAULT 'customer',
    verified    INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS bookings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_ref  TEXT    NOT NULL UNIQUE,
    user_id      INTEGER REFERENCES users(id) ON DELETE SET NULL,
    name         TEXT    NOT NULL,
    email        TEXT    NOT NULL COLLATE NOCASE,
    phone        TEXT    NOT NULL,
    service      TEXT    NOT NULL,
    date         TEXT    NOT NULL,
    time         TEXT    NOT NULL,
    area         TEXT,
    notes        TEXT,
    status       TEXT    NOT NULL DEFAULT 'pending',
    assigned_to  TEXT,
    price        REAL,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    email      TEXT NOT NULL,
    phone      TEXT,
    service    TEXT,
    message    TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'unread',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS quotes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER REFERENCES users(id) ON DELETE SET NULL,
    name            TEXT NOT NULL,
    email           TEXT NOT NULL,
    phone           TEXT,
    service         TEXT NOT NULL,
    property_type   TEXT,
    size_sqm        REAL,
    frequency       TEXT,
    notes           TEXT,
    estimated_price REAL,
    status          TEXT NOT NULL DEFAULT 'pending',
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS reset_tokens (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token      TEXT    NOT NULL UNIQUE,
    expires_at TEXT    NOT NULL,
    used       INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS audit_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    actor      TEXT,
    action     TEXT NOT NULL,
    entity     TEXT,
    entity_id  TEXT,
    detail     TEXT,
    ip         TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_bookings_email  ON bookings(email);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);
CREATE INDEX IF NOT EXISTS idx_bookings_date   ON bookings(date);
CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status);
CREATE INDEX IF NOT EXISTS idx_users_email     ON users(email);
"""

# ── Async DB connection ───────────────────────────────────────
_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DB_PATH)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA foreign_keys=ON")
    return _db


async def init_db():
    """Create tables and seed the default admin user."""
    from passlib.context import CryptContext
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

    db = await get_db()
    # Execute schema statements one by one
    for stmt in SCHEMA.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            await db.execute(stmt)
    await db.commit()

    # Seed admin if not exists
    async with db.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1") as cur:
        admin = await cur.fetchone()
    if not admin:
        hashed = pwd_ctx.hash(settings.ADMIN_PASSWORD)
        await db.execute(
            "INSERT INTO users (name, email, phone, password, role, verified) VALUES (?,?,?,?,?,?)",
            (settings.ADMIN_NAME, settings.ADMIN_EMAIL.lower(), "+27713599995", hashed, "admin", 1),
        )
        await db.commit()
        print("✅  Default admin user created.")


async def close_db():
    global _db
    if _db:
        await _db.close()
        _db = None


# ── Helpers ───────────────────────────────────────────────────

def generate_booking_ref(count: int) -> str:
    """Generate SN-YYYYMMDD-NNNN style reference."""
    date_str = datetime.date.today().strftime("%Y%m%d")
    return f"SN-{date_str}-{str(count).zfill(4)}"


async def next_booking_ref() -> str:
    db = await get_db()
    async with db.execute("SELECT COUNT(*) as c FROM bookings") as cur:
        row = await cur.fetchone()
    return generate_booking_ref((row["c"] or 0) + 1)


async def audit(actor: str, action: str, entity: str = None,
                entity_id=None, detail: str = None, ip: str = None):
    db = await get_db()
    await db.execute(
        "INSERT INTO audit_log (actor, action, entity, entity_id, detail, ip) VALUES (?,?,?,?,?,?)",
        (actor, action, entity, str(entity_id) if entity_id else None, detail, ip),
    )
    await db.commit()
