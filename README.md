# 🌿 SaFi Njema Cleaning Services – Backend API

Full Node.js + Express + SQLite backend for the SaFi Njema website.

---

## 📁 Project Structure

```
safinjema-backend/
├── server.js              # Main Express server (entry point)
├── db.js                  # SQLite database setup & helpers
├── mailer.js              # Email templates & Nodemailer config
├── package.json
├── .env.example           # ← Copy to .env and fill in
├── middleware/
│   └── auth.js            # JWT authentication middleware
├── routes/
│   ├── auth.js            # Register, login, profile, password reset
│   ├── bookings.js        # Create bookings, view own bookings, cancel
│   ├── contact.js         # Contact/quote form
│   └── admin.js           # Full admin dashboard API
├── data/
│   └── safinjema.db       # SQLite database (auto-created)
└── public/                # ← Place your HTML/CSS/JS files here
    ├── Java.js            # Updated frontend script (API-connected)
    └── admin.html         # Admin dashboard UI
```

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
cd safinjema-backend
npm install
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
PORT=5000
JWT_SECRET=your_super_secret_key_here_at_least_64_chars
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=safinjema@outlook.com
SMTP_PASS=your_email_password
ADMIN_EMAIL=safinjema@outlook.com
FRONTEND_ORIGIN=https://safinjema.co.za
```

### 3. Copy your frontend files

Copy all your `.html`, `style.css`, and `image/` folder into the `public/` directory.
**Replace** the old `Java.js` with the new one from `public/Java.js`.

```
public/
├── index.html
├── About.html
├── Book.html
├── services.html
├── contact.html
├── Galary.html
├── residential.html
├── commercial.html
├── industrial.html
├── events.html
├── login.html
├── register.html
├── style.css
├── Java.js          ← replace with the new one
├── admin.html       ← new admin dashboard
└── image/           ← your images folder
```

### 4. Start the server

```bash
# Production
npm start

# Development (auto-reload)
npm run dev
```

Server starts at: **http://localhost:5000**

---

## 🔑 Default Admin Login

On first run, a default admin account is created:

| Field    | Value                           |
|----------|---------------------------------|
| Email    | `safinjema@outlook.com`         |
| Password | `SafiNjema@Admin2026`           |

**Change this immediately** in your `.env` file:
```env
ADMIN_EMAIL=safinjema@outlook.com
ADMIN_PASSWORD=YourNewSecurePassword123!
```

Then delete `data/safinjema.db` and restart to recreate with new credentials.

---

## 📡 API Endpoints

### Health
```
GET  /api/health        → Server status check
GET  /api               → Full endpoint map
```

### Authentication
```
POST /api/auth/register         → Create new account
POST /api/auth/login            → Sign in, get JWT token
GET  /api/auth/me        🔒    → Get current user profile
PUT  /api/auth/profile   🔒    → Update name/phone
PUT  /api/auth/change-password 🔒 → Change password
POST /api/auth/forgot-password  → Send reset link
POST /api/auth/reset-password   → Apply reset token
```

### Bookings
```
POST /api/bookings              → Submit a new booking
GET  /api/bookings/my    🔒    → Customer's own bookings
GET  /api/bookings/:ref  🔒    → Get booking by reference
PUT  /api/bookings/:ref/cancel 🔒 → Cancel a booking
```

### Contact
```
POST /api/contact               → Submit contact/quote form
```

### Admin (🔒👑 admin only)
```
GET    /api/admin/dashboard           → Stats overview
GET    /api/admin/bookings            → All bookings (filterable)
GET    /api/admin/bookings/:id        → Single booking
PUT    /api/admin/bookings/:id        → Update booking
DELETE /api/admin/bookings/:id        → Delete booking
GET    /api/admin/messages            → All contact messages
PUT    /api/admin/messages/:id        → Mark read/replied
DELETE /api/admin/messages/:id        → Delete message
GET    /api/admin/users               → All users
GET    /api/admin/users/:id           → User + their bookings
PUT    /api/admin/users/:id/role      → Change user role
DELETE /api/admin/users/:id           → Delete user
GET    /api/admin/audit               → Audit log
```

🔒 = Requires `Authorization: Bearer <token>` header  
👑 = Requires admin role

---

## 📧 Email Configuration

### Microsoft Outlook / Office 365
```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=safinjema@outlook.com
SMTP_PASS=your_password
```

### Gmail (App Password required)
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=your@gmail.com
SMTP_PASS=your_app_password  # Not your regular Gmail password
```

