(function () {
  const cfg = window.GROUPS_CONFIG || {};
  let selectedMeetupId = cfg.meetups && cfg.meetups.length ? cfg.meetups[0].id : null;
  let votePollTimer = null;
  let socket = null;
  let chatGroupId = null;

  function selectedMeetup() {
    return (cfg.meetups || []).find(m => m.id === selectedMeetupId);
  }

  window.selectMeetup = function (id) {
    selectedMeetupId = id;
    document.querySelectorAll('.meetup-row-item').forEach(el => {
      el.style.borderColor = parseInt(el.dataset.meetupId, 10) === id ? 'var(--blue)' : 'var(--border)';
    });
    refreshVotePanel();
    connectMeetupChat(id);
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
        return `<div style="margin-bottom:8px">
          <div style="display:flex;justify-content:space-between;font-size:12px;font-weight:600"><span>${opt.label}</span><span>${opt.vote_count || 0} (${pct}%)</span></div>
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
    if (data.success) refreshVotePanel();
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

  function initSocket() {
    if (socket || typeof io === 'undefined') return;
    socket = io({ withCredentials: true });

    socket.on('new_message', msg => {
      if (msg.group_id !== chatGroupId) return;
      appendChatMessage(msg);
      // New-message alert, unless the chat is muted or it's our own message.
      if (msg.user_id !== cfg.currentUserId && !isChatMuted() && typeof showToast === 'function') {
        showToast('💬 ' + (msg.full_name || 'New message') + ': ' + (msg.body || '').slice(0, 60));
      }
    });
    socket.on('user_typing', data => {
      if (data.group_id !== chatGroupId) return;
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
        if (chatGroupId) socket.emit('typing', { group_id: chatGroupId });
      });
    }
  }

  // Resolve the selected meetup's shared chat group, join its room and load
  // history. All accepted members of the meetup share this single room.
  async function connectMeetupChat(meetupId) {
    const emptyEl = document.getElementById('chat-empty');
    const activeEl = document.getElementById('chat-active');
    const label = document.getElementById('chat-group-label');
    if (!meetupId) {
      if (emptyEl) emptyEl.style.display = 'block';
      if (activeEl) activeEl.style.display = 'none';
      return;
    }
    let data;
    try {
      const res = await fetch(`/meetup/${meetupId}/chat/group`);
      data = await res.json();
    } catch (e) { data = { success: false }; }

    if (!data || !data.success) {
      if (emptyEl) {
        emptyEl.style.display = 'block';
        emptyEl.textContent = (data && data.message) || 'Chat unavailable for this meetup.';
      }
      if (activeEl) activeEl.style.display = 'none';
      return;
    }

    initSocket();
    if (socket && chatGroupId && chatGroupId !== data.group_id) {
      socket.emit('leave_group', { group_id: chatGroupId });
    }
    chatGroupId = data.group_id;
    if (socket) socket.emit('join_group', { group_id: chatGroupId });

    const meetup = (cfg.meetups || []).find(m => m.id === meetupId);
    if (label) label.textContent = (meetup ? meetup.title : 'Meetup') + ' · accepted members only';
    if (emptyEl) emptyEl.style.display = 'none';
    if (activeEl) activeEl.style.display = 'block';
    refreshMuteBtn();
    loadChatMessages();
  }

  async function loadChatMessages() {
    const box = document.getElementById('chat-messages');
    if (!box || !chatGroupId) return;
    const res = await fetch(`/meetup/chat/${chatGroupId}/messages`);
    const data = await res.json();
    box.innerHTML = '';
    (data.messages || []).forEach(appendChatMessage);
  }

  function escapeChatHtml(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function appendChatMessage(msg) {
    const box = document.getElementById('chat-messages');
    if (!box) return;
    const div = document.createElement('div');
    div.dataset.msgId = msg.id;
    div.style.marginBottom = '8px';
    const readCount = (msg.read_by && msg.read_by.length) ? ` · seen ${msg.read_by.length}` : '';
    const stamp = formatChatTime(msg.created_at);
    div.innerHTML =
      `<strong>${escapeChatHtml(msg.full_name || 'User')}</strong>: ` +
      `<span class="chat-body">${escapeChatHtml(msg.body)}</span>` +
      `<span style="color:var(--muted);font-size:10px">${stamp ? ' · ' + stamp : ''}${readCount}</span> ` +
      `<button type="button" class="chat-translate-btn" style="background:none;border:none;color:var(--blue);font-size:10px;cursor:pointer;padding:0">Translate</button>` +
      `<div class="chat-translation" data-loaded="0" style="display:none;font-size:12px;color:var(--muted);margin-top:2px;padding-left:8px;border-left:2px solid var(--border)"></div>`;
    const btn = div.querySelector('.chat-translate-btn');
    if (btn) btn.addEventListener('click', () => translateChatMessage(btn, msg.body || ''));
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
    if (socket && msg.id && chatGroupId) {
      socket.emit('mark_read', { message_id: msg.id, group_id: chatGroupId });
    }
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

  function formatChatTime(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    if (isNaN(d)) return '';
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  // ── Mute (client-side, per meetup) ──────────────────────────────
  function muteKey() { return 'bhetamla_chat_mute_' + selectedMeetupId; }
  function isChatMuted() { return localStorage.getItem(muteKey()) === '1'; }
  function refreshMuteBtn() {
    const btn = document.getElementById('chat-mute-btn');
    if (!btn) return;
    btn.textContent = isChatMuted() ? '🔕 Muted' : '🔔 Mute';
  }
  window.toggleChatMute = function () {
    localStorage.setItem(muteKey(), isChatMuted() ? '0' : '1');
    refreshMuteBtn();
    if (typeof showToast === 'function') showToast(isChatMuted() ? 'Chat muted' : 'Chat unmuted');
  };

  window.copyChatInvite = async function () {
    if (!selectedMeetupId) return;
    try {
      const res = await fetch(`/meetup/${selectedMeetupId}/chat/invite-link`);
      const data = await res.json();
      if (!data.success) { if (typeof showToast === 'function') showToast(data.message || 'Could not create link'); return; }
      await navigator.clipboard.writeText(data.link);
      if (typeof showToast === 'function') showToast('🔗 Invite link copied!');
      else prompt('Share this invite link:', data.link);
    } catch (e) {
      if (typeof showToast === 'function') showToast('Could not copy link');
    }
  };

  window.leaveChat = async function () {
    if (!selectedMeetupId || !confirm('Leave this chat? You can rejoin via an invite link.')) return;
    await fetch(`/meetup/${selectedMeetupId}/chat/leave`, { method: 'POST' });
    const activeEl = document.getElementById('chat-active');
    const emptyEl = document.getElementById('chat-empty');
    if (activeEl) activeEl.style.display = 'none';
    if (emptyEl) { emptyEl.style.display = 'block'; emptyEl.textContent = 'You left this chat.'; }
    if (socket && chatGroupId) socket.emit('leave_group', { group_id: chatGroupId });
    chatGroupId = null;
  };

  window.shareRestaurant = function () {
    const sel = document.getElementById('chat-share-select');
    if (!sel || !sel.value || !socket || !chatGroupId) return;
    const opt = sel.options[sel.selectedIndex];
    const name = opt.getAttribute('data-name');
    const addr = opt.getAttribute('data-addr');
    const body = `📍 How about ${name}?${addr ? ' (' + addr + ')' : ''}`;
    socket.emit('send_message', { group_id: chatGroupId, body: body });
    sel.value = '';
  };

  window.sendChatMessage = function () {
    const input = document.getElementById('chat-input');
    if (!input || !socket || !chatGroupId || !input.value.trim()) return;
    socket.emit('send_message', { group_id: chatGroupId, body: input.value.trim() });
    input.value = '';
  };

  document.addEventListener('DOMContentLoaded', () => {
    if (selectedMeetupId) selectMeetup(selectedMeetupId);
    else connectMeetupChat(null);
  });
})();
