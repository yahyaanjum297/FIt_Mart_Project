/* ══════════════════════════════════════════
   FITMART — app.js v3.0  (Fixed & Production Ready)
   Cursor · Nav · Reveal · Toast · LocalStorage · AI · Backend Sync
══════════════════════════════════════════ */

/* ══ CUSTOM CURSOR (fixed for all browsers) ══ */
(function initCursor(){
  function setup() {
    const cur   = document.getElementById('cur');
    const cring = document.getElementById('cring');
    if (!cur || !cring) return false;


  let mx = window.innerWidth/2, my = window.innerHeight/2;
  let rx = mx, ry = my;
  let raf;

  // Set initial position to avoid flash at top-left
  cur.style.left = mx + 'px';
  cur.style.top  = my + 'px';
  cring.style.left = rx + 'px';
  cring.style.top  = ry + 'px';

  document.addEventListener('mousemove', e => {
    mx = e.clientX;
    my = e.clientY;
    cur.style.left = mx + 'px';
    cur.style.top  = my + 'px';
  });

  function loop() {
    rx += (mx - rx) * 0.12;
    ry += (my - ry) * 0.12;
    cring.style.left = rx + 'px';
    cring.style.top  = ry + 'px';
    raf = requestAnimationFrame(loop);
  }
  loop();

  // Hover state — attach to existing + future elements via delegation
  function addHover(el) {
    el.addEventListener('mouseenter', () => document.body.classList.add('hovering'));
    el.addEventListener('mouseleave', () => document.body.classList.remove('hovering'));
  }

  document.querySelectorAll(
    'a, button, input, select, textarea, .card, .clickable, [onclick], label[for]'
  ).forEach(addHover);

  // Watch for dynamically added elements
  const mutObs = new MutationObserver(muts => {
    muts.forEach(m => m.addedNodes.forEach(node => {
      if (node.nodeType !== 1) return;
      const sel = 'a, button, input, select, textarea, .card, .clickable, [onclick]';
      if (node.matches && node.matches(sel)) addHover(node);
      node.querySelectorAll && node.querySelectorAll(sel).forEach(addHover);
    }));
  });
  mutObs.observe(document.body, { childList: true, subtree: true });

  // Hide cursor on touch devices
  if ('ontouchstart' in window) {
    cur.style.display   = 'none';
    cring.style.display = 'none';
    document.body.style.cursor = 'auto';
    cancelAnimationFrame(raf);
  }
    return true;
  }
  // Run immediately (works when elements are in HTML)
  // or after DOM ready (works when injected by nav.js)
  if (!setup()) {
    document.addEventListener('DOMContentLoaded', setup);
  }
})();

/* ══ NAV SCROLL ══ */
(function(){
  const nav = document.getElementById('nav');
  if (!nav) return;
  const stuck = () => nav.classList.toggle('stuck', window.scrollY > 60);
  window.addEventListener('scroll', stuck, { passive: true });
  stuck();

  // Active nav link detection
  const page = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-a').forEach(a => {
    const href = a.getAttribute('href') || '';
    if (href === page || href === './' + page) a.classList.add('on');
  });
})();

/* ══ SCROLL REVEAL ══ */
(function(){
  if (!('IntersectionObserver' in window)) {
    document.querySelectorAll('.rv,.rv-l,.rv-r,.rv-s').forEach(el => el.classList.add('in'));
    return;
  }
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('in');
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.06, rootMargin: '0px 0px -30px 0px' });
  document.querySelectorAll('.rv,.rv-l,.rv-r,.rv-s').forEach(el => obs.observe(el));
})();

/* ══ COUNTER ANIMATION ══ */
(function(){
  if (!('IntersectionObserver' in window)) return;
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (!e.isIntersecting) return;
      const el     = e.target;
      const target = +el.dataset.target;
      const suffix = el.dataset.suffix || '';
      const isK    = target > 999;
      const disp   = isK ? Math.round(target / 1000) : target;
      const s      = isK ? 'K+' : suffix;
      let v = 0, dur = 1800, steps = dur / 16;
      const t = setInterval(() => {
        v += disp / steps;
        if (v >= disp) { v = disp; clearInterval(t); }
        el.textContent = Math.round(v) + s;
      }, 16);
      obs.unobserve(el);
    });
  }, { threshold: 0.5 });
  document.querySelectorAll('.cnt-n[data-target]').forEach(el => obs.observe(el));
})();

