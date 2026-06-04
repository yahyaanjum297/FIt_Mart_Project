/* ══ SHARED NAV INJECTOR v2.0 ══
   Injects nav, cursor, grain layer, grid, and toast container.
   Loaded first so cursor appears immediately.
══ */
(function(){
  const path  = window.location.pathname.split('/').pop() || 'index.html';
  const user  = (function(){ try { const d=localStorage.getItem('fm_user'); return d?JSON.parse(d):null; } catch{ return null; } })();

  const links = [
    { href:'index.html',         label:'Home'       },
    { href:'gym.html',           label:'Gym'        },
    { href:'healthcare.html',    label:'Health Care' },
    { href:'bmi-calculator.html',label:'BMI'        },
    { href:'plans.html',         label:'Plans'      },
    { href:'contact.html',       label:'Contact'    },
  ];

  const rightHtml = user
    ? `<a class="btn-ghost btn-sm" href="dashboard.html">Dashboard</a>
       <button class="btn-volt btn-sm" onclick="window.FM&&FM.logout()">Logout</button>`
    : `<a class="btn-ghost btn-sm" href="auth-login.html">Login</a>
       <a class="btn-volt btn-sm" href="auth-register.html">Get Started</a>`;

  const navHtml = `
    <div class="grain-layer" aria-hidden="true"></div>
    <div class="global-grid" aria-hidden="true"></div>
    <div id="cur"   aria-hidden="true"></div>
    <div id="cring" aria-hidden="true"></div>
    <div class="toast-wrap" id="toastWrap" aria-live="polite" role="status"></div>
    <nav class="nav" id="nav" role="navigation" aria-label="Main navigation">
      <a class="nav-brand" href="index.html" aria-label="FitMart Home">
        <div class="n-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/>
            <line x1="4" y1="22" x2="4" y2="15"/>
          </svg>
        </div>
        FitMart
      </a>
      <div class="nav-center" role="menubar">
        ${links.map(l =>
          `<a class="nav-a${l.href === path ? ' on' : ''}" href="${l.href}" role="menuitem">${l.label}</a>`
        ).join('')}
      </div>
      <div class="nav-right">
        ${rightHtml}
      </div>
    </nav>`;

  document.body.insertAdjacentHTML('afterbegin', navHtml);
})();
