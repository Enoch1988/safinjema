/* SaFi Njema – Main JavaScript  |  Java.js */

/* ── NAV ── */
function toggleMenu(){
  document.getElementById("navLinks").classList.toggle("show");
}

/* ── SCROLL REVEAL ── */
const revealObserver = new IntersectionObserver((entries)=>{
  entries.forEach(e=>{ if(e.isIntersecting) e.target.classList.add('visible'); });
},{threshold:0.1});
document.querySelectorAll('.reveal').forEach(el=>revealObserver.observe(el));

/* ── SEARCH ── */
function doSearch(){
  const q = (document.getElementById('sSearch')||{value:''}).value.trim().toLowerCase();
  if(!q) return;
  const map = {
    'carpet':'residential.html','couch':'residential.html','sofa':'residential.html',
    'mattress':'residential.html','window':'residential.html','pest':'residential.html',
    'deep':'residential.html','construction':'residential.html',
    'office':'commercial.html','commercial':'commercial.html','contract':'commercial.html',
    'factory':'industrial.html','industrial':'industrial.html','warehouse':'industrial.html',
    'event':'events.html','party':'events.html','venue':'events.html',
    'book':'Book.html','booking':'Book.html',
    'contact':'contact.html','about':'About.html','gallery':'Galary.html',
  };
  for(const [k,v] of Object.entries(map)){
    if(q.includes(k)){ window.location.href=v; return; }
  }
  window.location.href='services.html';
}
const sInput = document.getElementById('sSearch');
if(sInput) sInput.addEventListener('keydown', e=>{ if(e.key==='Enter') doSearch(); });

/* ── ACCORDION ── */
document.querySelectorAll('.acc-trigger').forEach(btn=>{
  btn.addEventListener('click', function(){
    const item  = this.closest('.acc-item');
    const body  = item.querySelector('.acc-body');
    const isOpen = this.classList.contains('open');
    // close all
    document.querySelectorAll('.acc-trigger.open').forEach(b=>{
      b.classList.remove('open');
      b.closest('.acc-item').classList.remove('open');
      b.nextElementSibling.style.display='none';
    });
    if(!isOpen){
      this.classList.add('open');
      item.classList.add('open');
      body.style.display='block';
    }
  });
});

/* ── BOOKING FORM ── */
const bookForm = document.getElementById('bookingForm');
if(bookForm){
  const minDate = ()=>{
    const d=new Date(); d.setDate(d.getDate()+1);
    return d.toISOString().split('T')[0];
  };
  const dateInput = document.getElementById('bDate');
  if(dateInput) dateInput.min = minDate();

  bookForm.addEventListener('submit', function(e){
    e.preventDefault();
    const d = {
      name:     document.getElementById('bName').value.trim(),
      phone:    document.getElementById('bPhone').value.trim(),
      email:    document.getElementById('bEmail').value.trim(),
      service:  document.getElementById('bService').value,
      date:     document.getElementById('bDate').value,
      time:     document.getElementById('bTime').value,
      area:     document.getElementById('bArea').value.trim(),
      notes:    document.getElementById('bNotes').value.trim(),
      submitted:new Date().toLocaleString('en-ZA'),
    };
    const msg = document.getElementById('bookMsg');
    if(!d.name||!d.phone||!d.email||!d.service||!d.date||!d.time){
      msg.textContent='⚠️ Please fill in all required fields.';
      msg.className='alert err'; return;
    }
    // Email via mailto
    const TO = 'safinjema@outlook.com';
    const sub = encodeURIComponent(`New Booking – ${d.service} – ${d.name}`);
    const body = encodeURIComponent(
      `NEW BOOKING – SaFi Njema\n`+
      `──────────────────────────\n`+
      `Name:     ${d.name}\nPhone:    ${d.phone}\nEmail:    ${d.email}\n`+
      `Service:  ${d.service}\nDate:     ${d.date}\nTime:     ${d.time}\n`+
      `Area:     ${d.area||'N/A'}\nNotes:    ${d.notes||'None'}\n`+
      `Submitted:${d.submitted}\n──────────────────────────\n[SaFi Njema Booking System]`
    );
    window.open(`mailto:${TO}?subject=${sub}&body=${body}`,'_blank');

    // WhatsApp notification
    const waMsg = encodeURIComponent(
      `📋 *NEW BOOKING*\n👤 *${d.name}*\n📞 ${d.phone}\n🧹 ${d.service}\n📅 ${d.date} @ ${d.time}\n📍 ${d.area||'TBC'}`
    );
    window.open(`https://wa.me/27713599995?text=${waMsg}`,'_blank');

    msg.textContent='✅ Booking submitted! Check your email & WhatsApp for confirmation.';
    msg.className='alert ok';
    bookForm.reset();
  });
}