/* ══ TOAST ══ */
window.FMToast = (function(){
  let wrap = null;
  function init() {
    if (wrap) return;
    wrap = document.getElementById('toastWrap') || document.createElement('div');
    wrap.className = 'toast-wrap';
    if (!wrap.parentElement) document.body.appendChild(wrap);
  }
  function show(msg, type = 'success', duration = 4000) {
    init();
    const t    = document.createElement('div');
    const icons = { success: '✓', error: '✕', info: 'ℹ', warning: '⚠' };
    t.className = 'toast';
    // Sanitize msg to prevent XSS
    const safeMsg = String(msg).replace(/</g,'&lt;').replace(/>/g,'&gt;');
    t.innerHTML = `
      <div class="toast-icon ${type}">${icons[type] || 'ℹ'}</div>
      <span class="toast-msg">${safeMsg}</span>
      <button class="toast-close" aria-label="Dismiss" onclick="this.closest('.toast').remove()">×</button>`;
    wrap.appendChild(t);
    if (duration > 0) {
      setTimeout(() => {
        t.classList.add('remove');
        setTimeout(() => t.remove(), 400);
      }, duration);
    }
    return t;
  }
  return {
    show,
    success: (m, d) => show(m, 'success', d),
    error:   (m, d) => show(m, 'error',   d),
    info:    (m, d) => show(m, 'info',    d),
    warning: (m, d) => show(m, 'warning', d),
  };
})();

/* ══ MODAL ══ */
window.FMModal = {
  open(id) {
    const m = document.getElementById(id);
    if (m) {
      m.classList.add('open');
      document.body.style.overflow = 'hidden';
      // Focus first input inside modal
      setTimeout(() => {
        const inp = m.querySelector('input, select, textarea, button');
        if (inp) inp.focus();
      }, 100);
    }
  },
  close(id) {
    const m = document.getElementById(id);
    if (m) {
      m.classList.remove('open');
      document.body.style.overflow = '';
    }
  }
};

// Close modal on overlay click
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) {
    FMModal.close(e.target.id);
  }
});

// Close modal on Escape key
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.open').forEach(m => {
      FMModal.close(m.id);
    });
  }
});

/* ══ LOCAL STORAGE (FM.*) ══ */
window.FM = {
  _key(k) { return 'fm_' + k; },
  save(k, d) { try { localStorage.setItem(this._key(k), JSON.stringify(d)); } catch(e) {} },
  load(k, def = null) {
    try {
      const d = localStorage.getItem(this._key(k));
      return d !== null ? JSON.parse(d) : def;
    } catch(e) { return def; }
  },
  remove(k) { try { localStorage.removeItem(this._key(k)); } catch(e) {} },
  clear()   { try {
    Object.keys(localStorage).filter(k => k.startsWith('fm_')).forEach(k => localStorage.removeItem(k));
  } catch(e) {} },

  setUser(u) { this.save('user', u); },
  getUser()  { return this.load('user'); },
  isLoggedIn() { return !!this.getUser(); },
  logout() {
    const keys = ['user','workouts','vitals','progress','food_log_today','bmi_history','appointments'];
    keys.forEach(k => this.remove(k));
    window.location.href = 'index.html';
  },

  addWorkout(e) {
    const l = this.load('workouts', []) || [];
    e.id   = e.id   || Date.now();
    e.date = e.date || new Date().toISOString().split('T')[0];
    l.unshift(e);
    this.save('workouts', l.slice(0, 500));
    return e;
  },
  getWorkouts() { return this.load('workouts', []) || []; },

  addVital(e) {
    const v = this.load('vitals', []) || [];
    e.id        = e.id        || Date.now();
    e.timestamp = e.timestamp || new Date().toISOString();
    v.unshift(e);
    this.save('vitals', v.slice(0, 200));
    return e;
  },
  getVitals() { return this.load('vitals', []) || []; },

  addBMI(e) {
    const b = this.load('bmi_history', []) || [];
    e.id   = e.id   || Date.now();
    e.date = e.date || new Date().toISOString().split('T')[0];
    b.unshift(e);
    this.save('bmi_history', b.slice(0, 100));
    return e;
  },
  getBMIHistory() { return this.load('bmi_history', []) || []; },
};

