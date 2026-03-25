# routes/admin.py – Admin-only management endpoints
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from database import audit, get_db
from middleware.auth import require_admin
from mailer import send_booking_status

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# All routes require admin role via dependency
AdminDep = Depends(require_admin)


# ══════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════
@router.get("/dashboard")
async def dashboard(admin=AdminDep):
    db = await get_db()

    async def count(sql, *args):
        async with db.execute(sql, args) as c:
            return (await c.fetchone())[0]

    total_bookings    = await count("SELECT COUNT(*) FROM bookings")
    pending           = await count("SELECT COUNT(*) FROM bookings WHERE status='pending'")
    confirmed         = await count("SELECT COUNT(*) FROM bookings WHERE status='confirmed'")
    completed         = await count("SELECT COUNT(*) FROM bookings WHERE status='completed'")
    cancelled         = await count("SELECT COUNT(*) FROM bookings WHERE status='cancelled'")
    total_users       = await count("SELECT COUNT(*) FROM users WHERE role='customer'")
    total_messages    = await count("SELECT COUNT(*) FROM messages")
    unread_messages   = await count("SELECT COUNT(*) FROM messages WHERE status='unread'")

    async with db.execute(
        "SELECT COALESCE(SUM(price),0) FROM bookings WHERE status='completed' AND price IS NOT NULL"
    ) as c:
        revenue = (await c.fetchone())[0]

    async with db.execute(
        "SELECT service, COUNT(*) as cnt FROM bookings GROUP BY service ORDER BY cnt DESC LIMIT 5"
    ) as c:
        by_service = [dict(r) for r in await c.fetchall()]

    async with db.execute("""
        SELECT date(created_at) as day, COUNT(*) as count FROM bookings
        WHERE created_at >= date('now', '-6 days')
        GROUP BY day ORDER BY day
    """) as c:
        last_7_days = [dict(r) for r in await c.fetchall()]

    async with db.execute(
        "SELECT booking_ref, name, service, date, time, status, created_at FROM bookings ORDER BY created_at DESC LIMIT 10"
    ) as c:
        recent = [dict(r) for r in await c.fetchall()]

    async with db.execute("""
        SELECT booking_ref, name, phone, service, date, time, area, status
        FROM bookings
        WHERE date >= date('now') AND date <= date('now','+7 days')
        AND status IN ('pending','confirmed')
        ORDER BY date, time
    """) as c:
        upcoming = [dict(r) for r in await c.fetchall()]

    return {
        "success": True,
        "stats": {
            "bookings": {"total": total_bookings, "pending": pending,
                         "confirmed": confirmed, "completed": completed,
                         "cancelled": cancelled},
            "customers": total_users,
            "messages":  {"total": total_messages, "unread": unread_messages},
            "revenue":   revenue,
        },
        "by_service":       by_service,
        "last_7_days":      last_7_days,
        "recent_bookings":  recent,
        "upcoming_bookings": upcoming,
    }


# ══════════════════════════════════════════
# BOOKINGS
# ══════════════════════════════════════════
@router.get("/bookings")
async def list_bookings(
    status:  Optional[str] = None,
    service: Optional[str] = None,
    date:    Optional[str] = None,
    search:  Optional[str] = None,
    page:    int = 1,
    limit:   int = 20,
    admin=AdminDep,
):
    db = await get_db()
    where, params = [], []
    if status:  where.append("b.status = ?");  params.append(status)
    if service: where.append("b.service = ?"); params.append(service)
    if date:    where.append("b.date = ?");    params.append(date)
    if search:
        where.append("(b.name LIKE ? OR b.email LIKE ? OR b.phone LIKE ? OR b.booking_ref LIKE ?)")
        q = f"%{search}%"
        params.extend([q, q, q, q])

    clause = f"WHERE {' AND '.join(where)}" if where else ""
    offset = (page - 1) * limit

    async with db.execute(f"SELECT COUNT(*) FROM bookings b {clause}", params) as c:
        total = (await c.fetchone())[0]

    async with db.execute(
        f"SELECT b.* FROM bookings b {clause} ORDER BY b.created_at DESC LIMIT ? OFFSET ?",
        params + [limit, offset],
    ) as c:
        rows = [dict(r) for r in await c.fetchall()]

    return {"success": True, "total": total, "page": page, "limit": limit,
            "total_pages": -(-total // limit), "bookings": rows}


@router.get("/bookings/{booking_id}")
async def get_booking(booking_id: int, admin=AdminDep):
    db = await get_db()
    async with db.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)) as c:
        row = await c.fetchone()
    if not row:
        raise HTTPException(404, "Booking not found.")
    return {"success": True, "booking": dict(row)}