/* ── CONTACT FORM ── */
const contactForm = document.getElementById('contactForm');
if(contactForm){
  contactForm.addEventListener('submit',function(e){
    e.preventDefault();
    const name=document.getElementById('cName').value.trim();
    const email=document.getElementById('cEmail').value.trim();
    const message=document.getElementById('cMsg').value.trim();
    const phone=document.getElementById('cPhone')?document.getElementById('cPhone').value.trim():'';
    const msg=document.getElementById('contactMsg');
    if(!name||!email||!message){msg.textContent='Please fill in all required fields.';msg.className='alert err';return;}
    const sub=encodeURIComponent(`Website Enquiry from ${name}`);
    const body=encodeURIComponent(`From: ${name}\nEmail: ${email}\nPhone: ${phone}\n\n${message}`);
    window.open(`mailto:info@safinjema.co.za?subject=${sub}&body=${body}`,'_blank');
    msg.textContent='✅ Message sent! We\'ll reply within 24 hours.';
    msg.className='alert ok';
    contactForm.reset();
  });
}

/* ── GALLERY LIGHTBOX ── */
function openLightbox(src){
  const lb=document.getElementById('lightbox');
  document.getElementById('lbImg').src=src;
  lb.classList.add('open');
}
function closeLightbox(){
  document.getElementById('lightbox')?.classList.remove('open');
}
document.addEventListener('keydown',e=>{ if(e.key==='Escape') closeLightbox(); });

/* ── GALLERY FILTER ── */
function filterGallery(cat){
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.toggle('active',b.dataset.cat===cat));
  document.querySelectorAll('.gallery-item').forEach(item=>{
    item.style.display=(cat==='all'||item.dataset.cat===cat)?'block':'none';
  });
}
// ── DATA ──
const SERVICES = {
  cleaning: {
    title: "Cleaning Services",
    subtitle: "Select the type of cleaning you need.",
    icon: "🧹",
    options: [
      "Deep Cleaning","End of Tenancy Cleaning","Move In & Move Out Cleaning",
      "Window Cleaning","Post Construction Cleaning","Post Renovation Cleaning",
      "AirBnB Cleaning","Sanitary Bin","Laundry & Ironing","Indoor Cleaning","Outdoor Cleaning"
    ]
  },
  carpet: {
    title: "Carpet & Upholstery",
    subtitle: "Select the item(s) you need cleaned.",
    icon: "🛋️",
    options: [
      "Couches Cleaning","Carpet Cleaning","Rugs Cleaning",
      "Mattress Cleaning","Chairs Cleaning","Stairs Carpet Cleaning"
    ]
  },
  domestic: {
    title: "Domestic Service",
    subtitle: "Tell us what type of domestic assistance you need.",
    icon: "🏠",
    options: ["Regular Domestic Cleaning","Spring Cleaning","Kitchen Deep Clean","Bathroom Sanitisation","Full House Cleaning"]
  },
  moms: {
    title: "Mom's Helper",
    subtitle: "We're here to help busy households.",
    icon: "👩‍👧",
    options: ["Childcare Support","Meal Preparation","Laundry & Ironing","School Run Assistance","General Household Help"]
  },
  elder: {
    title: "Elder Care",
    subtitle: "Compassionate support for senior family members.",
    icon: "🧓",
    options: ["Light Housekeeping","Companionship Visits","Meal Preparation","Personal Laundry","General Errands"]
  },
  pest: {
    title: "Pest Control",
    subtitle: "Safe and effective pest treatment.",
    icon: "🐛",
    options: ["Cockroach Treatment","Ant & Crawling Insects","Rodent Control","Bed Bug Treatment","General Fumigation","Mosquito Treatment"]
  }
};

