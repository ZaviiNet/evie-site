/* Den — prototype behaviour.
   NON-FUNCTIONAL: no backend, no network calls, nothing persisted except a role hint
   in localStorage so the preview can look different as Zavii vs GT.
   Everything here exists to make the *feel* judgeable. */

(function () {
  'use strict';

  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  /* ---------- role preview (login page + everywhere) ---------- */
  window.denRole = () => localStorage.getItem('den-role') || 'zavii';
  window.setDenRole = (role) => {
    localStorage.setItem('den-role', role);
    location.href = role === 'gt' ? 'room.html' : 'room.html';
  };

  document.addEventListener('DOMContentLoaded', () => {
    const role = window.denRole();
    const banner = $('#role-indicator');
    if (banner) banner.textContent = role === 'gt' ? 'GT (guest)' : 'Zavii (owner)';

    // mark the current page in the nav
    const here = location.pathname.split('/').pop() || 'index.html';
    $$('.nav-links a').forEach((a) => {
      if (a.getAttribute('href') === here) a.classList.add('active');
    });
  });

  /* ---------- command palette ---------- */
  const COMMANDS = [
    { cmd: '/new', desc: 'start a fresh agent session (my context resets)', ownerOnly: false },
    { cmd: '/clear', desc: 'clear the visible transcript', ownerOnly: false },
    { cmd: '/plan', desc: 'ask Evie for a proposed plan', ownerOnly: false },
    { cmd: '/export', desc: 'download transcript + artifacts', ownerOnly: false },
    { cmd: '/status', desc: 'who is here, session id, spend so far', ownerOnly: false },
    { cmd: '/stop', desc: 'cancel the in-flight run (owner only)', ownerOnly: true },
  ];

  function buildPalette() {
    if ($('#palette')) return;
    const wrap = document.createElement('div');
    wrap.className = 'palette';
    wrap.id = 'palette';
    wrap.innerHTML = `<div class="palette-inner">
      <div class="palette-item" style="cursor:default"><strong>Commands</strong><span class="muted small">Esc to close</span></div>
      ${COMMANDS.map((c) => `<div class="palette-item" data-cmd="${c.cmd}">
          <span class="mono">${c.cmd}</span>
          <span class="muted small">${c.desc}${c.ownerOnly ? ' · owner only' : ''}</span>
        </div>`).join('')}
    </div>`;
    document.body.appendChild(wrap);
    wrap.addEventListener('click', (e) => {
      const item = e.target.closest('.palette-item[data-cmd]');
      if (item) insertCommand(item.dataset.cmd);
      wrap.classList.remove('open');
    });
  }

  function commandAllowed(cmd) {
    const c = COMMANDS.find((x) => x.cmd === cmd);
    if (!c) return true;
    if (c.ownerOnly && window.denRole() === 'gt') return false;
    return true;
  }

  function insertCommand(cmd) {
    const box = $('#composer-input');
    if (box) { box.value = cmd + ' '; box.focus(); }
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { const p = $('#palette'); if (p) p.classList.remove('open'); }
  });

  /* ---------- the room ---------- */
  function esc(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // highlight @evie / @neuro mentions
  function withMentions(text) {
    return esc(text).replace(/@(evie|neuro)\b/gi, (m) => `<span class="mention">${m}</span>`);
  }

  const who = (role) => (role === 'zavii'
    ? { name: 'Zavii', cls: 'msg-owner', initial: 'Z' }
    : role === 'gt'
      ? { name: 'GT', cls: 'msg-guest', initial: 'G' }
      : { name: 'Evie', cls: 'msg-agent', initial: 'E' });

  function appendMessage(role, text, opts) {
    const list = $('#transcript');
    if (!list) return;
    const w = who(role);
    const el = document.createElement('div');
    el.className = `msg ${w.cls}`;
    const files = (opts && opts.files) || [];
    el.innerHTML = `
      <div class="avatar">${w.initial}</div>
      <div>
        <div class="msg-head"><span class="msg-name">${w.name}</span><span class="msg-time">${new Date().toUTCString().slice(17, 22)}</span></div>
        <div class="msg-body">${withMentions(text)}</div>
        ${files.map((f) => `<div style="margin-top:.35rem"><span class="file-chip">📎 ${esc(f)} <span class="muted">· uploaded by ${w.name.toLowerCase()}</span></span></div>`).join('')}
      </div>`;
    list.appendChild(el);
    list.scrollTop = list.scrollHeight;
  }

  function appendSystem(text) {
    const list = $('#transcript');
    if (!list) return;
    const el = document.createElement('div');
    el.className = 'msg msg-system';
    el.innerHTML = `<div class="body">${esc(text)}</div>`;
    list.appendChild(el);
    list.scrollTop = list.scrollHeight;
  }

  const REPLIES = {
    default: "Here's where I'd answer — read the transcript, use the recent messages as context, and reply only because I was mentioned.",
    plan: "Proposed plan: 1) agree the room's job in one sentence, 2) list what we can reuse before we build, 3) two stages with a test each. Say which part you want me to go deeper on.",
    session: "Fresh session started — my own context is empty again, but the room transcript is still here and still gets handed to me as context.",
  };

  function fakeReply(text) {
    const typing = $('#typing');
    if (typing) typing.style.display = 'flex';
    setTimeout(() => {
      if (typing) typing.style.display = 'none';
      if (/^\/plan/.test(text)) return appendMessage('evie', REPLIES.plan);
      if (/^\/new/.test(text)) { appendSystem('/new — fresh agent session started by ' + who(window.denRole()).name); return appendMessage('evie', REPLIES.session); }
      if (/^\/clear/.test(text)) { $$('#transcript .msg').forEach((m) => { if (!m.classList.contains('msg-system')) m.remove(); }); return appendSystem('/clear — visible transcript cleared (my session memory is untouched)'); }
      if (/^\/stop/.test(text)) {
        if (window.denRole() === 'gt') return appendSystem('Refused: /stop is owner-only. Rejected at the server, not by me.');
        return appendSystem('/stop — in-flight run aborted (the real one calls sessions.abort with the runId)');
      }
      if (/^\/status/.test(text)) return appendMessage('evie', 'Session: hook:tavern-pixel · queue mode: followup · spend today: £0.00 (prototype)');
      return appendMessage('evie', REPLIES.default);
    }, 900);
  }

  window.denSend = function () {
    const box = $('#composer-input');
    if (!box) return;
    const text = box.value.trim();
    if (!text) return;

    // A command the guest is not allowed to run: refuse it at the "server" layer, visibly.
    const cmd = (text.match(/^\/\w+/) || [])[0];
    if (cmd && !commandAllowed(cmd)) {
      box.value = '';
      return appendSystem(`Refused: ${cmd} is owner-only — rejected before it ever reached the model.`);
    }

    appendMessage(window.denRole(), text);
    box.value = '';
    updateContextMeter();

    // only a mention (or a command) gets a reply — this is the whole mechanic
    if (/@(evie|neuro)\b/i.test(text) || text.startsWith('/')) fakeReply(text);
  };

  function updateContextMeter() {
    const meter = $('#context-meter');
    const label = $('#context-label');
    if (!meter) return;
    const n = $$('#transcript .msg:not(.msg-system)').length;
    const pct = Math.min(100, Math.round((n / 50) * 100));
    meter.querySelector('i').style.width = pct + '%';
    if (label) label.textContent = `${n} of 50 messages in window`;
  }

  /* ---------- composer wiring ---------- */
  document.addEventListener('DOMContentLoaded', () => {
    const box = $('#composer-input');
    if (box) {
      box.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); window.denSend(); }
      });
      box.addEventListener('input', () => {
        if (box.value === '/') { buildPalette(); $('#palette').classList.add('open'); }
      });
    }
    $$('[data-cmd]').forEach((b) => b.addEventListener('click', () => insertCommand(b.dataset.cmd)));
    $$('[data-send]').forEach((b) => b.addEventListener('click', () => window.denSend()));
    $$('[data-attach]').forEach((b) => b.addEventListener('click', () => {
      appendSystem('File picker would open here — uploaded files are staged (≤16 MiB, private 24 h) and the path is attached to the message for Evie to open.');
    }));
    $$('[data-danger]').forEach((b) => b.addEventListener('click', () => appendSystem('Kill switch: this is where the out-of-band emergency stop lives.')));
    updateContextMeter();
  });
})();