/* ══ CONFIG ══ */
window.FMConfig = (function(){
  const stored = () => { try { return localStorage.getItem('fm_api_key') || ''; } catch { return ''; } };
  const storedBackend = () => {
    try { return localStorage.getItem('fm_backend_url') || 'http://127.0.0.1:8000'; }
    catch { return 'http://127.0.0.1:8000'; }
  };
  return {
    getApiKey()    { return stored(); },
    setApiKey(k)   { try { localStorage.setItem('fm_api_key', k); } catch {} },
    hasApiKey()    { const k = stored(); return !!(k && k.startsWith('sk-ant-')); },
    getBackendUrl(){ return storedBackend(); },
    setBackendUrl(url) { try { localStorage.setItem('fm_backend_url', url.replace(/\/$/, '')); } catch {} },
  };
})();

/* ══ BACKEND API ══ */
window.FMAPI = {
  get BASE() { return FMConfig.getBackendUrl(); },

  async request(method, path, data, opts = {}) {
    const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
    const config  = {
      method,
      headers,
      signal: opts.signal || AbortSignal.timeout(opts.timeout || 15000),
    };
    if (data && method !== 'GET') config.body = JSON.stringify(data);

    const res = await fetch(this.BASE + path, config);
    if (!res.ok) {
      let errMsg = `HTTP ${res.status}`;
      try {
        const errData = await res.json();
        errMsg = errData.detail || errData.message || errMsg;
      } catch {
        try { errMsg = await res.text() || errMsg; } catch {}
      }
      throw new Error(errMsg);
    }
    return res.json();
  },

  async post(path, data, opts)  { return this.request('POST',   path, data, opts); },
  async get(path, opts)         { return this.request('GET',    path, null, opts); },
  async patch(path, data, opts) { return this.request('PATCH',  path, data, opts); },
  async del(path, opts)         { return this.request('DELETE', path, null, opts); },
};

/* ══ CLAUDE AI ══ */
window.FMAi = {
  async ask(prompt, max_tokens = 1000) {
    // Try backend proxy first (API key stays server-side)
    try {
      const res = await FMAPI.post('/ai/chat', { prompt, max_tokens },
        { signal: AbortSignal.timeout(30000) });
      if (res && res.text) return res.text;
    } catch (err) {
      // If 503 (not configured), fall through to direct call
      if (!String(err.message).includes('503') && !String(err.message).includes('not configured')) {
        throw err;
      }
    }
    // Direct call fallback (uses localStorage key)
    const key = FMConfig.getApiKey();
    if (!key || !key.startsWith('sk-ant-')) {
      return _aiKeyMissingMsg();
    }
    const res = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': key,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens,
        messages: [{ role: 'user', content: prompt }]
      })
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error.message);
    return data.content?.[0]?.text || '';
  }
};

function _aiKeyMissingMsg() {
  return `<p><strong>AI Key Not Configured</strong></p>
  <p style="color:var(--muted)">To enable AI-powered plans, add your Anthropic API key:</p>
  <ol style="color:var(--muted);font-size:13px;margin:8px 0;padding-left:18px;line-height:2">
    <li>Get a free key at <a href="https://console.anthropic.com" target="_blank" style="color:var(--volt)">console.anthropic.com</a></li>
    <li>Open <strong>Admin Dashboard → Settings</strong> and paste your key, OR</li>
    <li>In browser console: <code style="color:var(--volt)">FMConfig.setApiKey('sk-ant-...')</code></li>
  </ol>
  <p style="color:var(--muted);font-size:13px">A fallback plan has been generated using built-in templates.</p>`;
}

