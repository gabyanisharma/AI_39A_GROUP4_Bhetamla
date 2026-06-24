(function () {
  const cfg = window.GROUPS_CONFIG || {};
  let selectedMeetupId = cfg.meetups && cfg.meetups.length ? cfg.meetups[0].id : null;
  let votePollTimer = null;
  let socket = null;

  function selectedMeetup() {
    return (cfg.meetups || []).find(m => m.id === selectedMeetupId);
  }

  window.selectMeetup = function (id) {
    selectedMeetupId = id;
    // Highlight the selected meetup row
    document.querySelectorAll('.meetup-row-item').forEach(el => {
      el.style.borderColor = parseInt(el.dataset.meetupId, 10) === id ? 'var(--blue)' : 'var(--border)';
    });
    // Keep the vote dropdown in sync
    const sel = document.getElementById('vote-meetup-select');
    if (sel && sel.value !== String(id)) sel.value = String(id);
    // Refresh vote panel for the selected meetup
    refreshVotePanel();
  };

  async function refreshVotePanel() {
    if (!selectedMeetupId) return;
    const res = await fetch(`/meetup/${selectedMeetupId}/vote/results`);
    const data = await res.json();
    const meetup = selectedMeetup();
    const organiserActions = document.getElementById('vote-organiser-actions');
    const optionsEl = document.getElementById('vote-options');
    const resultsEl = document.getElementById('vote-results');
    const badge = document.getElementById('vote-status-badge');
    const noActive = document.getElementById('vote-no-active');
    const voteActive = data.vote && data.vote.status === 'open';

    if (noActive) noActive.style.display = voteActive ? 'none' : 'block';
    if (resultsEl) resultsEl.style.display = voteActive ? 'block' : 'none';

    if (organiserActions) {
      const showStart = meetup && meetup.isOrganiser && (!data.vote || data.vote.status === 'closed');
      organiserActions.style.display = showStart ? 'block' : 'none';
    }

    if (badge) {
      if (!data.vote) badge.textContent = 'No vote yet';
      else if (data.vote.status === 'open') badge.textContent = 'Voting open';
      else badge.textContent = 'Vote closed';
    }

    optionsEl.innerHTML = '';
    if (data.vote && data.vote.status === 'open' && data.results) {
      data.results.forEach(opt => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn-sec';
        btn.style.cssText = 'width:100%;justify-content:flex-start;padding:10px 14px;font-size:12px';
        btn.textContent = `${opt.label} (${opt.vote_count} votes)`;
        if (data.my_vote === opt.id) btn.style.borderColor = 'var(--blue)';
        btn.onclick = () => castVote(opt.id);
        optionsEl.appendChild(btn);
      });
    }

    if (resultsEl && data.results && data.results.length) {
      const total = data.results.reduce((s, o) => s + (o.vote_count || 0), 0) || 1;
      resultsEl.innerHTML = data.results.map(opt => {
        const pct = Math.round((opt.vote_count || 0) / total * 100);
        const safeLabel = escapeChatHtml(opt.label || '');
        return `<div style="margin-bottom:8px">
          <div style="display:flex;justify-content:space-between;font-size:12px;font-weight:600"><span>${safeLabel}</span><span>${opt.vote_count || 0} (${pct}%)</span></div>
          <div style="height:6px;background:var(--border);border-radius:3px;margin-top:4px;overflow:hidden">
            <div style="height:100%;width:${pct}%;background:var(--blue);border-radius:3px"></div>
          </div>
        </div>`;
      }).join('');
    }

    if (data.vote && data.vote.status === 'open') {
      clearInterval(votePollTimer);
      votePollTimer = setInterval(refreshVotePanel, 5000);
    }
  }

  window.startVote = async function () {
    if (!selectedMeetupId) return;
    const res = await fetch(`/meetup/${selectedMeetupId}/vote/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });
    const data = await res.json();
    if (data.success) {
      if (typeof showToast === 'function') showToast('🗳️ Vote started — 24h deadline');
      refreshVotePanel();
    } else if (typeof showToast === 'function') {
      showToast(data.message || 'Could not start vote');
    }
  };

  async function castVote(optionId) {
    const res = await fetch(`/meetup/${selectedMeetupId}/vote/cast`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ option_id: optionId })
    });
    const data = await res.json();
    if (data.success) {
      refreshVotePanel();
    } else if (typeof showToast === 'function') {
      showToast(data.message || 'Could not cast vote.');
    } else {
      alert(data.message || 'Could not cast vote.');
    }
  }

  window.recordBudgetSplit = async function () {
    if (!selectedMeetupId) {
      alert("Please select a meetup first!");
      return;
    }
    try {
      const res = await fetch(`/meetup/budget-split/${selectedMeetupId}/record`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await res.json();
      
      if (typeof showToast === 'function') {
        showToast('💰 Budget split recorded — Penny Pincher unlocked!');
      } else {
        alert('Budget split recorded! "Penny Pincher" achievement unlocked.');
      }
      
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } catch (error) {
      console.error('Error recording budget split:', error);
    }
  };

  function initChat() {
    if (!cfg.chatGroupId) {
      // No chat group — show error in chat box
      const box = document.getElementById('chat-messages');
      if (box) box.innerHTML = '<div style="text-align:center;color:var(--muted);font-size:12px;padding:20px 0">Chat room unavailable. Try refreshing.</div>';
      return;
    }
    if (typeof io === 'undefined') {
      loadChatMessages();
      if (!window.chatPollTimer) {
        window.chatPollTimer = setInterval(loadChatMessages, 5000);
      }
      return;
    }

    socket = io({ withCredentials: true, transports: ['websocket', 'polling'] });
    loadChatMessages();

    // Wait for connection before joining the room
    socket.on('connect', () => {
      socket.emit('join_group', { group_id: cfg.chatGroupId });
      loadChatMessages();
    });

    socket.on('connect_error', (err) => {
      console.warn('Socket connect error:', err);
      // Fall back to polling-only load
      loadChatMessages();
      if (!window.chatPollTimer) {
        window.chatPollTimer = setInterval(() => {
          if (!socket || !socket.connected) loadChatMessages();
        }, 5000);
      }
    });

    socket.on('new_message', msg => {
      appendChatMessage(msg);
      if (socket && msg.id && Number(msg.user_id) !== Number(cfg.currentUserId)) {
        socket.emit('mark_read', { message_id: msg.id, group_id: cfg.chatGroupId });
      }
    });
    socket.on('all_read', data => {
      if (Number(data.user_id) !== Number(cfg.currentUserId)) return;
      document.querySelectorAll('#chat-messages .chat-message-row').forEach(el => {
        const meta = el.querySelector('.chat-message-meta');
        if (meta && !meta.textContent.includes('seen')) {
          meta.textContent += ' · seen';
        }
      });
    });
    socket.on('message_read', data => {
      const el = document.querySelector(`[data-msg-id="${data.message_id}"] .chat-message-meta`);
      if (el && !el.textContent.includes('seen')) {
        el.textContent += ' · seen 1';
      }
    });
    socket.on('user_typing', data => {
      const el = document.getElementById('chat-typing');
      if (el) el.textContent = data.full_name + ' is typing…';
      setTimeout(() => { if (el) el.textContent = ''; }, 3000);
    });
    socket.on('message_deleted', data => {
      const el = document.querySelector(`[data-msg-id="${data.message_id}"]`);
      if (el) el.textContent = '[deleted]';
    });

    const input = document.getElementById('chat-input');
    if (input) {
      input.addEventListener('input', () => {
        if (socket && socket.connected) socket.emit('typing', { group_id: cfg.chatGroupId });
      });
    }
  }

  async function loadChatMessages() {
    const box = document.getElementById('chat-messages');
    if (!box || !cfg.chatGroupId) return;
    const res = await fetch(`/meetup/chat/${cfg.chatGroupId}/messages`);
    const data = await res.json();
    if (!data.success) {
      box.innerHTML = `<div style="text-align:center;color:var(--muted);font-size:12px;padding:20px 0">${escapeChatHtml(data.message || 'Could not load messages.')}</div>`;
      return;
    }
    box.innerHTML = '';
    (data.messages || []).forEach(appendChatMessage);
    if (socket && cfg.chatGroupId) {
      socket.emit('mark_all_read', { group_id: cfg.chatGroupId });
    }
  }

  function escapeChatHtml(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function profileSnippet(msg) {
    const name = msg.full_name || 'User';
    if (msg.profile_pic && msg.profile_pic !== 'default.png') {
      return `<img class="direct-chat-avatar" src="${cfg.profileUploadBase}${escapeChatHtml(msg.profile_pic)}" alt="${escapeChatHtml(name)}" style="width:28px;height:28px;font-size:10px">`;
    }
    return `<div class="direct-chat-avatar" style="width:28px;height:28px;font-size:10px">${escapeChatHtml(name.slice(0, 2).toUpperCase())}</div>`;
  }

  function chatTime(value) {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '';
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function appendChatMessage(msg) {
    const box = document.getElementById('chat-messages');
    if (!box) return;
    const existing = msg.id ? box.querySelector(`[data-msg-id="${msg.id}"]`) : null;
    if (existing) return;
    const div = document.createElement('div');
    div.dataset.msgId = msg.id;
    const mine = Number(msg.user_id) === Number(cfg.currentUserId);
    div.className = `chat-message-row${mine ? ' mine' : ''}`;
    const readCount = (msg.read_by && msg.read_by.length) ? ` · seen ${msg.read_by.length}` : '';
    div.innerHTML =
      profileSnippet(msg) +
      `<div class="chat-message-stack">` +
        `<div class="chat-message-meta">${escapeChatHtml(mine ? 'You' : (msg.full_name || cfg.chatTitle || 'User'))}${chatTime(msg.created_at) ? ' - ' + escapeChatHtml(chatTime(msg.created_at)) : ''}${readCount}</div>` +
        `<div class="chat-bubble">${escapeChatHtml(msg.body)}</div>` +
        `<button type="button" class="chat-translate-btn">Translate</button>` +
        `<div class="chat-translation" data-loaded="0" style="display:none;font-size:12px;color:var(--muted);margin-top:2px;padding-left:8px;border-left:2px solid var(--border)"></div>` +
      `</div>`;
    const btn = div.querySelector('.chat-translate-btn');
    if (btn) btn.addEventListener('click', () => translateChatMessage(btn, msg.body || ''));
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
  }

  // US17 — translate a chat message into the user's preferred language.
  // Original text stays visible; the translation shows beneath it.
  function translateChatMessage(btn, text) {
    const wrap = btn.closest('[data-msg-id]');
    const slot = wrap ? wrap.querySelector('.chat-translation') : null;
    if (!slot || !text.trim()) return;

    if (slot.dataset.loaded === '1') {        // toggle off
      slot.style.display = 'none';
      slot.dataset.loaded = '0';
      btn.textContent = 'Translate';
      return;
    }

    btn.textContent = 'Translating…';
    fetch('/meetup/chat/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
      body: JSON.stringify({ text: text })
    })
      .then(r => r.json())
      .then(d => {
        if (d && d.success) {
          slot.textContent = '🌐 ' + d.translated;
          slot.style.display = 'block';
          slot.dataset.loaded = '1';
          btn.textContent = 'Hide';
        } else {
          btn.textContent = 'Translate';
          if (typeof showToast === 'function') showToast((d && d.message) || 'Translation failed.');
        }
      })
      .catch(() => {
        btn.textContent = 'Translate';
        if (typeof showToast === 'function') showToast('Translation failed.');
      });
  }

  window.sendChatMessage = function () {
    const input = document.getElementById('chat-input');
    if (!input || !input.value.trim()) return;
    const body = input.value.trim();
    input.value = '';

    fetch(`/meetup/chat/${cfg.chatGroupId}/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
      body: JSON.stringify({ body: body })
    })
    .then(r => r.json())
    .then(d => {
      if (d && d.success) {
        if (d.message) appendChatMessage(d.message);
        else loadChatMessages();
      } else {
        input.value = body;
        if (typeof showToast === 'function') showToast((d && d.message) || 'Could not send message. Try refreshing.');
      }
    })
    .catch(() => {
      input.value = body;
      if (typeof showToast === 'function') showToast('Could not send message. Check your connection.');
    });
  };

  document.addEventListener('DOMContentLoaded', () => {
    // Auto-select first meetup for voting
    if (selectedMeetupId) {
      selectMeetup(selectedMeetupId);
      const sel = document.getElementById('vote-meetup-select');
      if (sel) sel.value = String(selectedMeetupId);
    }
    initChat();
  });

  // ── Collapsible vote panel ────────────────────────────────────────
  window.toggleVotePanel = function () {
    const body = document.getElementById('vote-body');
    const icon = document.getElementById('vote-collapse-icon');
    if (!body) return;
    const isHidden = body.style.display === 'none';
    body.style.display = isHidden ? 'block' : 'none';
    if (icon) icon.style.transform = isHidden ? 'rotate(0deg)' : 'rotate(-90deg)';
  };
})();
