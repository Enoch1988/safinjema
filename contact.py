# routes/contact.py
from typing import Optional
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr

from database import audit, get_db
from middleware.auth import get_optional_user
from mailer import send_admin_contact_alert, send_contact_autoreply

router = APIRouter(prefix="/api/contact", tags=["Contact"])


class ContactIn(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    service: Optional[str] = None
    message: str

    def validate_message(self):
        if len(self.message.strip()) < 5:
            raise ValueError("Message is too short.")


@router.post("", status_code=201)
async def send_contact(body: ContactIn, request: Request,
                       _user=Depends(get_optional_user)):
    if len(body.message.strip()) < 5:
        from fastapi import HTTPException
        raise HTTPException(400, "Message is too short.")

    db = await get_db()
    async with db.execute(
        "INSERT INTO messages (name, email, phone, service, message) VALUES (?,?,?,?,?)",
        (body.name.strip(), body.email.lower(),
         body.phone.strip() if body.phone else None,
         body.service.strip() if body.service else None,
         body.message.strip()),
    ) as cur:
        msg_id = cur.lastrowid
    await db.commit()

    data = body.model_dump()
    await audit(body.email, "CONTACT_FORM", "messages", msg_id, ip=request.client.host)
    await send_contact_autoreply(data)
    await send_admin_contact_alert(data)

    return {"success": True, "message": "Message received! We'll reply within 24 hours."}
