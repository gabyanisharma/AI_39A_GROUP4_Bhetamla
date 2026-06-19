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
    document.querySelectorAll('.meetup-row-item').forEach(el => {
      el.style.borderColor = parseInt(el.dataset.meetupId, 10) === id ? 'var(--blue)' : 'var(--border)';
    });
    refreshVotePanel();
    refreshGallery();
    const form = document.getElementById('gallery-upload-form');
    if (form) form.style.display = id ? 'block' : 'none';
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

  async function refreshGallery() {
    if (!selectedMeetupId) return;
    const grid = document.getElementById('gallery-grid');
    if (!grid) return;
    const res = await fetch(`/meetup/${selectedMeetupId}/gallery/list`);
    if (!res.ok) {
      grid.innerHTML = '<div class="gallery-placeholder" style="grid-column:span 3;text-align:center;padding:30px;color:var(--muted)">Select a meetup to view gallery</div>';
      return;
    }
    const data = await res.json();
    const photos = data.photos || [];
    if (!photos.length) {
      grid.innerHTML = '';
      for (let i = 0; i < 3; i++) {
        grid.innerHTML += '<div class="gallery-placeholder" style="height:120px;border-radius:10px;background:var(--input-bg);display:flex;align-items:center;justify-content:center;font-size:28px;color:var(--muted)">📷</div>';
      }
      return;
    }
    grid.innerHTML = photos.map(p => `
      <div style="position:relative;border-radius:10px;overflow:hidden;height:120px;background:var(--input-bg)">
        <img src="${p.url}" alt="" style="width:100%;height:100%;object-fit:cover">
        <div style="position:absolute;bottom:0;left:0;right:0;background:rgba(0,0,0,.6);color:#fff;font-size:9px;padding:4px 6px">
          ❤️ ${p.like_count} · 💬 ${p.comment_count} · ${p.is_public ? '🌐' : '🔒'}
        </div>
        ${p.user_id === cfg.currentUserId ? `<button onclick="deletePhoto(${p.id})" style="position:absolute;top:4px;right:4px;background:rgba(0,0,0,.5);color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:10px;padding:2px 6px">✕</button>` : ''}
        ${p.user_id === cfg.currentUserId ? `<button onclick="togglePhotoPrivacy(${p.id}, ${p.is_public})" style="position:absolute;bottom:4px;right:4px;background:rgba(0,0,0,.5);color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:9px;padding:2px 5px">${p.is_public ? 'Public' : 'Private'}</button>` : ''}
        <button onclick="likePhoto(${p.id})" style="position:absolute;top:4px;left:4px;background:rgba(0,0,0,.5);color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:10px;padding:2px 6px">♥</button>
        <button onclick="commentPhoto(${p.id})" style="position:absolute;top:4px;left:28px;background:rgba(0,0,0,.5);color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:10px;padding:2px 6px">💬</button>
      </div>
    `).join('');
  }

  window.uploadGallery = async function (e) {
    e.preventDefault();
    const form = e.target;
    const fd = new FormData(form);
    if (!fd.get('is_public')) fd.append('is_public', '0');
    const res = await fetch(`/meetup/${selectedMeetupId}/gallery/upload`, { method: 'POST', body: fd });
    const data = await res.json();
    if (data.success) {
      form.reset();
      refreshGallery();
      if (typeof showToast === 'function') showToast('📸 Photo uploaded');
    } else if (typeof showToast === 'function') showToast(data.message || 'Upload failed');
    return false;
  };

  window.deletePhoto = async function (id) {
    if (!confirm('Delete your photo?')) return;
    await fetch(`/meetup/gallery/${id}/delete`, { method: 'POST' });
    refreshGallery();
  };

  window.likePhoto = async function (id) {
    await fetch(`/meetup/gallery/${id}/like`, { method: 'POST' });
    refreshGallery();
  };

  window.commentPhoto = async function (id) {
    const text = prompt('Add a comment:');
    if (!text || !text.trim()) return;
    await fetch(`/meetup/gallery/${id}/comment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ comment: text.trim() })
    });
    refreshGallery();
  };

  window.togglePhotoPrivacy = async function (id, isPublic) {
    await fetch(`/meetup/gallery/${id}/privacy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_public: !isPublic })
    });
    refreshGallery();
  };

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
    if (!cfg.chatGroupId || typeof io === 'undefined') return;
    socket = io({ withCredentials: true });
    socket.emit('join_group', { group_id: cfg.chatGroupId });

    loadChatMessages();

    socket.on('new_message', msg => appendChatMessage(msg));
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
        socket.emit('typing', { group_id: cfg.chatGroupId });
      });
    }
  }

  async function loadChatMessages() {
    const box = document.getElementById('chat-messages');
    if (!box || !cfg.chatGroupId) return;
    const res = await fetch(`/meetup/chat/${cfg.chatGroupId}/messages`);
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
    div.innerHTML =
      `<strong>${escapeChatHtml(msg.full_name || 'User')}</strong>: ` +
      `<span class="chat-body">${escapeChatHtml(msg.body)}</span>` +
      `<span style="color:var(--muted);font-size:10px">${readCount}</span> ` +
      `<button type="button" class="chat-translate-btn" style="background:none;border:none;color:var(--blue);font-size:10px;cursor:pointer;padding:0">Translate</button>` +
      `<div class="chat-translation" data-loaded="0" style="display:none;font-size:12px;color:var(--muted);margin-top:2px;padding-left:8px;border-left:2px solid var(--border)"></div>`;
    const btn = div.querySelector('.chat-translate-btn');
    if (btn) btn.addEventListener('click', () => translateChatMessage(btn, msg.body || ''));
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
    if (socket && msg.id) {
      socket.emit('mark_read', { message_id: msg.id, group_id: cfg.chatGroupId });
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

  window.sendChatMessage = function () {
    const input = document.getElementById('chat-input');
    if (!input || !socket || !input.value.trim()) return;
    socket.emit('send_message', { group_id: cfg.chatGroupId, body: input.value.trim() });
    input.value = '';
  };

  document.addEventListener('DOMContentLoaded', () => {
    if (selectedMeetupId) selectMeetup(selectedMeetupId);
    initChat();
  });
})();