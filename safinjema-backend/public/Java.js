/* ═══════════════════════════════════════════════════════════════
   Java.js  –  SaFi Njema Frontend Scripts
   Connects to backend API at /api/*
   ═══════════════════════════════════════════════════════════════ */

/* ── CONFIG ── */
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:5000/api'
  : '/api';  // Same-origin in production

/* ── TOKEN HELPERS ── */
const Auth = {
  getToken:   ()      => localStorage.getItem('sn_token'),
  setToken:   (t)     => localStorage.setItem('sn_token', t),
  getUser:    ()      => { try { return JSON.parse(localStorage.getItem('sn_user') || 'null'); } catch { return null; } },
  setUser:    (u)     => localStorage.setItem('sn_user', JSON.stringify(u)),
  clear:      ()      => { localStorage.removeItem('sn_token'); localStorage.removeItem('sn_user'); },
  isLoggedIn: ()      => !!localStorage.getItem('sn_token'),
  isAdmin:    ()      => { const u = Auth.getUser(); return u?.role === 'admin'; },
};

/* ── API HELPER ── */
async function apiFetch(endpoint, options = {}) {
  const token = Auth.getToken();
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  const data = await res.json().catch(() => ({ success: false, message: 'Invalid server response.' }));
  return { ok: res.ok, status: res.status, data };
}

/* ══════════════════════════════════
   NAV
   ══════════════════════════════════ */
function toggleMenu() {
  document.getElementById('navLinks')?.classList.toggle('show');
}

/* ── Inject Login/Logout state into nav ── */
(function updateNav() {
  const user = Auth.getUser();
  const navActions = document.querySelector('.nav-actions');
  if (!navActions) return;

  if (Auth.isLoggedIn() && user) {
    // Replace login/register with user name + logout
    const loginBtn    = navActions.querySelector('a[href="login.html"]');
    const registerBtn = navActions.querySelector('a[href="register.html"]');
    if (loginBtn)    loginBtn.style.display    = 'none';
    if (registerBtn) registerBtn.style.display = 'none';

    // Add user pill if not already there
    if (!navActions.querySelector('.nav-user')) {
      const pill = document.createElement('a');
      pill.className = 'nav-auth nav-user';
      pill.href      = '#';
      pill.innerHTML = `<i class="fa fa-user"></i> ${user.name.split(' ')[0]}`;
      navActions.insertBefore(pill, navActions.querySelector('.book-btn'));

      const logoutBtn = document.createElement('a');
      logoutBtn.className = 'nav-auth';
      logoutBtn.href      = '#';
      logoutBtn.innerHTML = '<i class="fa fa-sign-out-alt"></i> Logout';
      logoutBtn.style.cursor = 'pointer';
      logoutBtn.addEventListener('click', (e) => { e.preventDefault(); handleLogout(); });
      navActions.insertBefore(logoutBtn, navActions.querySelector('.book-btn'));

      if (Auth.isAdmin()) {
        const adminBtn = document.createElement('a');
        adminBtn.className = 'nav-auth reg';
        adminBtn.href      = 'admin.html';
        adminBtn.innerHTML = '<i class="fa fa-cog"></i> Admin';
        navActions.insertBefore(adminBtn, navActions.querySelector('.book-btn'));
      }
    }
  }
})();

function handleLogout() {
  Auth.clear();
  showToast('Signed out successfully.', 'ok');
  setTimeout(() => window.location.href = 'index.html', 800);
}

/* ══════════════════════════════════
   SCROLL REVEAL
   ══════════════════════════════════ */
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
}, { threshold: 0.1 });
document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

/* ══════════════════════════════════
   SEARCH
   ══════════════════════════════════ */
function doSearch() {
  const q = (document.getElementById('sSearch') || { value: '' }).value.trim().toLowerCase();
  if (!q) return;
  const map = {
    'carpet': 'residential.html', 'couch': 'residential.html', 'sofa': 'residential.html',
    'mattress': 'residential.html', 'window': 'residential.html', 'pest': 'residential.html',
    'deep': 'residential.html', 'construction': 'residential.html',
    'office': 'commercial.html', 'commercial': 'commercial.html', 'contract': 'commercial.html',
    'factory': 'industrial.html', 'industrial': 'industrial.html', 'warehouse': 'industrial.html',
    'event': 'events.html', 'party': 'events.html', 'venue': 'events.html',
    'book': 'Book.html', 'booking': 'Book.html',
    'contact': 'contact.html', 'about': 'About.html', 'gallery': 'Galary.html',
  };
  for (const [k, v] of Object.entries(map)) {
    if (q.includes(k)) { window.location.href = v; return; }
  }
  window.location.href = 'services.html';
}
const sInput = document.getElementById('sSearch');
if (sInput) sInput.addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });

/* ══════════════════════════════════
   ACCORDION
   ══════════════════════════════════ */
document.querySelectorAll('.acc-trigger').forEach(btn => {
  btn.addEventListener('click', function () {
    const item   = this.closest('.acc-item');
    const body   = item.querySelector('.acc-body');
    const isOpen = this.classList.contains('open');
    document.querySelectorAll('.acc-trigger.open').forEach(b => {
      b.classList.remove('open');
      b.closest('.acc-item').classList.remove('open');
      b.nextElementSibling.style.display = 'none';
    });
    if (!isOpen) {
      this.classList.add('open');
      item.classList.add('open');
      body.style.display = 'block';
    }
  });
});

/* ══════════════════════════════════
   TOAST NOTIFICATION
   ══════════════════════════════════ */
function showToast(message, type = 'ok', duration = 4000) {
  let container = document.getElementById('sn-toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'sn-toast-container';
    container.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:10px;max-width:360px;';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  const colors = { ok: '#2d9e60', err: '#dc3545', info: '#0d6efd', warn: '#f0ad4e' };
  toast.style.cssText = `
    background:${colors[type] || colors.ok};color:#fff;padding:14px 20px;
    border-radius:10px;font-size:14px;font-weight:500;box-shadow:0 4px 20px rgba(0,0,0,.2);
    animation:slideIn .3s ease;cursor:pointer;line-height:1.4;
  `;
  toast.textContent = message;
  toast.addEventListener('click', () => toast.remove());
  container.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; toast.style.transition = 'opacity .4s'; setTimeout(() => toast.remove(), 400); }, duration);
}

// Inject slideIn keyframe once
if (!document.getElementById('sn-anim-style')) {
  const style = document.createElement('style');
  style.id = 'sn-anim-style';
  style.textContent = `@keyframes slideIn{from{opacity:0;transform:translateX(40px)}to{opacity:1;transform:translateX(0)}}`;
  document.head.appendChild(style);
}

/* ══════════════════════════════════
   BOOKING FORM
   ══════════════════════════════════ */