class BookingUpdate(BaseModel):
    status:      Optional[str] = None
    assigned_to: Optional[str] = None
    price:       Optional[float] = None
    notes:       Optional[str] = None
    date:        Optional[str] = None
    time:        Optional[str] = None
    area:        Optional[str] = None

VALID_STATUSES = {"pending","confirmed","in_progress","completed","cancelled"}

@router.put("/bookings/{booking_id}")
async def update_booking(booking_id: int, body: BookingUpdate,
                         request: Request, admin=AdminDep):
    db = await get_db()
    async with db.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)) as c:
        old = await c.fetchone()
    if not old:
        raise HTTPException(404, "Booking not found.")

    if body.status and body.status not in VALID_STATUSES:
        raise HTTPException(400, "Invalid status value.")

    # Only update fields that were provided
    updates, params = [], []
    field_map = {
        "status": body.status, "assigned_to": body.assigned_to,
        "price": body.price,   "notes": body.notes,
        "date": body.date,     "time": body.time, "area": body.area,
    }
    for col, val in field_map.items():
        if val is not None:
            updates.append(f"{col}=?")
            params.append(val)

    if updates:
        updates.append("updated_at=datetime('now')")
        params.append(booking_id)
        await db.execute(
            f"UPDATE bookings SET {', '.join(updates)} WHERE id=?", params
        )
        await db.commit()

    async with db.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)) as c:
        updated = dict(await c.fetchone())

    await audit(admin["email"], "UPDATE_BOOKING", "bookings", booking_id,
                f"status→{body.status}", request.client.host)

    # Email customer on status change
    if body.status and body.status != old["status"]:
        await send_booking_status(updated)

    return {"success": True, "message": "Booking updated.", "booking": updated}


@router.delete("/bookings/{booking_id}", status_code=200)
async def delete_booking(booking_id: int, request: Request, admin=AdminDep):
    db = await get_db()
    async with db.execute("SELECT booking_ref FROM bookings WHERE id=?", (booking_id,)) as c:
        row = await c.fetchone()
    if not row:
        raise HTTPException(404, "Booking not found.")
    await db.execute("DELETE FROM bookings WHERE id=?", (booking_id,))
    await db.commit()
    await audit(admin["email"], "DELETE_BOOKING", "bookings", booking_id,
                row["booking_ref"], request.client.host)
    return {"success": True, "message": "Booking deleted."}


# ══════════════════════════════════════════
# MESSAGES
# ══════════════════════════════════════════
@router.get("/messages")
async def list_messages(status: Optional[str] = None, page: int = 1,
                        limit: int = 20, admin=AdminDep):
    db = await get_db()
    where = "WHERE status=?" if status else ""
    params = [status] if status else []
    offset = (page - 1) * limit

    async with db.execute(f"SELECT COUNT(*) FROM messages {where}", params) as c:
        total = (await c.fetchone())[0]
    async with db.execute(
        f"SELECT * FROM messages {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        params + [limit, offset],
    ) as c:
        rows = [dict(r) for r in await c.fetchall()]

    return {"success": True, "total": total, "messages": rows}


class MsgStatusIn(BaseModel):
    status: str

@router.put("/messages/{msg_id}")
async def update_message(msg_id: int, body: MsgStatusIn, admin=AdminDep):
    if body.status not in ("unread", "read", "replied"):
        raise HTTPException(400, "Invalid status.")
    db = await get_db()
    await db.execute("UPDATE messages SET status=? WHERE id=?", (body.status, msg_id))
    await db.commit()
    return {"success": True, "message": "Message status updated."}

@router.delete("/messages/{msg_id}")
async def delete_message(msg_id: int, request: Request, admin=AdminDep):
    db = await get_db()
    await db.execute("DELETE FROM messages WHERE id=?", (msg_id,))
    await db.commit()
    await audit(admin["email"], "DELETE_MESSAGE", "messages", msg_id, ip=request.client.host)
    return {"success": True, "message": "Message deleted."}


