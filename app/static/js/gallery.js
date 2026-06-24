(function () {
  const cfg = window.GALLERY_CONFIG || {};
  let currentMeetupId = cfg.meetups && cfg.meetups.length ? cfg.meetups[0].id : null;

  /* ── Helpers ─────────────────────────────────────────── */
  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function fmtDate(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    if (isNaN(d)) return '';
    return d.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });
  }

  function timeAgo(iso) {
    if (!iso) return '';
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1)  return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24)  return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    if (days < 7)  return `${days}d ago`;
    return fmtDate(iso);
  }

  function toast(msg) {
    if (typeof showToast === 'function') showToast(msg); else console.log(msg);
  }

  /* ── Photo preview before upload ─────────────────────── */
  window.previewPhoto = function (input) {
    const file = input.files && input.files[0];
    const wrap = document.getElementById('gallery-preview-wrap');
    const ph   = document.getElementById('gallery-drop-placeholder');
    const img  = document.getElementById('gallery-preview-img');
    const name = document.getElementById('gallery-preview-name');
    if (!file) { wrap.style.display = 'none'; ph.style.display = ''; return; }
    const reader = new FileReader();
    reader.onload = e => {
      img.src = e.target.result;
      name.textContent = file.name + ' · ' + (file.size / 1024 / 1024).toFixed(2) + ' MB';
      wrap.style.display = 'block';
      ph.style.display = 'none';
    };
    reader.readAsDataURL(file);
  };

  window.handleDrop = function (e) {
    e.preventDefault();
    const zone = document.getElementById('gallery-drop-zone');
    zone.style.borderColor = 'var(--border)';
    zone.style.background = 'var(--input-bg)';
    const file = e.dataTransfer.files && e.dataTransfer.files[0];
    if (!file) return;
    const inp = document.getElementById('gallery-file-input');
    const dt = new DataTransfer();
    dt.items.add(file);
    inp.files = dt.files;
    window.previewPhoto(inp);
  };

  /* ── Load gallery ─────────────────────────────────────── */
  window.loadGallery = async function (meetupId) {
    currentMeetupId = meetupId ? parseInt(meetupId, 10) : null;
    const grid  = document.getElementById('gallery-grid');
    const empty = document.getElementById('gallery-empty');
    const stats = document.getElementById('gallery-stats-bar');
    if (!grid) return;

    if (!currentMeetupId) {
      grid.innerHTML = '';
      empty.style.display = 'block';
      stats.style.display = 'none';
      return;
    }

    grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--muted)">⏳ Loading photos…</div>';

    const res = await fetch(`/meetup/${currentMeetupId}/gallery/list`);
    if (!res.ok) {
      grid.innerHTML = '';
      empty.style.display = 'block';
      return;
    }

    const data   = await res.json();
    const photos = data.photos || [];

    if (!photos.length) {
      grid.innerHTML = '';
      empty.style.display = 'block';
      stats.style.display = 'none';
      return;
    }

    empty.style.display = 'none';
    stats.style.display = 'flex';
    document.getElementById('gallery-photo-count').textContent =
      `${photos.length} photo${photos.length !== 1 ? 's' : ''}`;

    grid.innerHTML = photos.map(renderCard).join('');
  };

  /* ── Render one card ─────────────────────────────────── */
  function renderCard(p) {
    const mine    = p.user_id === cfg.currentUserId;
    const poster  = esc(p.full_name || 'Member');
    const when    = timeAgo(p.created_at);
    const whenFull = fmtDate(p.created_at);
    const initials = poster.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);

    return `
      <div class="card" data-photo-id="${p.id}"
           style="padding:0;overflow:hidden;display:flex;flex-direction:column;transition:transform .15s,box-shadow .15s"
           onmouseenter="this.style.transform='translateY(-3px)';this.style.boxShadow='0 6px 24px rgba(20,50,42,.13)'"
           onmouseleave="this.style.transform='';this.style.boxShadow=''">

        <!-- Image -->
        <div style="position:relative;height:190px;background:var(--input-bg);cursor:zoom-in;overflow:hidden"
             onclick="window.openLightbox(${p.id})">
          <img src="${esc(p.url)}" alt="${esc(p.caption)}"
               style="width:100%;height:100%;object-fit:cover;transition:transform .3s"
               onmouseenter="this.style.transform='scale(1.04)'"
               onmouseleave="this.style.transform=''">
          <span style="position:absolute;top:8px;right:8px;background:rgba(0,0,0,.52);color:#fff;font-size:10px;padding:3px 9px;border-radius:20px;backdrop-filter:blur(4px)">
            ${p.is_public ? '🌐 Public' : '🔒 Private'}
          </span>
          ${mine ? '<span style="position:absolute;top:8px;left:8px;background:rgba(26,86,219,.82);color:#fff;font-size:10px;padding:3px 9px;border-radius:20px">Yours</span>' : ''}
        </div>

        <!-- Body -->
        <div style="padding:13px 14px;display:flex;flex-direction:column;gap:8px;flex:1">

          <!-- Caption -->
          <div style="font-size:13px;font-weight:600;min-height:18px;line-height:1.4">
            ${esc(p.caption) || '<span style="color:var(--muted);font-weight:400;font-style:italic">No caption</span>'}
          </div>

          <!-- Posted by -->
          <div style="display:flex;align-items:center;gap:8px">
            <div style="width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,var(--primary),#1A56C4);color:#fff;font-size:10px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0">
              ${initials}
            </div>
            <div style="min-width:0">
              <div style="font-size:12px;font-weight:600;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${poster}</div>
              <div style="font-size:11px;color:var(--muted)" title="${whenFull}">${when}</div>
            </div>
          </div>

          <!-- Actions -->
          <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:2px">
            <button class="btn-sec" style="width:auto;padding:5px 10px;font-size:12px;${p.liked_by_me ? 'border-color:var(--red);color:var(--red)' : ''}"
                    onclick="window.toggleLike(${p.id})">
              ${p.liked_by_me ? '❤️' : '🤍'} <span data-like-count>${p.like_count}</span>
            </button>
            <button class="btn-sec" style="width:auto;padding:5px 10px;font-size:12px"
                    onclick="window.toggleComments(${p.id})">
              💬 <span data-comment-count>${p.comment_count}</span>
            </button>
            <a class="btn-sec" style="width:auto;padding:5px 10px;font-size:12px;text-decoration:none"
               href="${esc(p.url)}" download title="Download">⬇</a>
            ${mine ? `<button class="btn-sec" style="width:auto;padding:5px 10px;font-size:12px" onclick="window.togglePrivacy(${p.id}, ${p.is_public})">${p.is_public ? '🔒 Make private' : '🌐 Make public'}</button>` : ''}
            ${mine ? `<button class="btn-sec" style="width:auto;padding:5px 10px;font-size:12px;color:var(--red);border-color:var(--red)" onclick="window.deletePhoto(${p.id})">🗑</button>` : ''}
          </div>

          <!-- Comments section -->
          <div class="gallery-comments" data-comments-for="${p.id}"
               style="display:none;border-top:1px solid var(--border);padding-top:10px;margin-top:2px">
            <div class="comment-list" style="display:flex;flex-direction:column;gap:7px;margin-bottom:8px;max-height:180px;overflow-y:auto"></div>
            <div style="display:flex;gap:6px">
              <input type="text" placeholder="Add a comment…" maxlength="300"
                     style="flex:1;padding:7px 10px;border-radius:8px;border:1px solid var(--border);font-size:12px;background:var(--input-bg);color:var(--text)"
                     onkeydown="if(event.key==='Enter')window.addComment(${p.id}, this)">
              <button class="btn-primary" style="width:auto;padding:7px 12px;font-size:12px;margin-top:0"
                      onclick="window.addComment(${p.id}, this.previousElementSibling)">Send</button>
            </div>
          </div>
        </div>
      </div>`;
  }

  /* ── Upload ───────────────────────────────────────────── */
  window.uploadGallery = async function (e) {
    e.preventDefault();
    if (!currentMeetupId) { toast('Select a meetup first'); return false; }

    const form = e.target;
    const btn  = document.getElementById('gallery-upload-btn');
    const fd   = new FormData(form);
    if (!fd.get('is_public')) fd.append('is_public', '0');

    btn.disabled = true;
    btn.textContent = 'Uploading…';

    const res  = await fetch(`/meetup/${currentMeetupId}/gallery/upload`, { method: 'POST', body: fd });
    const data = await res.json();

    btn.disabled = false;
    btn.textContent = 'Upload';

    if (data.success) {
      form.reset();
      // Reset preview
      document.getElementById('gallery-preview-wrap').style.display = 'none';
      document.getElementById('gallery-drop-placeholder').style.display = '';
      toast('📸 Photo uploaded!');
      window.loadGallery(currentMeetupId);
    } else {
      toast(data.message || 'Upload failed');
    }
    return false;
  };

  /* ── Delete ───────────────────────────────────────────── */
  window.deletePhoto = async function (id) {
    if (!confirm('Delete your photo? This cannot be undone.')) return;
    await fetch(`/meetup/gallery/${id}/delete`, { method: 'POST' });
    window.loadGallery(currentMeetupId);
  };

  /* ── Like ─────────────────────────────────────────────── */
  window.toggleLike = async function (id) {
    const res  = await fetch(`/meetup/gallery/${id}/like`, { method: 'POST' });
    const data = await res.json();
    const card = document.querySelector(`[data-photo-id="${id}"]`);
    if (!card || !data.success) return;
    const btn     = card.querySelector('button[onclick*="toggleLike"]');
    const countEl = card.querySelector('[data-like-count]');
    let n = parseInt(countEl.textContent, 10) || 0;
    if (data.liked) {
      n += 1;
      btn.innerHTML = `❤️ <span data-like-count>${n}</span>`;
      btn.style.borderColor = 'var(--red)';
      btn.style.color = 'var(--red)';
    } else {
      n = Math.max(0, n - 1);
      btn.innerHTML = `🤍 <span data-like-count>${n}</span>`;
      btn.style.borderColor = '';
      btn.style.color = '';
    }
  };

  /* ── Privacy ──────────────────────────────────────────── */
  window.togglePrivacy = async function (id, isPublic) {
    await fetch(`/meetup/gallery/${id}/privacy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_public: !isPublic })
    });
    window.loadGallery(currentMeetupId);
  };

  /* ── Comments ─────────────────────────────────────────── */
  window.toggleComments = async function (id) {
    const card = document.querySelector(`[data-photo-id="${id}"]`);
    const box  = card && card.querySelector(`[data-comments-for="${id}"]`);
    if (!box) return;
    if (box.style.display === 'block') { box.style.display = 'none'; return; }
    box.style.display = 'block';
    const list = box.querySelector('.comment-list');
    list.innerHTML = '<div style="font-size:12px;color:var(--muted)">Loading…</div>';
    const res  = await fetch(`/meetup/gallery/${id}/comments`);
    const data = await res.json();
    renderComments(card, id, data.comments || []);
  };

  function renderComments(card, id, comments) {
    const list = card.querySelector(`[data-comments-for="${id}"] .comment-list`);
    if (!comments.length) {
      list.innerHTML = '<div style="font-size:12px;color:var(--muted);font-style:italic">No comments yet.</div>';
    } else {
      list.innerHTML = comments.map(c => {
        const initials = (c.full_name || 'M').split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
        return `
          <div style="display:flex;gap:8px;align-items:flex-start">
            <div style="width:24px;height:24px;border-radius:50%;background:linear-gradient(135deg,var(--primary),#1A56C4);color:#fff;font-size:9px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0">${esc(initials)}</div>
            <div style="flex:1;min-width:0">
              <div style="font-size:12px">
                <strong style="color:var(--text)">${esc(c.full_name || 'Member')}</strong>
                <span style="color:var(--muted);font-size:10px;margin-left:4px">${timeAgo(c.created_at)}</span>
              </div>
              <div style="font-size:12px;color:var(--text);margin-top:2px;word-break:break-word">${esc(c.comment)}</div>
            </div>
          </div>`;
      }).join('');
    }
    const countEl = card.querySelector('[data-comment-count]');
    if (countEl) countEl.textContent = comments.length;
  }

  window.addComment = async function (id, input) {
    const text = (input.value || '').trim();
    if (!text) return;
    const res  = await fetch(`/meetup/gallery/${id}/comment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ comment: text })
    });
    const data = await res.json();
    if (data.success) {
      input.value = '';
      const card = document.querySelector(`[data-photo-id="${id}"]`);
      renderComments(card, id, data.comments || []);
    }
  };

  /* ── Lightbox ─────────────────────────────────────────── */
  window.openLightbox = async function (id) {
    const res  = await fetch(`/meetup/${currentMeetupId}/gallery/list`);
    const data = await res.json();
    const p    = (data.photos || []).find(x => x.id === id);
    if (!p) return;
    document.getElementById('lightbox-img').src = p.url;
    document.getElementById('lightbox-caption').textContent = p.caption || 'Photo';
    document.getElementById('lightbox-meta').textContent =
      `Posted by ${p.full_name || 'Member'} · ${fmtDate(p.created_at)} · ❤️ ${p.like_count} · 💬 ${p.comment_count}`;
    const dl = document.getElementById('lightbox-download');
    dl.href = p.url;
    if (typeof openModal === 'function') openModal('gallery-lightbox');
  };

  /* ── Init ─────────────────────────────────────────────── */
  document.addEventListener('DOMContentLoaded', () => {
    if (currentMeetupId) window.loadGallery(currentMeetupId);
    else window.loadGallery(null);
  });
})();