const bookForm = document.getElementById('bookingForm');
if (bookForm) {
  /* Set minimum date to tomorrow */
  const dateInput = document.getElementById('bDate');
  if (dateInput) {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    dateInput.min = tomorrow.toISOString().split('T')[0];
  }

  /* Pre-fill if logged in */
  const user = Auth.getUser();
  if (user) {
    const nameInput  = document.getElementById('bName');
    const emailInput = document.getElementById('bEmail');
    const phoneInput = document.getElementById('bPhone');
    if (nameInput  && !nameInput.value)  nameInput.value  = user.name  || '';
    if (emailInput && !emailInput.value) emailInput.value = user.email || '';
    if (phoneInput && !phoneInput.value) phoneInput.value = user.phone || '';
  }

  bookForm.addEventListener('submit', async function (e) {
    e.preventDefault();

    const submitBtn = this.querySelector('[type="submit"]');
    const msg       = document.getElementById('bookMsg');
    const payload   = {
      name:    document.getElementById('bName')?.value.trim(),
      phone:   document.getElementById('bPhone')?.value.trim(),
      email:   document.getElementById('bEmail')?.value.trim(),
      service: document.getElementById('bService')?.value,
      date:    document.getElementById('bDate')?.value,
      time:    document.getElementById('bTime')?.value,
      area:    document.getElementById('bArea')?.value.trim(),
      notes:   document.getElementById('bNotes')?.value.trim(),
    };

    if (!payload.name || !payload.phone || !payload.email || !payload.service || !payload.date || !payload.time) {
      if (msg) { msg.textContent = '⚠️ Please fill in all required fields.'; msg.className = 'alert err'; }
      return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Submitting…';

    const { ok, data } = await apiFetch('/bookings', { method: 'POST', body: JSON.stringify(payload) });

    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fa fa-calendar-check"></i> &nbsp;Confirm Booking Request';

    if (ok) {
      if (msg) {
        msg.innerHTML = `✅ Booking submitted! Ref: <strong>${data.booking_ref}</strong>. Check your email for confirmation.`;
        msg.className = 'alert ok';
      }
      showToast(`✅ Booking confirmed! Ref: ${data.booking_ref}`, 'ok', 6000);
      bookForm.reset();
      // Also open WhatsApp notification (optional, non-blocking)
      const waMsg = encodeURIComponent(
        `📋 *NEW BOOKING*\n👤 *${payload.name}*\n📞 ${payload.phone}\n🧹 ${payload.service}\n📅 ${payload.date} @ ${payload.time}\n📍 ${payload.area || 'TBC'}\n🔖 Ref: ${data.booking_ref}`
      );
      window.open(`https://wa.me/27713599995?text=${waMsg}`, '_blank');
    } else {
      if (msg) { msg.textContent = `⚠️ ${data.message || 'Submission failed. Please try again.'}`; msg.className = 'alert err'; }
      showToast(data.message || 'Booking failed. Please try again.', 'err');
    }
  });
}

/* ══════════════════════════════════
   CONTACT FORM
   ══════════════════════════════════ */
const contactForm = document.getElementById('contactForm');
if (contactForm) {
  contactForm.addEventListener('submit', async function (e) {
    e.preventDefault();

    const submitBtn = this.querySelector('[type="submit"]');
    const msg       = document.getElementById('contactMsg');
    const payload   = {
      name:    document.getElementById('cName')?.value.trim(),
      email:   document.getElementById('cEmail')?.value.trim(),
      phone:   document.getElementById('cPhone')?.value.trim(),
      service: this.querySelector('select')?.value,
      message: document.getElementById('cMsg')?.value.trim(),
    };

    if (!payload.name || !payload.email || !payload.message) {
      if (msg) { msg.textContent = 'Please fill in all required fields.'; msg.className = 'alert err'; }
      return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Sending…';

    const { ok, data } = await apiFetch('/contact', { method: 'POST', body: JSON.stringify(payload) });

    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fa fa-paper-plane"></i> &nbsp;Send Message';

    if (ok) {
      if (msg) { msg.textContent = "✅ Message sent! We'll reply within 24 hours."; msg.className = 'alert ok'; }
      showToast("✅ Message sent! We'll reply soon.", 'ok');
      contactForm.reset();
    } else {
      if (msg) { msg.textContent = `⚠️ ${data.message || 'Send failed. Please try again.'}`; msg.className = 'alert err'; }
      showToast(data.message || 'Failed to send message.', 'err');
    }
  });
}

/* ══════════════════════════════════
   LOGIN FORM
   ══════════════════════════════════ */
const loginForm = document.getElementById('loginForm');
if (loginForm) {
  loginForm.addEventListener('submit', async function (e) {
    e.preventDefault();
    const submitBtn = this.querySelector('[type="submit"]');
    const msg       = document.getElementById('loginMsg');
    const email     = document.getElementById('lEmail')?.value.trim();
    const password  = document.getElementById('lPass')?.value;

    if (!email || !password) {
      if (msg) { msg.textContent = 'Please fill in all fields.'; msg.className = 'alert err'; }
      return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Signing in…';

    const { ok, data } = await apiFetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fa fa-sign-in-alt"></i> &nbsp;Sign In';

    if (ok) {
      Auth.setToken(data.token);
      Auth.setUser(data.user);
      if (msg) { msg.textContent = '✓ Signed in successfully!'; msg.className = 'alert ok'; }
      showToast(`Welcome back, ${data.user.name.split(' ')[0]}! 👋`, 'ok');
      setTimeout(() => window.location.href = data.user.role === 'admin' ? 'admin.html' : 'index.html', 1200);
    } else {
      if (msg) { msg.textContent = data.message || 'Login failed.'; msg.className = 'alert err'; }
      showToast(data.message || 'Login failed.', 'err');
    }
  });
}

/* ══════════════════════════════════
   REGISTER FORM
   ══════════════════════════════════ */
const regForm = document.getElementById('regForm');
if (regForm) {
  regForm.addEventListener('submit', async function (e) {
    e.preventDefault();
    const submitBtn = this.querySelector('[type="submit"]');
    const msg       = document.getElementById('regMsg');
    const name      = document.getElementById('rName')?.value.trim();
    const email     = document.getElementById('rEmail')?.value.trim();
    const phone     = document.getElementById('rPhone')?.value.trim();
    const password  = document.getElementById('rPass')?.value;
    const password2 = document.getElementById('rPass2')?.value;

    if (!name || !email || !password || !password2) {
      if (msg) { msg.textContent = 'Please fill in all fields.'; msg.className = 'alert err'; }
      return;
    }
    if (password !== password2) {
      if (msg) { msg.textContent = 'Passwords do not match.'; msg.className = 'alert err'; }
      return;
    }
    if (password.length < 6) {
      if (msg) { msg.textContent = 'Password must be at least 6 characters.'; msg.className = 'alert err'; }
      return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Creating account…';

    const { ok, data } = await apiFetch('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, phone, password }),
    });

    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fa fa-user-plus"></i> &nbsp;Create Account';

    if (ok) {
      Auth.setToken(data.token);
      Auth.setUser(data.user);
      if (msg) { msg.textContent = '✓ Account created! Redirecting…'; msg.className = 'alert ok'; }
      showToast('Account created! Welcome to SaFi Njema 🌿', 'ok');
      setTimeout(() => window.location.href = 'index.html', 1500);
    } else {
      if (msg) { msg.textContent = data.message || 'Registration failed.'; msg.className = 'alert err'; }
      showToast(data.message || 'Registration failed.', 'err');
    }
  });
}

/* ══════════════════════════════════
   GALLERY LIGHTBOX
   ══════════════════════════════════ */
function openLightbox(src) {
  const lb = document.getElementById('lightbox');
  if (!lb) return;
  document.getElementById('lbImg').src = src;
  lb.classList.add('open');
}
function closeLightbox() {
  document.getElementById('lightbox')?.classList.remove('open');
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeLightbox(); });

/* ── GALLERY FILTER ── */
function filterGallery(cat) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.toggle('active', b.dataset.cat === cat));
  document.querySelectorAll('.gallery-item').forEach(item => {
    item.style.display = (cat === 'all' || item.dataset.cat === cat) ? 'block' : 'none';
  });
}