> For Gmail: Go to Google Account → Security → 2-Step Verification → App passwords

---

## 🗄️ Database

SQLite database is stored at `data/safinjema.db`. Tables:

| Table         | Purpose                          |
|---------------|----------------------------------|
| `users`       | Customer and admin accounts      |
| `bookings`    | All booking requests             |
| `messages`    | Contact form submissions         |
| `reset_tokens`| Password reset tokens            |
| `audit_log`   | Action audit trail               |

---

## 🌐 Production Deployment

### Option A: VPS / Linux server (recommended)

```bash
# Install Node.js 20+
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install PM2 (process manager)
npm install -g pm2

# Start app
pm2 start server.js --name safinjema-api
pm2 save
pm2 startup

# Nginx config (proxy to Node)
# Add to your Nginx server block:
location /api {
    proxy_pass http://localhost:5000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
}
```

### Option B: Railway / Render / Fly.io

1. Push to GitHub
2. Connect to Railway/Render
3. Set environment variables in their dashboard
4. Deploy — they handle the rest

---

## 🔒 Security Features

- ✅ JWT authentication with expiry
- ✅ Passwords hashed with bcrypt (12 rounds)
- ✅ Rate limiting on all API routes
- ✅ Stricter limits on auth and form routes
- ✅ Input validation with `validator.js`
- ✅ SQL injection protection (parameterised queries)
- ✅ HTTP security headers via Helmet
- ✅ CORS whitelist
- ✅ Request size limits (10kb)
- ✅ Audit log for all admin actions

---

## 📞 Support

SaFi Njema Cleaning Services  
📞 +27 71 359 9995  
✉️ safinjema@outlook.com  
📍 Cape Town, South Africa
# 🌿 SaFi Njema Cleaning Services – Python Backend

**FastAPI + SQLite (aiosqlite) + JWT + aiosmtplib**

---

## 📁 Project Structure

```
safinjema-python/
├── main.py              # FastAPI app entry point
├── config.py            # Settings from .env
├── database.py          # Async SQLite schema, init, helpers
├── mailer.py            # Async email sending + Jinja2 HTML templates
├── requirements.txt
├── .env.example         # ← Copy to .env and fill in
├── middleware/
│   └── auth.py          # JWT helpers + FastAPI dependencies
├── routes/
│   ├── auth.py          # Register, login, profile, password reset
│   ├── bookings.py      # Create, list, cancel bookings
│   ├── contact.py       # Contact/quote form
│   ├── quotes.py        # Service pricing matrix + quote requests
│   └── admin.py         # Full admin CRUD dashboard
├── data/
│   └── safinjema.db     # SQLite DB (auto-created on startup)
├── public/              # ← Place your HTML/CSS/JS files here
├── test_api.py          # pytest test suite
└── deploy.sh            # Ubuntu production deployment
```

---

## 🚀 Quick Start

### 1. Create virtual environment

```bash
cd safinjema-python
python3 -m venv .venv
source .venv/bin/activate       # Linux/Mac
# .venv\Scripts\activate        # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
nano .env
```

Minimum required settings:
```env
JWT_SECRET=your_64_character_random_string_here
SMTP_USER=safinjema@outlook.com
SMTP_PASS=your_email_password
ADMIN_EMAIL=safinjema@outlook.com
ADMIN_PASSWORD=YourSecureAdminPassword!
```

### 4. Copy your frontend files