// ── STATE ──
let state = {
  category: null, categoryLabel: null,
  service: null,
  seaters: null,
  mattressSize: null,
  date: null, time: null, frequency: 'Once-off',
  address: null, city: null, postal: null, proptype: null,
  fname: null, lname: null, phone: null, email: null,
  source: null, notes: null
};

let currentStep = 1;

// ── NAV DROPDOWN ──
function toggleDD(id) {
  const el = document.getElementById(id);
  const wasOpen = el.classList.contains('open');
  closeAllDD();
  if (!wasOpen) el.classList.add('open');
}

function closeAllDD() {
  document.querySelectorAll('.nav-links > li.open').forEach(l => l.classList.remove('open'));
}

document.addEventListener('click', e => {
  if (!e.target.closest('.nav-links')) closeAllDD();
});

// ── STEP NAVIGATION ──
function goToStep(n) {
  // prevent skipping steps
  if (n > currentStep + 1) return;

  // build Step 2 dynamically
  if (n === 2 && state.category) {
    buildServiceList(state.category);
  }

  currentStep = n;

  [1,2,3,4,5,'success'].forEach(s => {
    const el = document.getElementById('step-' + s);
    if (el) el.classList.add('hidden');
  });

  const active = document.getElementById('step-' + n);
  if (active) active.classList.remove('hidden');

  updateStepper(n);

  document.getElementById('booking-form')
    .scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function updateStepper(n) {
  const pct = { 1:20, 2:40, 3:60, 4:80, 5:100 };
  document.getElementById('progress-fill').style.width = (pct[n] || 100) + '%';

  for (let i = 1; i <= 5; i++) {
    const ind = document.getElementById('step-indicator-' + i);
    if (!ind) continue;

    ind.classList.remove('active','done');

    if (i < n) ind.classList.add('done');
    else if (i === n) ind.classList.add('active');
  }
}

// ── STEP 1: Category ──
function pickCategory(el) {
  document.querySelectorAll('.cat-card').forEach(c => c.classList.remove('selected'));
  el.classList.add('selected');

  state.category = el.dataset.cat;
  state.categoryLabel = SERVICES[el.dataset.cat].title;

  document.getElementById('btn-to-2').disabled = false;

  // reset dependent data
  state.service = null;
  state.seaters = null;
  state.mattressSize = null;
}

// ── STEP 2: Service ──
function buildServiceList(cat) {
  const data = SERVICES[cat];

  document.getElementById('step2-title').textContent = data.title;
  document.getElementById('step2-sub').textContent = data.subtitle;

  const list = document.getElementById('service-list');
  list.innerHTML = '';

  data.options.forEach(opt => {
    const div = document.createElement('div');
    div.className = 'service-opt';
    div.innerHTML = `<div class="opt-dot"></div><span>${opt}</span>`;
    div.onclick = () => pickService(div, opt, cat);
    list.appendChild(div);
  });

  document.getElementById('seater-wrap').classList.remove('show');
  document.getElementById('mattresses-wrap').classList.remove('show');

  document.getElementById('btn-to-3').disabled = true;
}

function pickService(el, val, cat) {
  document.querySelectorAll('.service-opt').forEach(s => s.classList.remove('selected'));
  el.classList.add('selected');

  state.service = val;
  document.getElementById('btn-to-3').disabled = false;

  const sw = document.getElementById('seater-wrap');
  const mw = document.getElementById('mattresses-wrap');

  // Couches
  if (val === 'Couches Cleaning') {
    sw.classList.add('show');
    mw.classList.remove('show');
    state.mattressSize = null;
  }
  // Mattress
  else if (val === 'Mattress Cleaning') {
    mw.classList.add('show');
    sw.classList.remove('show');
    state.seaters = null;
  }
  // Others
  else {
    sw.classList.remove('show');
    mw.classList.remove('show');
    state.seaters = null;
    state.mattressSize = null;
  }
}

// Seater selection
function pickSeater(el, n) {
  document.querySelectorAll('.seater-btn').forEach(b => b.classList.remove('active'));
  el.classList.add('active');

  state.seaters = n + ' seater' + (n > 1 ? 's' : '');
}

// Mattress selection (USE LABELS)
function pickMattresses(el, label) {
  document.querySelectorAll('.mattresses-btn').forEach(b => b.classList.remove('active'));
  el.classList.add('active');

  state.mattressSize = label;   // ✅ exact label stored
  state.seaters = null;         // optional: prevent conflict
}

// ── STEP 3: Schedule ──
const today = new Date().toISOString().split('T')[0];
document.getElementById('f-date').min = today;
document.getElementById('f-date').value = today;

function pickFreq(el, val) {
  document.querySelectorAll('.freq-opt').forEach(f => f.classList.remove('selected'));
  el.classList.add('selected');

  state.frequency = val;
}

function validateStep3() {
  const date = document.getElementById('f-date').value;
  const time = document.getElementById('f-time').value;
  const addr = document.getElementById('f-address').value.trim();
  const city = document.getElementById('f-city').value.trim();

  if (!date || !time || !addr || !city) {
    alert('Please fill all required fields.');
    return;
  }

  state.date = date;
  state.time = time;
  state.address = addr;
  state.city = city;
  state.postal = document.getElementById('f-postal').value.trim();
  state.proptype = document.getElementById('f-proptype').value;

  goToStep(4);
}

// ── STEP 4: Contact ──
function validateStep4() {
  const fname = document.getElementById('f-fname').value.trim();
  const lname = document.getElementById('f-lname').value.trim();
  const phone = document.getElementById('f-phone').value.trim();

  if (!fname || !lname || !phone) {
    alert('Fill required fields.');
    return;
  }

  state.fname = fname;
  state.lname = lname;
  state.phone = phone;
  state.email = document.getElementById('f-email').value.trim();
  state.notes = document.getElementById('f-notes').value.trim();

  buildSummary();
  goToStep(5);
}

// ── STEP 5: Summary ──
function buildSummary() {
  let extra = '';

if (state.seaters) {
  extra = ` (${state.seaters})`;
} else if (state.mattressSize) {
  extra = ` (${state.mattressSize})`;
}
  const rows = [
    ['Service Category', state.categoryLabel],
    ['Service', state.service + extra],
    ['Date', formatDate(state.date)],
    ['Time', formatTime(state.time)],
    ['Frequency', state.frequency],
    ['Address', [state.address, state.city, state.postal].filter(Boolean).join(', ')],
    ['Property Type', state.proptype || '—'],
    ['Full Name', [state.fname, state.lname].join(' ')],
    ['Phone', state.phone],
    ['Email', state.email || '—'],
    ['Notes', state.notes || '—']
  ];

  document.getElementById('summary-block').innerHTML =
    rows.map(([k,v]) =>
      `<div class="summary-row">
        <span class="summary-key">${k}</span>
        <span class="summary-val">${v}</span>
      </div>`
    ).join('');
}

// SAFE FORMATTERS
function formatDate(d) {
  if (!d) return '—';
  const parts = d.split('-');
  if (parts.length !== 3) return '—';
  return `${parts[2]}/${parts[1]}/${parts[0]}`;
}

function formatTime(t) {
  if (!t) return '—';
  const [h, m] = t.split(':');
  const hr = parseInt(h);
  if (isNaN(hr)) return '—';
  return `${hr > 12 ? hr - 12 : hr}:${m} ${hr >= 12 ? 'PM' : 'AM'}`;
}

// ── SUBMIT ──
function submitBooking() {
  const ref = 'SFN-' + Math.floor(100000 + Math.random() * 900000);

  document.getElementById('ref-num').textContent = 'Ref: ' + ref;

  document.querySelectorAll('.card').forEach(c => c.classList.add('hidden'));
  document.getElementById('step-success').classList.remove('hidden');

  document.getElementById('progress-fill').style.width = '100%';
}

// ── RESET ──
function resetForm() {
  location.reload(); // simplest and cleanest reset
}