/* ══ BACKEND SYNC ══ */
window.FMSync = {
  async saveWorkout(entry) {
    const user = FM.getUser();
    FM.addWorkout(entry);
    if (!user?.id) return entry;
    try {
      const res = await FMAPI.post('/workouts/' + user.id, {
        exercise: entry.exercise, muscle: entry.muscle, date: entry.date,
        sets: entry.sets || [], duration: entry.duration,
        calories: entry.calories, notes: entry.notes
      });
      return { ...entry, serverId: res.id };
    } catch(e) {
      console.warn('[FMSync] saveWorkout offline:', e.message);
      return entry;
    }
  },

  async saveVitals(entry) {
    const user  = FM.getUser();
    const saved = FM.addVital(entry);
    if (!user?.id) return saved;
    try {
      const res = await FMAPI.post('/vitals/' + user.id, {
        heart_rate:   entry.heartRate,
        bp_systolic:  entry.bpSys,
        bp_diastolic: entry.bpDia,
        blood_sugar:  entry.sugar,
        sleep_hrs:    entry.sleep,
        steps:        entry.steps,
        spo2:         entry.spo2,
        weight:       entry.weight,
        temperature:  entry.temperature,
        notes:        entry.notes
      });
      if (res.alerts?.length) {
        res.alerts.forEach(a => FMToast.error(a, 8000));
      }
      return { ...saved, serverId: res.id };
    } catch(e) {
      console.warn('[FMSync] saveVitals offline:', e.message);
      return saved;
    }
  },

  async saveProgress(entry) {
    const user = FM.getUser();
    const prog = FM.load('progress', []) || [];
    entry.id   = entry.id || Date.now();
    prog.unshift(entry);
    FM.save('progress', prog.slice(0, 200));
    if (!user?.id) return entry;
    try {
      const res = await FMAPI.post('/progress/' + user.id, entry);
      return { ...entry, serverId: res.id };
    } catch(e) {
      console.warn('[FMSync] saveProgress offline:', e.message);
      return entry;
    }
  },

  async bookAppointment(appt) {
    const user  = FM.getUser();
    const appts = FM.load('appointments', []) || [];
    appts.push({ ...appt, id: Date.now() });
    FM.save('appointments', appts);
    if (!user?.id) return appt;
    try {
      return await FMAPI.post('/appointments/' + user.id, {
        doctor_name: appt.doctor || appt.doctor_name,
        appt_date:   appt.date   || appt.appt_date,
        appt_time:   appt.time   || appt.appt_time,
        appt_type:   appt.type   || appt.appt_type || 'In-Clinic',
        speciality:  appt.speciality,
        reason:      appt.reason
      });
    } catch(e) {
      console.warn('[FMSync] bookAppointment offline:', e.message);
      return appt;
    }
  },

  async saveFood(entry) {
    const user = FM.getUser();
    const log  = FM.load('food_log_today', []) || [];
    log.unshift({ ...entry, id: Date.now() });
    FM.save('food_log_today', log.slice(0, 200));
    if (!user?.id) return entry;
    try {
      return await FMAPI.post('/food-logs/' + user.id, {
        log_date:  entry.log_date  || entry.date || new Date().toISOString().split('T')[0],
        meal_type: entry.meal_type || entry.meal,
        food_name: entry.food_name || entry.food,
        calories:  entry.calories,
        protein_g: entry.protein_g || entry.protein,
        carbs_g:   entry.carbs_g   || entry.carbs,
        fat_g:     entry.fat_g     || entry.fat,
        fiber_g:   entry.fiber_g,
        quantity:  entry.quantity
      });
    } catch(e) {
      console.warn('[FMSync] saveFood offline:', e.message);
      return entry;
    }
  }
};

/* ══ AUTH GUARDS ══ */
window.requireLogin = function(redirect = 'auth-login.html') {
  if (!FM.isLoggedIn()) {
    FMToast.error('Please log in to continue');
    setTimeout(() => window.location.href = redirect, 1200);
    return false;
  }
  return true;
};