```
public/
├── index.html
├── About.html
├── Book.html
├── services.html
├── contact.html
├── Galary.html
├── residential.html
├── commercial.html
├── industrial.html
├── events.html
├── login.html          ← updated version
├── register.html       ← updated version
├── account.html        ← new customer dashboard
├── admin.html          ← new admin dashboard
├── forgot-password.html
├── reset-password.html
├── style.css
├── Java.js             ← updated API-connected version
└── image/              ← your images folder
```

### 5. Run the server

```bash
# Development (with auto-reload)
uvicorn main:app --reload --port 8000

# Or simply:
python main.py
```

Server: **http://localhost:8000**  
API Docs: **http://localhost:8000/docs** ← interactive Swagger UI  
ReDoc: **http://localhost:8000/redoc**

---

## 🔑 Default Admin

Created automatically on first startup:

| Field    | Value (from .env)          |
|----------|---------------------------|
| Email    | `ADMIN_EMAIL` value        |
| Password | `ADMIN_PASSWORD` value     |

---

## 📡 API Endpoints

### Auth
```
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me                    🔒
PUT  /api/auth/profile               🔒
PUT  /api/auth/change-password       🔒
POST /api/auth/forgot-password
POST /api/auth/reset-password
```

### Bookings
```
POST /api/bookings
GET  /api/bookings/my                🔒
GET  /api/bookings/{ref}             🔒
PUT  /api/bookings/{ref}/cancel      🔒
```

### Contact
```
POST /api/contact
```

### Quotes / Pricing
```
GET  /api/quotes/services
GET  /api/quotes/services/{id}
GET  /api/quotes/estimate/{id}
POST /api/quotes
GET  /api/quotes/my                  🔒
```

### Admin (🔒👑)
```
GET    /api/admin/dashboard
GET    /api/admin/bookings
GET    /api/admin/bookings/{id}
PUT    /api/admin/bookings/{id}
DELETE /api/admin/bookings/{id}
GET    /api/admin/messages
PUT    /api/admin/messages/{id}
DELETE /api/admin/messages/{id}
GET    /api/admin/users
GET    /api/admin/users/{id}
PUT    /api/admin/users/{id}/role
DELETE /api/admin/users/{id}
GET    /api/admin/audit
GET    /api/admin/quotes
```

🔒 = Bearer token required &nbsp; 👑 = Admin role required

---

## 🧪 Running Tests

```bash
pip install pytest pytest-asyncio
pytest test_api.py -v
```

Expected output: **35+ tests passing**

---

## 📧 Email (SMTP)

### Outlook / Office 365
```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=safinjema@outlook.com
SMTP_PASS=your_password
```

### Gmail (needs App Password)
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASS=your_16_char_app_password
```

> Leave `SMTP_PASS` empty in development — emails will be logged to console instead.

---

## 🌐 Production Deployment

```bash
chmod +x deploy.sh
sudo bash deploy.sh
```

This installs: Python venv, Gunicorn (4 workers), Nginx reverse proxy, SSL via Certbot, systemd service.

### Manual Gunicorn start:
```bash
source .venv/bin/activate
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Useful commands:
```bash
systemctl status safinjema      # service status
journalctl -u safinjema -f      # live logs
systemctl restart safinjema     # restart
```

---

## 🔒 Security Features

- ✅ JWT with configurable expiry (default 7 days)
- ✅ bcrypt password hashing (12 rounds)
- ✅ Rate limiting via `slowapi`
- ✅ Input validation via Pydantic v2
- ✅ SQLite with parameterised queries (no SQL injection)
- ✅ CORS whitelist
- ✅ Admin role guard on all admin routes
- ✅ Audit log for all admin actions
- ✅ Password reset tokens expire in 1 hour

---

## 🗄️ Database Tables

| Table          | Purpose                         |
|----------------|---------------------------------|
| `users`        | Customer and admin accounts     |
| `bookings`     | All booking requests            |
| `messages`     | Contact form submissions        |
| `quotes`       | Quote/pricing requests          |
| `reset_tokens` | Password reset tokens           |
| `audit_log`    | Admin action trail              |

---

**SaFi Njema Cleaning Services** · 📞 +27 71 359 9995 · 📍 Cape Town, SA
