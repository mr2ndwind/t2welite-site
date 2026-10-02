/* T2W Elite portal: login, password reset, and role-aware home.
   Talks to Supabase Auth with the PUBLIC publishable key. All data access is protected by
   row-level security in the database, never by this page. See supabase/README.md. */
(function () {
  'use strict';
  var app = document.getElementById('portal-app');
  if (!app) return;
  var cfg = window.T2W_SUPABASE;
  if (!cfg || !window.supabase) {
    app.textContent = 'The portal could not load. Please refresh, or call (918) 918-3234.';
    return;
  }
  var page = app.getAttribute('data-page');
  var sb = window.supabase.createClient(cfg.url, cfg.key);
  var LOGIN = new URL('../login/', location.href).href;
  var HOME = new URL('../home/', location.href).href;
  var RESET = new URL('../reset/', location.href).href;

  function $(id) { return document.getElementById(id); }
  function el(tag, props, kids) {
    var n = document.createElement(tag);
    Object.keys(props || {}).forEach(function (k) {
      if (k === 'class') n.className = props[k];
      else if (k === 'text') n.textContent = props[k];
      else n.setAttribute(k, props[k]);
    });
    (kids || []).forEach(function (c) { n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
    return n;
  }
  function say(node, text, isErr) {
    node.hidden = false;
    node.className = 'portal-msg ' + (isErr ? 'err' : 'ok');
    node.textContent = text;
  }
  function busy(btn, on, label) { btn.disabled = on; if (label) btn.textContent = label; }

  /* ---------- LOGIN + FORGOT PASSWORD ---------- */
  function initLogin() {
    sb.auth.getSession().then(function (r) { if (r.data && r.data.session) location.replace(HOME); });
    var loginForm = $('login-form'), forgotForm = $('forgot-form'), msg = $('portal-msg');
    function toggle(showForgot) {
      loginForm.hidden = showForgot; forgotForm.hidden = !showForgot; msg.hidden = true;
    }
    $('show-forgot').addEventListener('click', function () { toggle(true); });
    $('show-login').addEventListener('click', function () { toggle(false); });

    loginForm.addEventListener('submit', function (e) {
      e.preventDefault();
      var btn = loginForm.querySelector('button[type=submit]');
      busy(btn, true, 'SIGNING IN...');
      sb.auth.signInWithPassword({ email: $('login-email').value.trim(), password: $('login-password').value })
        .then(function (res) {
          if (res.error) {
            busy(btn, false, 'LOGIN');
            say(msg, 'That email or password is not correct. If you forgot it, use "Forgot password?" below.', true);
          } else { location.replace(HOME); }
        });
    });

    forgotForm.addEventListener('submit', function (e) {
      e.preventDefault();
      var btn = forgotForm.querySelector('button[type=submit]');
      busy(btn, true, 'SENDING...');
      sb.auth.resetPasswordForEmail($('forgot-email').value.trim(), { redirectTo: RESET })
        .then(function (res) {
          busy(btn, false, 'EMAIL ME A RESET LINK');
          if (res.error && res.error.status === 429) {
            say(msg, 'Too many requests. Please wait a few minutes and try again.', true);
          } else {
            // Same message whether or not the account exists, so the form cannot be used to find accounts.
            say(msg, 'If an account exists for that email, a reset link is on its way. Check your spam folder too.', false);
          }
        });
    });
  }

  /* ---------- SET / RESET PASSWORD (also used by invite links) ---------- */
  function initReset() {
    var form = $('reset-form'), msg = $('portal-msg'), wait = $('reset-wait'), shown = false;
    function showForm() { if (shown) return; shown = true; wait.hidden = true; form.hidden = false; }
    sb.auth.onAuthStateChange(function (ev, session) { if (session) showForm(); });
    sb.auth.getSession().then(function (r) { if (r.data && r.data.session) showForm(); });
    setTimeout(function () {
      if (!shown) {
        wait.hidden = true;
        say(msg, 'This link has expired or was already used. Request a new one from the login page.', true);
        $('reset-back').hidden = false;
      }
    }, 5000);
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var p1 = $('new-password').value, p2 = $('new-password2').value;
      if (p1 !== p2) { say(msg, 'The two passwords do not match.', true); return; }
      if (p1.length < 10) { say(msg, 'Use at least 10 characters.', true); return; }
      var btn = form.querySelector('button[type=submit]');
      busy(btn, true, 'SAVING...');
      sb.auth.updateUser({ password: p1 }).then(function (res) {
        if (res.error) { busy(btn, false, 'SAVE PASSWORD'); say(msg, res.error.message, true); }
        else { say(msg, 'Password saved. Taking you to your portal...', false); setTimeout(function () { location.replace(HOME); }, 1200); }
      });
    });
  }

  /* ---------- HOME (role-aware, read-only in this phase) ---------- */
  function athleteCard(a, rp) {
    var status = 'Recruiting profile: not started';
    if (rp) {
      status = (rp.guardian_approved_at && rp.visibility === 'verified_recruiters')
        ? 'Recruiting profile: visible to verified recruiters (parent approved)'
        : 'Recruiting profile: private';
    }
    var bits = [a.grad_year ? 'Class of ' + a.grad_year : null, a.position, a.school].filter(Boolean).join(' · ');
    return el('div', { class: 'card accent' }, [
      el('h3', { text: a.first_name + ' ' + a.last_name }),
      el('p', { class: 'muted', text: bits || 'Details coming soon' }),
      el('p', { text: status })
    ]);
  }
  function section(title, kids) {
    return el('div', {}, [el('h2', { text: title, style: 'margin-top:32px' })].concat(kids));
  }
  function empty(text) { return el('p', { class: 'muted', text: text }); }
  function grid(cards) { var g = el('div', { class: 'grid g2' }); cards.forEach(function (c) { g.appendChild(c); }); return g; }

  function initHome() {
    sb.auth.getSession().then(function (r) {
      var session = r.data && r.data.session;
      if (!session) { location.replace(LOGIN); return; }
      render(session.user);
    });
  }
  function render(user) {
    var out = $('home-body');
    $('signout').addEventListener('click', function () { sb.auth.signOut().then(function () { location.replace(LOGIN); }); });
    sb.from('elite_profiles').select('role,status,display_name,organization,verified_at').eq('id', user.id).maybeSingle()
      .then(function (res) {
        var p = res.data;
        if (res.error || !p) {
          out.appendChild(el('div', { class: 'card accent' }, [
            el('h3', { text: 'Your account is being set up' }),
            el('p', { text: 'You are signed in, but your T2W Elite profile is not active yet. Call or text Coach Corey at (918) 918-3234 and we will finish it.' })]));
          return;
        }
        $('home-name').textContent = p.display_name || user.email;
        $('home-role').textContent = p.role.toUpperCase();
        if (p.status !== 'active') {
          out.appendChild(el('div', { class: 'card accent' }, [
            el('h3', { text: p.status === 'pending' ? 'Awaiting approval' : 'Account on hold' }),
            el('p', { text: 'Your account is not active yet. Coach Corey will contact you, or call (918) 918-3234.' })]));
          return;
        }
        if (p.role === 'parent') return parentView(out);
        if (p.role === 'athlete') return athleteView(out, user.id);
        if (p.role === 'recruiter' || p.role === 'school') return recruiterView(out, p);
        if (p.role === 'staff') return staffView(out);
      });
  }
  function profilesByAthlete(ids) {
    if (!ids.length) return Promise.resolve({});
    return sb.from('recruiting_profiles').select('athlete_id,visibility,guardian_approved_at').in('athlete_id', ids)
      .then(function (r) { var m = {}; (r.data || []).forEach(function (x) { m[x.athlete_id] = x; }); return m; });
  }
  function parentView(out) {
    sb.from('guardian_links').select('relationship, elite_athletes(id,first_name,last_name,grad_year,position,school)')
      .then(function (r) {
        var athletes = (r.data || []).map(function (x) { return x.elite_athletes; }).filter(Boolean);
        profilesByAthlete(athletes.map(function (a) { return a.id; })).then(function (m) {
          out.appendChild(section('Your athletes', athletes.length
            ? [grid(athletes.map(function (a) { return athleteCard(a, m[a.id]); }))]
            : [empty('No athletes are linked to your account yet. Call or text Coach Corey at (918) 918-3234.')]));
          out.appendChild(section('Coming next', [empty('Recruiting profile controls, NIL disclosures, and documents will appear here as each phase launches. Nothing is shared with recruiters unless you approve it.')]));
        });
      });
  }
  function athleteView(out, uid) {
    sb.from('elite_athletes').select('id,first_name,last_name,grad_year,position,school').eq('user_id', uid)
      .then(function (r) {
        var athletes = r.data || [];
        profilesByAthlete(athletes.map(function (a) { return a.id; })).then(function (m) {
          out.appendChild(section('Your profile', athletes.length
            ? [grid(athletes.map(function (a) { return athleteCard(a, m[a.id]); }))]
            : [empty('Your athlete profile is not linked yet. Ask Coach Corey.')]));
          out.appendChild(section('Training', [el('p', {}, [
            'Workouts and assignments live in the ', el('a', { href: 'https://t2wfit.com', rel: 'noopener', text: 'T2W Fit Training App' }), '.'])]));
        });
      });
  }
  function recruiterView(out, p) {
    if (!p.verified_at) {
      out.appendChild(el('div', { class: 'card accent' }, [
        el('h3', { text: 'Verification in progress' }),
        el('p', { text: 'We confirm every recruiter and school before any athlete information is visible. Coach Corey will be in touch.' })]));
      return;
    }
    sb.from('recruiting_profiles').select('headline,elite_athletes(first_name,last_name,grad_year,position,school)')
      .then(function (r) {
        var rows = r.data || [];
        out.appendChild(section('Approved athlete profiles', rows.length
          ? [grid(rows.map(function (x) {
              var a = x.elite_athletes || {};
              var bits = [a.grad_year ? 'Class of ' + a.grad_year : null, a.position, a.school].filter(Boolean).join(' · ');
              return el('div', { class: 'card accent' }, [
                el('h3', { text: (a.first_name || '') + ' ' + (a.last_name || '') }),
                el('p', { class: 'muted', text: bits }), el('p', { text: x.headline || '' })]);
            }))]
          : [empty('No profiles have been approved for recruiters yet. Check back soon.')]));
      });
  }
  function staffView(out) {
    function count(table, filter) {
      var q = sb.from(table).select('id', { count: 'exact', head: true });
      if (filter) q = q.eq(filter[0], filter[1]);
      return q.then(function (r) { return r.count || 0; });
    }
    Promise.all([count('elite_athletes'), count('recruiter_access_requests', ['status', 'pending'])]).then(function (n) {
      out.appendChild(section('Overview', [grid([
        el('div', { class: 'card accent' }, [el('h3', { text: String(n[0]) }), el('p', { class: 'muted', text: 'Athletes' })]),
        el('div', { class: 'card accent' }, [el('h3', { text: String(n[1]) }), el('p', { class: 'muted', text: 'Recruiter requests pending' })])
      ])]));
      out.appendChild(empty('Staff tools (invites, approvals) are managed in Supabase for now and move into the portal in a later phase.'));
    });
  }

  if (page === 'login') initLogin();
  else if (page === 'reset') initReset();
  else if (page === 'home') initHome();
})();
