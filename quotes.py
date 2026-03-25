# routes/quotes.py – Service pricing + quote requests
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr

from database import audit, get_db
from middleware.auth import get_current_user, get_optional_user

router = APIRouter(prefix="/api/quotes", tags=["Quotes"])

# ── Pricing matrix ────────────────────────────────────────────
SERVICES = [
    {
        "id": "carpet", "name": "Carpet Cleaning", "category": "Residential",
        "description": "Hot-water extraction removes embedded dirt, stains and allergens.",
        "pricing": [
            {"label": "Studio / 1-Bed (≤50m²)",  "price": 450,  "unit": "per session"},
            {"label": "2-Bed (51–100m²)",          "price": 750,  "unit": "per session"},
            {"label": "3-Bed (101–150m²)",          "price": 1050, "unit": "per session"},
            {"label": "4-Bed+ (151m²+)",            "price": 1400, "unit": "per session"},
        ],
        "notes": "Includes pre-treatment and hot-water extraction.",
    },
    {
        "id": "couch", "name": "Couch / Upholstery Cleaning", "category": "Residential",
        "description": "Restores fabric sofas, chairs and curtains.",
        "pricing": [
            {"label": "2-Seater Sofa",   "price": 350, "unit": "per piece"},
            {"label": "3-Seater Sofa",   "price": 450, "unit": "per piece"},
            {"label": "L-Shape Sofa",    "price": 750, "unit": "per piece"},
            {"label": "Single Armchair", "price": 250, "unit": "per piece"},
        ],
        "notes": "Leather cleaning available. Drying time: 2–4 hours.",
    },
    {
        "id": "mattress", "name": "Mattress Sanitising", "category": "Residential",
        "description": "UV treatment + deep cleaning eliminates dust mites and bacteria.",
        "pricing": [
            {"label": "Single Mattress", "price": 280, "unit": "per mattress"},
            {"label": "Double Mattress", "price": 350, "unit": "per mattress"},
            {"label": "Queen Mattress",  "price": 420, "unit": "per mattress"},
            {"label": "King Mattress",   "price": 500, "unit": "per mattress"},
        ],
        "notes": "Recommended every 6 months.",
    },
    {
        "id": "windows", "name": "Window Cleaning", "category": "Residential",
        "description": "Interior and exterior window cleaning for streak-free results.",
        "pricing": [
            {"label": "Up to 10 windows",  "price": 400, "unit": "per session"},
            {"label": "11–20 windows",     "price": 650, "unit": "per session"},
            {"label": "21–30 windows",     "price": 900, "unit": "per session"},
            {"label": "30+ windows",       "price": None, "unit": "custom quote"},
        ],
        "notes": "Both sides included.",
    },
    {
        "id": "deep-home", "name": "Deep Home Cleaning", "category": "Residential",
        "description": "Full top-to-bottom deep clean of your entire home.",
        "pricing": [
            {"label": "1-Bed Apartment", "price": 950,  "unit": "per session"},
            {"label": "2-Bed House",     "price": 1400, "unit": "per session"},
            {"label": "3-Bed House",     "price": 1900, "unit": "per session"},
            {"label": "4-Bed+ House",    "price": None, "unit": "custom quote"},
        ],
        "notes": "Products included.",
    },
    {
        "id": "post-construction", "name": "Post-Construction Cleaning",
        "category": "Residential / Commercial",
        "description": "Complete cleanup after building or renovation.",
        "pricing": [
            {"label": "Small (≤80m²)",    "price": 1500, "unit": "per session"},
            {"label": "Medium (81–200m²)","price": 2800, "unit": "per session"},
            {"label": "Large (200m²+)",   "price": None, "unit": "custom quote"},
        ],
        "notes": "Site inspection recommended for large projects.",
    },
    {
        "id": "commercial-office", "name": "Commercial / Office Cleaning",
        "category": "Commercial",
        "description": "Regular office cleaning for a hygienic workplace.",
        "pricing": [
            {"label": "Small (≤100m²)",          "price": 800,  "unit": "per session"},
            {"label": "Medium (101–300m²)",       "price": 1600, "unit": "per session"},
            {"label": "Large (300m²+)",           "price": None, "unit": "custom quote"},
            {"label": "Monthly contract (3x/wk)", "price": 3500, "unit": "per month"},
        ],
        "notes": "Discounts available for weekly/monthly contracts.",
    },
    {
        "id": "industrial", "name": "Industrial Cleaning", "category": "Industrial",
        "description": "Heavy-duty factory, warehouse and plant cleaning.",
        "pricing": [{"label": "On-site assessment required", "price": None, "unit": "custom quote"}],
        "notes": "Custom pricing based on facility size and schedule.",
    },
    {
        "id": "events", "name": "Events Cleaning", "category": "Events",
        "description": "Pre, during and post-event cleaning.",
        "pricing": [
            {"label": "Small (≤100 guests)",  "price": 1200, "unit": "per event"},
            {"label": "Medium (101–300)",      "price": 2200, "unit": "per event"},
            {"label": "Large (300+ guests)",   "price": None, "unit": "custom quote"},
        ],
        "notes": "Includes setup, maintenance and teardown.",
    },
    {
        "id": "pest-control", "name": "Pest Control", "category": "Residential / Commercial",
        "description": "Safe, eco-friendly pest elimination.",
        "pricing": [
            {"label": "Cockroaches / Ants",     "price": 600,  "unit": "per session"},
            {"label": "Rodents",                "price": 800,  "unit": "per session"},
            {"label": "Bedbugs",               "price": 1200, "unit": "per session"},
            {"label": "Full property fumigation","price": None, "unit": "custom quote"},
        ],
        "notes": "Eco-safe products. Retreatment guarantee included.",
    },
    {
        "id": "solar-panels", "name": "Solar Panel Cleaning",
        "category": "Residential / Commercial",
        "description": "Increase panel efficiency with professional cleaning.",
        "pricing": [
            {"label": "1–8 panels",   "price": 350, "unit": "per session"},
            {"label": "9–16 panels",  "price": 600, "unit": "per session"},
            {"label": "17–24 panels", "price": 850, "unit": "per session"},
            {"label": "25+ panels",   "price": None, "unit": "custom quote"},
        ],
        "notes": "Deionised water used. No harsh chemicals.",
    },
    {
        "id": "bin-cleaning", "name": "Bin Cleaning", "category": "Residential",
        "description": "Sanitise and deodorise your wheelie bins.",
        "pricing": [
            {"label": "Single bin",      "price": 150, "unit": "per clean"},
            {"label": "2 bins",          "price": 250, "unit": "per clean"},
            {"label": "Monthly (1 bin)", "price": 120, "unit": "per month"},
        ],
        "notes": "Includes disinfection and deodorising spray.",
    },
]

