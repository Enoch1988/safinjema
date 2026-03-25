# routes/bookings.py
import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, field_validator

from database import audit, get_db, next_booking_ref
from middleware.auth import get_current_user, get_optional_user
from mailer import send_admin_booking_alert, send_booking_confirmation, send_booking_status

router = APIRouter(prefix="/api/bookings", tags=["Bookings"])

VALID_SERVICES = {
    "Carpet Cleaning", "Couch / Upholstery Cleaning", "Mattress Cleaning",
    "Window Cleaning", "Deep Home Cleaning", "Post-Construction Cleaning",
    "Commercial / Office Cleaning", "Industrial Cleaning", "Events Cleaning",
    "Pest Control", "Solar Panel Cleaning", "Bin Cleaning",
}
VALID_TIMES = {
    "7:00 AM","8:00 AM","9:00 AM","10:00 AM","11:00 AM","12:00 PM",
    "1:00 PM","2:00 PM","3:00 PM","4:00 PM","5:00 PM",
}


class BookingIn(BaseModel):
    name: str
    email: EmailStr
    phone: str
    service: str
    date: str           # YYYY-MM-DD
    time: str
    area: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("service")
    @classmethod
    def valid_service(cls, v):
        if v not in VALID_SERVICES:
            raise ValueError("Invalid service selected.")
        return v

    @field_validator("time")
    @classmethod
    def valid_time(cls, v):
        if v not in VALID_TIMES:
            raise ValueError("Invalid time selected.")
        return v

    @field_validator("date")
    @classmethod
    def future_date(cls, v):
        try:
            d = datetime.date.fromisoformat(v)
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD.")
        if d < datetime.date.today():
            raise ValueError("Please select a valid future date.")
        return v


# ── CREATE BOOKING ────────────────────────────────────────────
@router.post("", status_code=201)
async def create_booking(body: BookingIn, request: Request,
                         current_user: Optional[dict] = Depends(get_optional_user)):
    db = await get_db()
    booking_ref = await next_booking_ref()
    user_id = current_user["id"] if current_user else None

    async with db.execute(
        """INSERT INTO bookings
           (booking_ref, user_id, name, email, phone, service, date, time, area, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (booking_ref, user_id,
         body.name.strip(), body.email.lower(), body.phone.strip(),
         body.service, body.date, body.time,
         body.area.strip() if body.area else None,
         body.notes.strip() if body.notes else None),
    ) as cur:
        booking_id = cur.lastrowid
    await db.commit()

    async with db.execute(
        "SELECT * FROM bookings WHERE id=?", (booking_id,)
    ) as cur:
        booking = dict(await cur.fetchone())

    await audit(body.email, "CREATE_BOOKING", "bookings",
                booking_id, booking_ref, request.client.host)
    await send_booking_confirmation(booking)
    await send_admin_booking_alert(booking)

    return {
        "success": True,
        "message": "Booking submitted! You will receive a confirmation email shortly.",
        "booking_ref": booking_ref,
        "booking": booking,
    }


# ── MY BOOKINGS ───────────────────────────────────────────────
@router.get("/my")
async def my_bookings(current_user: dict = Depends(get_current_user)):
    db = await get_db()
    async with db.execute(
        "SELECT * FROM bookings WHERE user_id=? OR email=? ORDER BY created_at DESC",
        (current_user["id"], current_user["email"]),
    ) as cur:
        rows = [dict(r) for r in await cur.fetchall()]
    return {"success": True, "bookings": rows}


# ── GET BY REFERENCE ──────────────────────────────────────────
@router.get("/{ref}")
async def get_booking(ref: str,
                      current_user: Optional[dict] = Depends(get_optional_user)):
    db = await get_db()
    async with db.execute(
        "SELECT * FROM bookings WHERE booking_ref=?", (ref,)
    ) as cur:
        row = await cur.fetchone()

    if not row:
        raise HTTPException(404, "Booking not found.")

    booking = dict(row)
    if (current_user is None or
            (current_user.get("role") != "admin" and
             booking["email"] != current_user.get("email"))):
        raise HTTPException(403, "Access denied.")

    return {"success": True, "booking": booking}


# ── CUSTOMER CANCEL ───────────────────────────────────────────
@router.put("/{ref}/cancel")
async def cancel_booking(ref: str, request: Request,
                         current_user: dict = Depends(get_current_user)):
    db = await get_db()
    async with db.execute(
        "SELECT * FROM bookings WHERE booking_ref=?", (ref,)
    ) as cur:
        row = await cur.fetchone()

    if not row:
        raise HTTPException(404, "Booking not found.")

    booking = dict(row)
    if booking["email"] != current_user["email"] and current_user.get("role") != "admin":
        raise HTTPException(403, "Access denied.")
    if booking["status"] in ("completed", "cancelled"):
        raise HTTPException(400, f"Cannot cancel a {booking['status']} booking.")

    await db.execute(
        "UPDATE bookings SET status='cancelled', updated_at=datetime('now') WHERE booking_ref=?",
        (ref,),
    )
    await db.commit()

    async with db.execute(
        "SELECT * FROM bookings WHERE booking_ref=?", (ref,)
    ) as cur:
        updated = dict(await cur.fetchone())

    await audit(current_user["email"], "CANCEL_BOOKING", "bookings",
                booking["id"], ref, request.client.host)
    await send_booking_status(updated)

    return {"success": True, "message": "Booking cancelled.", "booking": updated}
