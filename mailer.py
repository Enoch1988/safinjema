# mailer.py – Async email sending with HTML templates
import asyncio
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, DictLoader
from config import settings

# ── HTML email base template ──────────────────────────────────
BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body{margin:0;padding:0;background:#f0f4f0;font-family:Arial,sans-serif;}
  .wrap{max-width:600px;margin:28px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.08);}
  .hdr{background:linear-gradient(135deg,#1a6b3c,#2d9e60);padding:28px 36px;text-align:center;}
  .hdr h1{color:#fff;font-size:20px;margin:6px 0 0;}
  .hdr p{color:rgba(255,255,255,.75);font-size:12px;margin:4px 0 0;}
  .body{padding:28px 36px;}
  .highlight{background:#f0faf4;border-left:4px solid #2d9e60;padding:14px 18px;border-radius:0 8px 8px 0;margin:16px 0;}
  table{width:100%;border-collapse:collapse;}
  td{padding:9px 12px;font-size:14px;border-bottom:1px solid #f0f0f0;}
  td:first-child{font-weight:600;color:#555;width:38%;background:#fafafa;}
  .btn{display:inline-block;background:linear-gradient(135deg,#1a6b3c,#2d9e60);color:#fff;text-decoration:none;padding:11px 26px;border-radius:8px;font-size:14px;font-weight:600;margin-top:8px;}
  .badge{display:inline-block;padding:3px 12px;border-radius:50px;font-size:11px;font-weight:700;text-transform:uppercase;}
  .footer{background:#f8faf8;padding:16px 36px;text-align:center;font-size:11px;color:#999;}
  h2{color:#1a6b3c;margin-top:0;}
  hr{border:none;border-top:1px solid #eee;margin:20px 0;}
</style>
</head>
<body><div class="wrap">
  <div class="hdr">
    <div style="font-size:26px;">🌿</div>
    <h1>SaFi Njema Cleaning Services</h1>
    <p>Professional Eco-Friendly Cleaning · Cape Town</p>
  </div>
  <div class="body">{% block content %}{% endblock %}</div>
  <div class="footer">
    📞 +27 71 359 9995 &nbsp;|&nbsp; ✉️ safinjema@outlook.com &nbsp;|&nbsp; 📍 Cape Town, SA<br>
    © 2026 SaFi Njema Cleaning Services · Eco-Friendly Solutions 🌿
  </div>
</div></body></html>
"""

TEMPLATES = {
    "booking_confirm": BASE_HTML.replace(
        "{% block content %}{% endblock %}",
        """
        <h2>Booking Confirmed! 🎉</h2>
        <p>Hi <strong>{{ name }}</strong>, we've received your booking request. Our team will confirm within <strong>30 minutes</strong>.</p>
        <div class="highlight"><strong>Booking Reference: <span style="color:#2d9e60;">{{ booking_ref }}</span></strong><br>
        <span style="font-size:12px;color:#888;">Please keep this for your records.</span></div>
        <hr>
        <table>
          <tr><td>Service</td><td>{{ service }}</td></tr>
          <tr><td>Date</td><td>{{ date }}</td></tr>
          <tr><td>Time</td><td>{{ time }}</td></tr>
          <tr><td>Area</td><td>{{ area or 'To be confirmed' }}</td></tr>
          <tr><td>Status</td><td><span class="badge" style="background:#fff3cd;color:#856404;">Pending</span></td></tr>
        </table>
        <hr>
        <a href="https://wa.me/27713599995?text=Hi%20SaFi%20Njema!%20My%20booking%20ref%20is%20{{ booking_ref }}" class="btn">💬 Chat on WhatsApp</a>
        """),
    "admin_booking": BASE_HTML.replace(
        "{% block content %}{% endblock %}",
        """
        <h2>🔔 New Booking Request</h2>
        <table>
          <tr><td>Reference</td><td><strong style="color:#2d9e60;">{{ booking_ref }}</strong></td></tr>
          <tr><td>Client</td><td>{{ name }}</td></tr>
          <tr><td>Phone</td><td>{{ phone }}</td></tr>
          <tr><td>Email</td><td>{{ email }}</td></tr>
          <tr><td>Service</td><td><strong>{{ service }}</strong></td></tr>
          <tr><td>Date</td><td>{{ date }}</td></tr>
          <tr><td>Time</td><td>{{ time }}</td></tr>
          <tr><td>Area</td><td>{{ area or '—' }}</td></tr>
          <tr><td>Notes</td><td>{{ notes or '—' }}</td></tr>
        </table>
        <hr>
        <a href="https://wa.me/{{ phone | replace(' ','') | replace('+','') }}?text=Hi%20{{ name }}!%20SaFi%20Njema%20here%20confirming%20your%20{{ service }}." class="btn">💬 WhatsApp Client</a>
        """),
    "booking_status": BASE_HTML.replace(
        "{% block content %}{% endblock %}",
        """
        <h2>Booking Update</h2>
        <p>Hi <strong>{{ name }}</strong>, {{ status_msg }}</p>
        <div class="highlight">
          <strong>Ref: <span style="color:#2d9e60;">{{ booking_ref }}</span></strong> &nbsp;
          <span class="badge" style="background:{{ status_bg }};color:{{ status_color }};">{{ status }}</span>
        </div>
        <table>
          <tr><td>Service</td><td>{{ service }}</td></tr>
          <tr><td>Date</td><td>{{ date }}</td></tr>
          <tr><td>Time</td><td>{{ time }}</td></tr>
          {% if assigned_to %}<tr><td>Assigned To</td><td>{{ assigned_to }}</td></tr>{% endif %}
        </table>
        <hr>
        <a href="https://wa.me/27713599995" class="btn">💬 Contact Us</a>
        """),
    "contact_reply": BASE_HTML.replace(
        "{% block content %}{% endblock %}",
        """
        <h2>Thanks for reaching out! 👋</h2>
        <p>Hi <strong>{{ name }}</strong>, we received your message and will reply within <strong>24 hours</strong>.</p>
        <div class="highlight"><strong>Your message:</strong><br>
        <span style="font-style:italic;color:#555;">"{{ message }}"</span></div>
        <hr>
        <a href="https://wa.me/27713599995" class="btn">💬 Chat on WhatsApp</a>
        """),
    "admin_contact": BASE_HTML.replace(
        "{% block content %}{% endblock %}",
        """
        <h2>📩 New Website Enquiry</h2>
        <table>
          <tr><td>Name</td><td>{{ name }}</td></tr>
          <tr><td>Email</td><td>{{ email }}</td></tr>
          <tr><td>Phone</td><td>{{ phone or '—' }}</td></tr>
          <tr><td>Service</td><td>{{ service or '—' }}</td></tr>
          <tr><td>Message</td><td>{{ message }}</td></tr>
        </table>
        <hr>
        <a href="mailto:{{ email }}?subject=Re: SaFi Njema Enquiry" class="btn">📧 Reply by Email</a>
        """),
    "welcome": BASE_HTML.replace(
        "{% block content %}{% endblock %}",
        """
        <h2>Welcome to SaFi Njema! 🌿</h2>
        <p>Hi <strong>{{ name }}</strong>, your account has been created successfully.</p>
        <div class="highlight">You can now book cleaning services, track appointments and manage everything from your account dashboard.</div>
        <hr>
        <a href="https://safinjema.co.za/Book.html" class="btn">📅 Book Your First Clean</a>
        """),
    "reset_password": BASE_HTML.replace(
        "{% block content %}{% endblock %}",
        """
        <h2>Password Reset Request 🔐</h2>
        <p>Hi <strong>{{ name }}</strong>, click the button below to set a new password. This link expires in <strong>1 hour</strong>.</p>
        <hr>
        <a href="{{ reset_url }}" class="btn">🔑 Reset My Password</a>
        <p style="font-size:12px;color:#aaa;margin-top:18px;">If you didn't request this, ignore this email.</p>
        """),
}

jinja_env = Environment(loader=DictLoader(TEMPLATES))


# ── Async send ────────────────────────────────────────────────
async def send_email(to: str, subject: str, html: str, text: str = ""):
    """Send an email asynchronously. Silently logs on failure."""
    if not settings.SMTP_PASS:
        print(f"📧 [DEV] Email to {to}: {subject}")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = settings.SMTP_FROM
    msg["To"]      = to
    if text:
        msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASS,
            start_tls=True,
        )
        print(f"📧 Email sent → {to}")
    except Exception as e:
        print(f"❌ Email failed → {to}: {e}")


def render(template_name: str, **ctx) -> str:
    return jinja_env.get_template(template_name).render(**ctx)


# ── Template helpers ──────────────────────────────────────────
async def send_booking_confirmation(booking: dict):
    html = render("booking_confirm", **booking)
    asyncio.create_task(send_email(
        booking["email"],
        f"✅ Booking Received – {booking['booking_ref']} | SaFi Njema",
        html,
        f"Hi {booking['name']}, your booking {booking['booking_ref']} for {booking['service']} on {booking['date']} is received."
    ))


async def send_admin_booking_alert(booking: dict):
    html = render("admin_booking", **booking)
    asyncio.create_task(send_email(
        settings.ADMIN_EMAIL,
        f"🔔 NEW BOOKING: {booking['service']} – {booking['name']}",
        html,
    ))


STATUS_META = {
    "confirmed":   ("Your booking has been confirmed!", "#d1e7dd", "#0f5132"),
    "in_progress": ("Our team is on their way!", "#cff4fc", "#055160"),
    "completed":   ("Your cleaning is complete. We hope you love the results!", "#d1e7dd", "#0f5132"),
    "cancelled":   ("Your booking has been cancelled. Contact us if this was an error.", "#f8d7da", "#842029"),
}

async def send_booking_status(booking: dict):
    meta = STATUS_META.get(booking.get("status"), ("Your booking status was updated.", "#eee", "#333"))
    html = render("booking_status",
        status_msg=meta[0], status_bg=meta[1], status_color=meta[2], **booking)
    asyncio.create_task(send_email(
        booking["email"],
        f"Booking {booking['status'].title()} – {booking['booking_ref']} | SaFi Njema",
        html,
    ))


async def send_contact_autoreply(data: dict):
    html = render("contact_reply", **data)
    asyncio.create_task(send_email(data["email"], "We received your message | SaFi Njema", html))


async def send_admin_contact_alert(data: dict):
    html = render("admin_contact", **data)
    asyncio.create_task(send_email(settings.ADMIN_EMAIL, f"📩 Enquiry from {data['name']}", html))


async def send_welcome(user: dict):
    html = render("welcome", **user)
    asyncio.create_task(send_email(user["email"], "Welcome to SaFi Njema! 🌿", html))


async def send_password_reset(user: dict, token: str, base_url: str):
    reset_url = f"{base_url}/reset-password.html?token={token}"
    html = render("reset_password", name=user["name"], reset_url=reset_url)
    asyncio.create_task(send_email(user["email"], "Reset your SaFi Njema password 🔐", html))