# ══════════════════════════════════════════
# USERS
# ══════════════════════════════════════════
@router.get("/users")
async def list_users(search: Optional[str] = None, role: Optional[str] = None,
                     page: int = 1, limit: int = 20, admin=AdminDep):
    db = await get_db()
    where, params = [], []
    if role:   where.append("role=?");  params.append(role)
    if search:
        where.append("(name LIKE ? OR email LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    clause = f"WHERE {' AND '.join(where)}" if where else ""
    offset = (page - 1) * limit

    async with db.execute(f"SELECT COUNT(*) FROM users {clause}", params) as c:
        total = (await c.fetchone())[0]
    async with db.execute(
        f"SELECT id, name, email, phone, role, verified, created_at FROM users {clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        params + [limit, offset],
    ) as c:
        users = [dict(r) for r in await c.fetchall()]

    # Attach booking count per user
    for u in users:
        async with db.execute(
            "SELECT COUNT(*) FROM bookings WHERE user_id=? OR email=?",
            (u["id"], u["email"]),
        ) as c:
            u["booking_count"] = (await c.fetchone())[0]

    return {"success": True, "total": total, "users": users}


@router.get("/users/{user_id}")
async def get_user(user_id: int, admin=AdminDep):
    db = await get_db()
    async with db.execute(
        "SELECT id, name, email, phone, role, verified, created_at FROM users WHERE id=?",
        (user_id,),
    ) as c:
        user = await c.fetchone()
    if not user:
        raise HTTPException(404, "User not found.")
    user = dict(user)

    async with db.execute(
        "SELECT * FROM bookings WHERE user_id=? OR email=? ORDER BY created_at DESC",
        (user_id, user["email"]),
    ) as c:
        bookings = [dict(r) for r in await c.fetchall()]

    return {"success": True, "user": user, "bookings": bookings}


class RoleIn(BaseModel):
    role: str

@router.put("/users/{user_id}/role")
async def change_role(user_id: int, body: RoleIn, request: Request, admin=AdminDep):
    if body.role not in ("customer", "admin"):
        raise HTTPException(400, "Invalid role.")
    if user_id == admin["id"]:
        raise HTTPException(400, "You cannot change your own role.")
    db = await get_db()
    await db.execute(
        "UPDATE users SET role=?, updated_at=datetime('now') WHERE id=?",
        (body.role, user_id),
    )
    await db.commit()
    await audit(admin["email"], "CHANGE_ROLE", "users", user_id, body.role, request.client.host)
    return {"success": True, "message": f"Role updated to {body.role}."}


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, request: Request, admin=AdminDep):
    if user_id == admin["id"]:
        raise HTTPException(400, "You cannot delete yourself.")
    db = await get_db()
    await db.execute("DELETE FROM users WHERE id=?", (user_id,))
    await db.commit()
    await audit(admin["email"], "DELETE_USER", "users", user_id, ip=request.client.host)
    return {"success": True, "message": "User deleted."}


# ══════════════════════════════════════════
# AUDIT LOG
# ══════════════════════════════════════════
@router.get("/audit")
async def audit_log(page: int = 1, limit: int = 50, admin=AdminDep):
    db = await get_db()
    offset = (page - 1) * limit
    async with db.execute("SELECT COUNT(*) FROM audit_log") as c:
        total = (await c.fetchone())[0]
    async with db.execute(
        "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ) as c:
        logs = [dict(r) for r in await c.fetchall()]
    return {"success": True, "total": total, "logs": logs}


# ══════════════════════════════════════════
# QUOTES (admin view)
# ══════════════════════════════════════════
@router.get("/quotes")
async def list_quotes(page: int = 1, limit: int = 20, admin=AdminDep):
    db = await get_db()
    offset = (page - 1) * limit
    async with db.execute("SELECT COUNT(*) FROM quotes") as c:
        total = (await c.fetchone())[0]
    async with db.execute(
        "SELECT * FROM quotes ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ) as c:
        rows = [dict(r) for r in await c.fetchall()]
    return {"success": True, "total": total, "quotes": rows}
