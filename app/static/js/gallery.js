(function () {
  const cfg = window.GALLERY_CONFIG || {};
  let currentMeetupId = cfg.meetups && cfg.meetups.length ? cfg.meetups[0].id : null;

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

  function toast(msg) {
    if (typeof showToast === 'function') showToast(msg); else console.log(msg);
  }

  window.loadGallery = async function (meetupId) {
    currentMeetupId = meetupId ? parseInt(meetupId, 10) : null;
    const grid = document.getElementById('gallery-grid');
    const empty = document.getElementById('gallery-empty');
    if (!grid) return;
    if (!currentMeetupId) {
      grid.innerHTML = '';
      empty.style.display = 'block';
      return;
    }
    grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:30px;color:var(--muted)">Loading…</div>';
    const res = await fetch(`/meetup/${currentMeetupId}/gallery/list`);
    if (!res.ok) {
      grid.innerHTML = '';
      empty.style.display = 'block';
      empty.querySelector('div:nth-child(2)').textContent = 'Cannot load gallery';
      return;
    }
    const data = await res.json();
    const photos = data.photos || [];
    if (!photos.length) {
      grid.innerHTML = '';
      empty.style.display = 'block';
      return;
    }
    empty.style.display = 'none';
    grid.innerHTML = photos.map(renderCard).join('');
  };

  function renderCard(p) {
    const mine = p.user_id === cfg.currentUserId;
    return `
      <div class="card" data-photo-id="${p.id}" style="padding:0;overflow:hidden;display:flex;flex-direction:column">
        <div style="position:relative;height:180px;background:var(--input-bg);cursor:zoom-in"
             onclick="window.openLightbox(${p.id})">
          <img src="${esc(p.url)}" alt="${esc(p.caption)}" style="width:100%;height:100%;object-fit:cover">
          <span style="position:absolute;top:8px;right:8px;background:rgba(0,0,0,.55);color:#fff;font-size:10px;padding:2px 8px;border-radius:20px">
            ${p.is_public ? '🌐 Public' : '🔒 Private'}
          </span>
        </div>
        <div style="padding:12px;display:flex;flex-direction:column;gap:8px;flex:1">
          <div style="font-size:13px;font-weight:600;min-height:18px">${esc(p.caption) || '<span style="color:var(--muted);font-weight:400">No caption</span>'}</div>
          <div style="font-size:11px;color:var(--muted)">By ${esc(p.full_name || 'Member')} · ${fmtDate(p.created_at)}</div>
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
            <button class="btn-sec" style="width:auto;padding:5px 10px;font-size:12px;${p.liked_by_me ? 'border-color:var(--red);color:var(--red)' : ''}"
                    onclick="window.toggleLike(${p.id})">${p.liked_by_me ? '❤️' : '🤍'} <span data-like-count>${p.like_count}</span></button>
            <button class="btn-sec" style="width:auto;padding:5px 10px;font-size:12px" onclick="window.toggleComments(${p.id})">💬 <span data-comment-count>${p.comment_count}</span></button>
            <a class="btn-sec" style="width:auto;padding:5px 10px;font-size:12px;text-decoration:none" href="${esc(p.url)}" download>⬇</a>
            ${mine ? `<button class="btn-sec" style="width:auto;padding:5px 10px;font-size:12px" onclick="window.togglePrivacy(${p.id}, ${p.is_public})">${p.is_public ? 'Make private' : 'Make public'}</button>` : ''}
            ${mine ? `<button class="btn-sec" style="width:auto;padding:5px 10px;font-size:12px;color:var(--red);border-color:var(--red)" onclick="window.deletePhoto(${p.id})">Delete</button>` : ''}
          </div>
          <div class="gallery-comments" data-comments-for="${p.id}" style="display:none;border-top:1px solid var(--border);padding-top:8px;margin-top:2px">
            <div class="comment-list" style="display:flex;flex-direction:column;gap:6px;margin-bottom:8px;max-height:160px;overflow-y:auto"></div>
            <div style="display:flex;gap:6px">
              <input type="text" placeholder="Add a comment…" maxlength="300"
                     style="flex:1;padding:7px 10px;border-radius:8px;border:1px solid var(--border);font-size:12px"
                     onkeydown="if(event.key==='Enter')window.addComment(${p.id}, this)">
              <button class="btn-primary" style="width:auto;padding:7px 12px;font-size:12px" onclick="window.addComment(${p.id}, this.previousElementSibling)">Send</button>
            </div>
          </div>
        </div>
      </div>`;
  }

  window.uploadGallery = async function (e) {
    e.preventDefault();
    if (!currentMeetupId) { toast('Select a meetup first'); return false; }
    const form = e.target;
    const fd = new FormData(form);
    if (!fd.get('is_public')) fd.append('is_public', '0');
    const res = await fetch(`/meetup/${currentMeetupId}/gallery/upload`, { method: 'POST', body: fd });
    const data = await res.json();
    if (data.success) {
      form.reset();
      toast('📸 Photo uploaded');
      window.loadGallery(currentMeetupId);
    } else {
      toast(data.message || 'Upload failed');
    }
    return false;
  };

  window.deletePhoto = async function (id) {
    if (!confirm('Delete your photo? This cannot be undone.')) return;
    await fetch(`/meetup/gallery/${id}/delete`, { method: 'POST' });
    window.loadGallery(currentMeetupId);
  };

  window.toggleLike = async function (id) {
    const res = await fetch(`/meetup/gallery/${id}/like`, { method: 'POST' });
    const data = await res.json();
    const card = document.querySelector(`[data-photo-id="${id}"]`);
    if (!card || !data.success) return;
    const btn = card.querySelector('button[onclick*="toggleLike"]');
    const countEl = card.querySelector('[data-like-count]');
    let n = parseInt(countEl.textContent, 10) || 0;
    if (data.liked) {
      n += 1; btn.firstChild.textContent = '❤️ ';
      btn.style.borderColor = 'var(--red)'; btn.style.color = 'var(--red)';
    } else {
      n = Math.max(0, n - 1); btn.firstChild.textContent = '🤍 ';
      btn.style.borderColor = ''; btn.style.color = '';
    }
    countEl.textContent = n;
  };

  window.togglePrivacy = async function (id, isPublic) {
    await fetch(`/meetup/gallery/${id}/privacy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_public: !isPublic })
    });
    window.loadGallery(currentMeetupId);
  };

  window.toggleComments = async function (id) {
    const card = document.querySelector(`[data-photo-id="${id}"]`);
    const box = card && card.querySelector(`[data-comments-for="${id}"]`);
    if (!box) return;
    if (box.style.display === 'block') { box.style.display = 'none'; return; }
    box.style.display = 'block';
    const list = box.querySelector('.comment-list');
    list.innerHTML = '<div style="font-size:12px;color:var(--muted)">Loading…</div>';
    const res = await fetch(`/meetup/gallery/${id}/comments`);
    const data = await res.json();
    renderComments(card, id, data.comments || []);
  };

  function renderComments(card, id, comments) {
    const list = card.querySelector(`[data-comments-for="${id}"] .comment-list`);
    if (!comments.length) {
      list.innerHTML = '<div style="font-size:12px;color:var(--muted)">No comments yet.</div>';
    } else {
      list.innerHTML = comments.map(c => `
        <div style="font-size:12px">
          <strong>${esc(c.full_name || 'Member')}</strong>
          <span style="color:var(--muted);font-size:10px"> · ${fmtDate(c.created_at)}</span>
          <div>${esc(c.comment)}</div>
        </div>`).join('');
    }
    const countEl = card.querySelector('[data-comment-count]');
    if (countEl) countEl.textContent = comments.length;
  }

  window.addComment = async function (id, input) {
    const text = (input.value || '').trim();
    if (!text) return;
    const res = await fetch(`/meetup/gallery/${id}/comment`, {
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

  window.openLightbox = async function (id) {
    const res = await fetch(`/meetup/${currentMeetupId}/gallery/list`);
    const data = await res.json();
    const p = (data.photos || []).find(x => x.id === id);
    if (!p) return;
    document.getElementById('lightbox-img').src = p.url;
    document.getElementById('lightbox-caption').textContent = p.caption || 'Photo';
    document.getElementById('lightbox-meta').textContent =
      `By ${p.full_name || 'Member'} · ${fmtDate(p.created_at)} · ❤️ ${p.like_count} · 💬 ${p.comment_count}`;
    const dl = document.getElementById('lightbox-download');
    dl.href = p.url;
    if (typeof openModal === 'function') openModal('gallery-lightbox');
  };

  document.addEventListener('DOMContentLoaded', () => {
    if (currentMeetupId) window.loadGallery(currentMeetupId);
    else window.loadGallery(null);
  });
})();