window.requireRole = function(role, redirect = 'dashboard.html') {
  const u = FM.getUser();
  if (!u || u.role !== role) {
    FMToast.error(role.charAt(0).toUpperCase() + role.slice(1) + ' access required');
    setTimeout(() => window.location.href = redirect, 1200);
    return false;
  }
  return true;
};

/* ══ FORMAT HELPERS ══ */
window.FMFmt = {
  date: (d) => {
    try {
      return new Date(d).toLocaleDateString('en-PK', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch { return String(d); }
  },
  time: (d) => {
    try {
      return new Date(d).toLocaleTimeString('en-PK', { hour: '2-digit', minute: '2-digit' });
    } catch { return String(d); }
  },
  relTime: (d) => {
    const diff = Date.now() - new Date(d).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1)   return 'just now';
    if (mins < 60)  return `${mins}m ago`;
    if (mins < 1440) return `${Math.floor(mins/60)}h ago`;
    return `${Math.floor(mins/1440)}d ago`;
  },
  num:  (n, dec = 1) => isNaN(+n) ? '—' : parseFloat(n).toFixed(dec),
  kcal: (n) => isNaN(+n) ? '—' : `${Number(n).toLocaleString()} kcal`,
  kg:   (n) => isNaN(+n) ? '—' : `${parseFloat(n).toFixed(1)}kg`,
  pct:  (n) => isNaN(+n) ? '—' : `${Math.round(n)}%`,
  bmi:  (w, h) => {
    if (!w || !h || h === 0) return null;
    return parseFloat((w / ((h / 100) ** 2)).toFixed(1));
  },
  bmiCategory: (bmi) => {
    if (!bmi || isNaN(bmi)) return 'Unknown';
    if (bmi < 18.5) return 'Underweight';
    if (bmi < 25.0) return 'Normal Weight';
    if (bmi < 30.0) return 'Overweight';
    return 'Obese';
  },
  bmiColor: (bmi) => {
    if (!bmi) return 'var(--muted)';
    if (bmi < 18.5 || bmi >= 30) return 'var(--coral)';
    if (bmi < 25)  return 'var(--volt)';
    return '#f59e0b';
  },
  initial: (name) => {
    if (!name) return '?';
    return name.trim().split(/\s+/).map(n => n[0]).join('').toUpperCase().slice(0, 2);
  },
};

/* ══ VALIDATION HELPERS ══ */
window.FMValidate = {
  email: (v) => /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/.test(v.trim()),
  password: (v) => v && v.length >= 8,
  name: (v) => v && v.trim().length >= 2,
  number: (v, min, max) => {
    const n = parseFloat(v);
    return !isNaN(n) && (min === undefined || n >= min) && (max === undefined || n <= max);
  },
  required: (v) => v !== null && v !== undefined && String(v).trim() !== '',
  date: (v) => /^\d{4}-\d{2}-\d{2}$/.test(v) && !isNaN(Date.parse(v)),

  form(fields) {
    // fields: [{id, type, label, min, max}]
    const errors = [];
    fields.forEach(f => {
      const el = document.getElementById(f.id);
      if (!el) return;
      const v = el.value;
      let valid = true;
      if (f.type === 'email')    valid = this.email(v);
      else if (f.type === 'password') valid = this.password(v);
      else if (f.type === 'number')  valid = this.number(v, f.min, f.max);
      else if (f.required !== false)  valid = this.required(v);
      if (!valid) {
        errors.push(f.label || f.id);
        el.style.borderColor = 'rgba(255,99,71,0.6)';
        el.style.boxShadow   = '0 0 0 3px rgba(255,99,71,0.08)';
      } else {
        el.style.borderColor = '';
        el.style.boxShadow   = '';
      }
    });
    return errors;
  },

  clearErrors(ids) {
    ids.forEach(id => {
      const el = document.getElementById(id);
      if (el) { el.style.borderColor = ''; el.style.boxShadow = ''; }
    });
  }
};

/* ══ MAGNETIC BUTTONS ══ */
(function(){
  function attachMagnetic(btn) {
    btn.addEventListener('mousemove', e => {
      const r = btn.getBoundingClientRect();
      const x = (e.clientX - r.left - r.width/2)  * 0.15;
      const y = (e.clientY - r.top  - r.height/2) * 0.15;
      btn.style.transform = `translateY(-3px) translate(${x}px,${y}px)`;
    });
    btn.addEventListener('mouseleave', () => btn.style.transform = '');
  }
  document.querySelectorAll('.btn-main, .btn-volt, .btn-teal').forEach(attachMagnetic);

  // Watch for new buttons added dynamically
  const obs = new MutationObserver(muts => {
    muts.forEach(m => m.addedNodes.forEach(node => {
      if (node.nodeType !== 1) return;
      if (node.matches && node.matches('.btn-main,.btn-volt,.btn-teal')) attachMagnetic(node);
      node.querySelectorAll && node.querySelectorAll('.btn-main,.btn-volt,.btn-teal').forEach(attachMagnetic);
    }));
  });
  obs.observe(document.body, { childList: true, subtree: true });
})();

/* ══ API KEY SETUP BANNER ══ */
(function(){
  const aiPages = ['index.html','','bmi-calculator.html','diet.html','plan.html'];
  const pg = location.pathname.split('/').pop() || '';
  if (!aiPages.includes(pg)) return;
  if (FMConfig.hasApiKey()) return;
  if (FM.load('api_banner_dismissed')) return;

  const banner = document.createElement('div');
  banner.id = 'apiBanner';
  Object.assign(banner.style, {
    position: 'fixed', bottom: '24px', left: '50%',
    transform: 'translateX(-50%)', zIndex: '9990',
    background: '#0e1c24', border: '1px solid rgba(181,255,71,.25)',
    borderRadius: '14px', padding: '14px 20px',
    display: 'flex', alignItems: 'center', gap: '16px',
    boxShadow: '0 16px 40px rgba(0,0,0,.5)',
    maxWidth: '520px', width: 'calc(100% - 48px)',
    animation: 'slideUp 0.4s cubic-bezier(0.16,1,0.3,1)'
  });
  banner.innerHTML = `
    <span style="font-size:20px">⚡</span>
    <div style="flex:1">
      <div style="font-size:13px;font-weight:600;color:#edf4f0;margin-bottom:3px">Add your Claude API key for live AI plans</div>
      <div style="font-size:12px;color:rgba(237,244,240,.5)">Browser console: <code style="color:#b5ff47;background:rgba(181,255,71,.08);padding:1px 6px;border-radius:4px">FMConfig.setApiKey('sk-ant-...')</code></div>
    </div>
    <button onclick="FM.save('api_banner_dismissed',true);document.getElementById('apiBanner').remove()"
      style="color:rgba(237,244,240,.4);font-size:18px;background:none;border:none;cursor:pointer;padding:4px"
      aria-label="Dismiss">×</button>`;
  document.body.appendChild(banner);
  setTimeout(() => { if (banner.parentElement) banner.remove(); }, 14000);
})();

/* ══ LOADING BUTTON HELPER ══ */
window.FMBtn = {
  loading(id, loadingText = 'Loading...') {
    const btn = document.getElementById(id);
    if (!btn) return;
    btn.disabled = true;
    btn._originalHTML = btn.innerHTML;
    btn.innerHTML = `<div class="spinner" style="display:inline-block"></div> ${loadingText}`;
  },
  reset(id) {
    const btn = document.getElementById(id);
    if (!btn) return;
    btn.disabled = false;
    if (btn._originalHTML) btn.innerHTML = btn._originalHTML;
  }
};

/* ══ BACKEND STATUS CHECK ══ */
window.FMStatus = {
  async check() {
    try {
      const res = await fetch(FMConfig.getBackendUrl() + '/health', {
        signal: AbortSignal.timeout(3000)
      });
      return res.ok;
    } catch { return false; }
  }
};

// Check backend on load (non-blocking)
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => FMStatus.check());
} else {
  FMStatus.check();
}