/* ══════════════════════════════════
   MY BOOKINGS (account page helper)
   ══════════════════════════════════ */
async function loadMyBookings(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;
  if (!Auth.isLoggedIn()) { container.innerHTML = '<p>Please <a href="login.html">log in</a> to view your bookings.</p>'; return; }
  container.innerHTML = '<p><i class="fa fa-spinner fa-spin"></i> Loading bookings…</p>';
  const { ok, data } = await apiFetch('/bookings/my');
  if (!ok) { container.innerHTML = `<p style="color:red">${data.message}</p>`; return; }
  if (!data.bookings.length) { container.innerHTML = '<p>No bookings yet. <a href="Book.html">Book your first clean!</a></p>'; return; }
  const statusColors = { pending:'#f0ad4e', confirmed:'#2d9e60', in_progress:'#0d6efd', completed:'#198754', cancelled:'#dc3545' };
  container.innerHTML = data.bookings.map(b => `
    <div style="background:#fff;border:1px solid #e5e5e5;border-radius:12px;padding:20px;margin-bottom:16px;">
      <div style="display:flex;justify-content:space-between;align-items:start;flex-wrap:wrap;gap:8px;">
        <div>
          <strong style="font-size:16px;">${b.service}</strong>
          <div style="font-size:13px;color:#888;margin-top:2px;">Ref: ${b.booking_ref}</div>
        </div>
        <span style="background:${statusColors[b.status]||'#888'};color:#fff;padding:4px 14px;border-radius:50px;font-size:12px;font-weight:700;text-transform:uppercase;">${b.status}</span>
      </div>
      <div style="margin-top:12px;font-size:14px;color:#555;">
        📅 ${b.date} &nbsp;⏰ ${b.time} &nbsp;📍 ${b.area || 'TBC'}
      </div>
      ${['pending','confirmed'].includes(b.status) ? `
        <button onclick="cancelBooking('${b.booking_ref}')" style="margin-top:12px;background:none;border:1px solid #dc3545;color:#dc3545;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:13px;">
          Cancel Booking
        </button>` : ''}
    </div>
  `).join('');
}

async function cancelBooking(ref) {
  if (!confirm(`Cancel booking ${ref}?`)) return;
  const { ok, data } = await apiFetch(`/bookings/${ref}/cancel`, { method: 'PUT' });
  showToast(data.message, ok ? 'ok' : 'err');
  if (ok) loadMyBookings('myBookingsContainer');
}

/* ══════════════════════════════════
   EXPOSE GLOBALS
   ══════════════════════════════════ */
window.toggleMenu    = toggleMenu;
window.doSearch      = doSearch;
window.openLightbox  = openLightbox;
window.closeLightbox = closeLightbox;
window.filterGallery = filterGallery;
window.loadMyBookings = loadMyBookings;
window.cancelBooking  = cancelBooking;
window.Auth           = Auth;
window.apiFetch       = apiFetch;
window.showToast      = showToast;