SERVICE_MAP = {s["id"]: s for s in SERVICES}


# ── GET ALL SERVICES ──────────────────────────────────────────
@router.get("/services")
async def list_services(category: Optional[str] = None):
    if category:
        filtered = [s for s in SERVICES if category.lower() in s["category"].lower()]
    else:
        filtered = SERVICES
    return {"success": True, "services": filtered}


# ── GET SINGLE SERVICE ────────────────────────────────────────
@router.get("/services/{service_id}")
async def get_service(service_id: str):
    svc = SERVICE_MAP.get(service_id)
    if not svc:
        raise HTTPException(404, "Service not found.")
    return {"success": True, "service": svc}


# ── PRICE ESTIMATE ────────────────────────────────────────────
@router.get("/estimate/{service_id}")
async def estimate(service_id: str):
    svc = SERVICE_MAP.get(service_id)
    if not svc:
        raise HTTPException(404, "Service not found.")
    return {"success": True, "service": svc["name"], "pricing": svc["pricing"], "notes": svc["notes"]}


# ── SUBMIT QUOTE REQUEST ──────────────────────────────────────
class QuoteIn(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    service: str
    property_type: Optional[str] = None
    size_sqm: Optional[float] = None
    frequency: Optional[str] = None
    notes: Optional[str] = None


@router.post("", status_code=201)
async def submit_quote(body: QuoteIn, request: Request,
                       current_user: Optional[dict] = Depends(get_optional_user)):
    # Auto-estimate from pricing matrix
    svc = next((s for s in SERVICES if s["name"] == body.service), None)
    estimated = None
    if svc:
        first_fixed = next((p["price"] for p in svc["pricing"] if p["price"] is not None), None)
        estimated = first_fixed

    db = await get_db()
    async with db.execute(
        """INSERT INTO quotes
           (user_id, name, email, phone, service, property_type, size_sqm, frequency, notes, estimated_price)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (current_user["id"] if current_user else None,
         body.name.strip(), body.email.lower(),
         body.phone.strip() if body.phone else None, body.service,
         body.property_type, body.size_sqm, body.frequency,
         body.notes.strip() if body.notes else None, estimated),
    ) as cur:
        quote_id = cur.lastrowid
    await db.commit()

    await audit(body.email, "QUOTE_REQUEST", "quotes", quote_id,
                body.service, request.client.host)

    return {
        "success": True,
        "message": "Quote request received! We'll be in touch within 2 hours.",
        "quote_id": quote_id,
        "estimated": f"From R {estimated}" if estimated else "Custom pricing — we'll confirm shortly.",
    }


# ── MY QUOTES ─────────────────────────────────────────────────
@router.get("/my")
async def my_quotes(current_user: dict = Depends(get_current_user)):
    db = await get_db()
    async with db.execute(
        "SELECT * FROM quotes WHERE user_id=? OR email=? ORDER BY created_at DESC",
        (current_user["id"], current_user["email"]),
    ) as cur:
        rows = [dict(r) for r in await cur.fetchall()]
    return {"success": True, "quotes": rows}
