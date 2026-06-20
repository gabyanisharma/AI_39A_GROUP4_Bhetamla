// plan-dynamic.js — Dynamic data loading for the serial planner modals
// This makes the planner modals fetch real data from the backend instead of showing static content.

(function () {
  'use strict';

  const API = {
    cuisines: '/place/api/cuisines',
    budgetRange: '/place/api/budget-range',
    ambiences: '/place/api/ambiences',
    offers: '/place/api/offers',
    nearby: '/place/api/nearby',
    split: (meetupId) => `/ride/split/${meetupId}`,
    calculate: (meetupId) => `/ride/calculate/${meetupId}`,
    members: (meetupId) => `/meetup/${meetupId}/route`, // reusing route endpoint for member data
  };

  function getMeetupId() {
    const ctx = window.PLAN_CONTEXT || {};
    return ctx.meetupId || null;
  }

  function getMidpoint() {
    const ctx = window.PLAN_CONTEXT || {};
    return ctx.midpoint || null;
  }

  // ── Generic fetch helper ───────────────────────────────────────────
  async function fetchJSON(url) {
    try {
      const res = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      if (!res.ok) return null;
      return await res.json();
    } catch (e) {
      console.warn('fetchJSON failed:', url, e);
      return null;
    }
  }

  // ── Modal 1: Midpoint Calculator ─────────────────────────────────
  // Already handled by real calcMidpoint in plan.html

  // ── Modal 2: Restaurant Offers ────────────────────────────────────
  async function loadOffers() {
    const container = document.getElementById('offers-dynamic-list');
    if (!container) return;
    container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--muted)">Loading offers…</div>';

    const data = await fetchJSON(API.offers);
    if (!data || !data.success || !data.offers || !data.offers.length) {
      container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--muted)">No active offers found.</div>';
      return;
    }

    container.innerHTML = data.offers.map(o => `
      <div class="restaurant-card" style="margin-bottom:10px;cursor:pointer;" onclick="selectOffer(this)">
        <div class="rest-emoji">${offerEmoji(o.cuisine)}</div>
        <div style="flex:1">
          <div class="rest-name">${escapeHtml(o.restaurant_name)}</div>
          <div class="rest-meta">${escapeHtml(o.title)}${o.discount_percent ? ' · ' + o.discount_percent + '% off' : ''}</div>
        </div>
        ${o.discount_percent ? `<span style="background:var(--green);color:#fff;font-size:10px;font-weight:700;padding:3px 8px;border-radius:8px">${o.discount_percent}% OFF</span>` : ''}
      </div>
    `).join('');
  }

  function offerEmoji(cuisine) {
    const map = { 'nepali': '🍛', 'italian': '🍕', 'cafe': '☕', 'continental': '🥗', 'chinese': '🥡', 'indian': '🍛', 'japanese': '🍣', 'thai': '🍜' };
    return map[(cuisine || '').toLowerCase()] || '🍽️';
  }

  window.selectOffer = function (el) {
    document.querySelectorAll('#offers-dynamic-list .restaurant-card').forEach(c => c.style.borderColor = 'var(--border)');
    el.style.borderColor = 'var(--green)';
  };

  // ── Modal 3: Cuisine Preference ──────────────────────────────────
  async function loadCuisines() {
    const container = document.getElementById('cuisine-dynamic-chips');
    if (!container) return;
    const data = await fetchJSON(API.cuisines);
    const chips = (data && data.success && data.cuisines && data.cuisines.length)
      ? data.cuisines.map(c => `<div class="filter-chip" onclick="toggleChip(this)">${cuisineEmoji(c)} ${escapeHtml(c)}</div>`).join('')
      : '<div style="font-size:12px;color:var(--muted)">No cuisine data available.</div>';
    container.innerHTML = chips;
  }

  function cuisineEmoji(c) {
    const map = { 'nepali': '🍛', 'italian': '🍕', 'cafe': '☕', 'continental': '🥗', 'chinese': '🥡', 'indian': '🍛', 'japanese': '🍣', 'thai': '🍜', 'vegetarian': '🌱', 'mexican': '🌮' };
    return map[(c || '').toLowerCase()] || '🍽️';
  }

  // ── Modal 4: Budget Filter ───────────────────────────────────────
  async function loadBudgetRange() {
    const slider = document.querySelector('#modal-budget-filter input[type=range]');
    const display = document.getElementById('budget-display');
    if (!slider) return;

    const data = await fetchJSON(API.budgetRange);
    if (data && data.success) {
      slider.min = Math.max(200, Math.floor(data.min / 100) * 100);
      slider.max = Math.ceil(data.max / 100) * 100 || 5000;
      slider.step = 100;
      if (display) display.textContent = 'NPR ' + parseInt(slider.value).toLocaleString();
    }
  }

  // ── Modal 5: Ambience Filter ─────────────────────────────────────
  async function loadAmbiences() {
    const container = document.getElementById('ambience-dynamic-pills');
    if (!container) return;
    const data = await fetchJSON(API.ambiences);
    const pills = (data && data.success && data.ambiences && data.ambiences.length)
      ? data.ambiences.map(a => `
        <div class="ambience-pill" onclick="toggleAmbience(this)">
          <div class="ambience-pill-icon">${ambienceEmoji(a)}</div>
          <div class="ambience-pill-label">${escapeHtml(a)}</div>
        </div>`).join('')
      : '<div style="font-size:12px;color:var(--muted)">No ambience data available.</div>';
    container.innerHTML = pills;
  }

  function ambienceEmoji(a) {
    const map = { 'cozy cafe': '☕', 'rooftop': '🌇', 'garden': '🌿', 'quiet': '📚', 'lively': '🎉', 'romantic': '💖', 'family': '👨‍👩‍👧‍👦', 'luxury': '✨' };
    return map[(a || '').toLowerCase()] || '🏛️';
  }

  // ── Modal 6: Nearby Restaurants ─────────────────────────────────
  async function loadNearby() {
    const container = document.getElementById('nearby-dynamic-list');
    const subtitle = document.getElementById('nearby-dynamic-subtitle');
    if (!container) return;
    container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--muted)">Finding nearby spots…</div>';

    const mid = getMidpoint();
    let url = API.nearby;
    if (mid && mid.lat && mid.lng) {
      url += `?lat=${mid.lat}&lng=${mid.lng}&radius=3.0`;
      if (subtitle) subtitle.textContent = 'Top picks near ' + (mid.address || 'the midpoint') + '.';
    }

    const data = await fetchJSON(url);
    if (!data || !data.success || !data.restaurants || !data.restaurants.length) {
      container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--muted)">No restaurants found nearby. Try adjusting the midpoint.</div>';
      return;
    }

    container.innerHTML = data.restaurants.slice(0, 6).map((r, i) => `
      <div class="venue-row ${i === 0 ? 'selected' : ''}" id="venue${i + 1}" onclick="selectVenueRow(this)">
        <div class="venue-emoji">${offerEmoji(r.cuisine)}</div>
        <div style="flex:1">
          <div class="venue-name">${escapeHtml(r.name)}</div>
          <div class="venue-rating">⭐ ${r.rating || '—'}${r.distance_km ? ' · ' + r.distance_km + ' km' : ''}${r.avg_cost_per_person ? ' · NPR ' + Math.round(r.avg_cost_per_person) : ''}</div>
        </div>
      </div>
    `).join('');
  }

  window.selectVenueRow = function (el) {
    document.querySelectorAll('#nearby-dynamic-list .venue-row').forEach(c => c.classList.remove('selected'));
    el.classList.add('selected');
  };

  // ── Modal 7: Dynamic Budget Split ────────────────────────────────
  async function loadBudgetSplit() {
    const container = document.getElementById('split-dynamic-members');
    const summary = document.getElementById('split-dynamic-summary');
    const meetupId = getMeetupId();
    if (!container) return;

    if (!meetupId) {
      container.innerHTML = '<div style="font-size:12px;color:var(--muted)">Create a meetup first to calculate splits.</div>';
      return;
    }

    container.innerHTML = '<div style="font-size:12px;color:var(--muted)">Loading split data…</div>';
    const data = await fetchJSON(API.split(meetupId));

    if (!data || !data.success) {
      container.innerHTML = '<div style="font-size:12px;color:var(--muted)">No ride estimates yet. Ask members to share their location first.</div>';
      return;
    }

    const members = data.data && data.data.members ? data.data.members : [];
    const count = members.length || 1;
    const total = parseFloat(document.getElementById('budget-total') ? document.getElementById('budget-total').value : 3500) || 3500;
    const perPerson = Math.floor(total / count);
    const remainder = total - perPerson * (count - 1);

    container.innerHTML = members.map((m, i) => `
      <div class="split-member-row" style="display:flex;align-items:center;gap:10px;padding:8px 12px;background:var(--input-bg);border-radius:10px;margin-bottom:6px;">
        <div class="avatar" style="width:32px;height:32px;background:${i === 0 ? 'var(--primary)' : (i % 2 === 0 ? 'var(--blue)' : 'var(--amber)')};font-size:11px;flex-shrink:0;color:#fff;display:flex;align-items:center;justify-content:center;">${escapeHtml(m.name || 'M').slice(0, 2).toUpperCase()}</div>
        <div style="flex:1;font-weight:600;font-size:13px;">${escapeHtml(m.name || 'Member')}</div>
        <span class="split-amount" style="font-weight:700;font-size:14px;color:var(--primary);">NPR ${(i === count - 1 ? remainder : perPerson).toLocaleString()}</span>
      </div>
    `).join('');

    if (summary) summary.textContent = `Equal split: NPR ${perPerson.toLocaleString()} / person · ${count} member${count !== 1 ? 's' : ''}`;
  }

  // ── Modal 8: Ride Cost Estimation ────────────────────────────────
  async function loadRideCost() {
    const container = document.getElementById('ride-dynamic-list');
    const meetupId = getMeetupId();
    if (!container) return;

    if (!meetupId) {
      container.innerHTML = '<div style="font-size:12px;color:var(--muted)">Create a meetup first to estimate ride costs.</div>';
      return;
    }

    container.innerHTML = '<div style="font-size:12px;color:var(--muted)">Loading ride estimates…</div>';
    const data = await fetchJSON(API.split(meetupId));

    if (!data || !data.success || !data.data || !data.data.members || !data.data.members.length) {
      container.innerHTML = `
        <div class="restaurant-card selected" data-ride-option="Pathao Bike" onclick="selectRideOption(this)"><div class="rest-emoji">🛵</div><div style="flex:1"><div class="rest-name">Pathao Bike</div><div class="rest-meta">Share your location to calculate</div></div></div>
        <div class="restaurant-card" data-ride-option="Taxi" onclick="selectRideOption(this)"><div class="rest-emoji">🚕</div><div style="flex:1"><div class="rest-name">Taxi</div><div class="rest-meta">Share your location to calculate</div></div></div>
      `;
      return;
    }

    const myId = (window.PLAN_CONTEXT && window.PLAN_CONTEXT.currentUserId) || (window.GROUPS_CONFIG && window.GROUPS_CONFIG.currentUserId) || 0;
    const myEst = data.data.members.find(m => m.user_id === myId) || data.data.members[0];

    const bikeMins = myEst.bike_mins != null ? myEst.bike_mins : Math.round(myEst.distance / 22 * 60) || 12;
    const carMins  = myEst.car_mins  != null ? myEst.car_mins  : Math.round(myEst.distance / 16 * 60) || 18;

    container.innerHTML = `
      <div class="restaurant-card selected" data-ride-option="Pathao Bike" onclick="selectRideOption(this)">
        <div class="rest-emoji">🛵</div>
        <div style="flex:1"><div class="rest-name">Pathao Bike</div><div class="rest-meta">~${bikeMins} mins · NPR ${Math.round(myEst.bike_cost || 85)}${myEst.is_peak ? ' · Peak surge' : ''}</div></div>
      </div>
      <div class="restaurant-card" data-ride-option="Pathao Car" onclick="selectRideOption(this)">
        <div class="rest-emoji">🚗</div>
        <div style="flex:1"><div class="rest-name">Pathao Car</div><div class="rest-meta">~${carMins} mins · NPR ${Math.round(myEst.car_cost || 200)}${myEst.is_peak ? ' · Peak surge' : ''}</div></div>
      </div>
      <div class="restaurant-card" data-ride-option="Taxi" onclick="selectRideOption(this)">
        <div class="rest-emoji">🚕</div>
        <div style="flex:1"><div class="rest-name">Taxi</div><div class="rest-meta">Meter fare · NPR ${Math.round(myEst.taxi_cost || 220)}${myEst.is_peak ? ' · Peak surge' : ''}</div></div>
      </div>
    `;
  }

  // ── Ride option selection ──────────────────────────────────────────
  window.selectRideOption = function(card){
    if(!card) return;
    var container = card.closest('#ride-dynamic-list');
    if(container){
      container.querySelectorAll('.restaurant-card').forEach(function(c){
        c.classList.remove('selected');
      });
    }
    card.classList.add('selected');
  };

  
  // ── Modal 9: Walking Distance ────────────────────────────────────
  async function loadWalkingDistance() {
    const container = document.getElementById('walking-dynamic-list');
    const meetupId = getMeetupId();
    if (!container) return;

    if (!meetupId) {
      container.innerHTML = '<div style="font-size:12px;color:var(--muted)">Create a meetup first to calculate walking distances.</div>';
      return;
    }

    container.innerHTML = '<div style="font-size:12px;color:var(--muted)">Calculating distances…</div>';
    const data = await fetchJSON(API.split(meetupId));

    if (!data || !data.success || !data.data || !data.data.members || !data.data.members.length) {
      container.innerHTML = '<div style="font-size:12px;color:var(--muted)">No estimates yet. Share locations first.</div>';
      return;
    }

    const walkSpeed = 4.5; // km/h
    container.innerHTML = data.data.members.map(m => {
      const dist = m.distance || 0;
      const mins = Math.round((dist / walkSpeed) * 60);
      const isWalkable = dist <= 1.5 && mins <= 20;
      return `
        <div style="display:flex;align-items:center;gap:12px;padding:11px 14px;background:${isWalkable ? 'var(--green-light)' : 'var(--input-bg)'};border-radius:10px;border:1.5px solid ${isWalkable ? 'rgba(46,125,50,.25)' : 'var(--border)'};margin-bottom:8px;">
          <span style="font-size:20px">👤</span>
          <div style="flex:1">
            <div style="font-weight:700;font-size:13px">${escapeHtml(m.name || 'Member')}</div>
            <div style="font-size:12px;color:var(--muted)">${dist.toFixed(1)} km · ~${mins} min walk</div>
          </div>
          <span style="font-size:11px;font-weight:700;color:${isWalkable ? 'var(--green)' : 'var(--amber)'}">${isWalkable ? 'WALKABLE' : 'RIDE'}</span>
        </div>
      `;
    }).join('');
  }

  // ── Escape helper ──────────────────────────────────────────────────
  function escapeHtml(text) {
    if (text == null) return '';
    return String(text).replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
  }

  // ── Modal data loader router ───────────────────────────────────────
  const MODAL_LOADERS = {
    'modal-restaurant-offers': loadOffers,
    'modal-cuisine-preference': loadCuisines,
    'modal-budget-filter': loadBudgetRange,
    'modal-ambience-filter': loadAmbiences,
    'modal-nearby-restaurants': loadNearby,
    'modal-budget-split': loadBudgetSplit,
    'modal-ride-cost': loadRideCost,
    'modal-walking-distance': loadWalkingDistance,
  };

  function loadModalData(modalId) {
    const loader = MODAL_LOADERS[modalId];
    if (loader) loader();
  }

  // ── MutationObserver to detect modal open ────────────────────────
  const observer = new MutationObserver(mutations => {
    mutations.forEach(mutation => {
      if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
        const el = mutation.target;
        if (el.classList.contains('open') && el.id && MODAL_LOADERS[el.id]) {
          loadModalData(el.id);
        }
      }
    });
  });

  document.querySelectorAll('.feat-modal-overlay, .modal-overlay').forEach(modal => {
    observer.observe(modal, { attributes: true, attributeFilter: ['class'] });
  });

  // Also hook into the existing serial planner start
  const originalStartSerialPlan = window.startSerialPlan;
  window.startSerialPlan = function () {
    if (originalStartSerialPlan) originalStartSerialPlan.apply(this, arguments);
    // Pre-load first modal data after a short delay
    setTimeout(() => {
      const firstModal = document.querySelector('.feat-modal-overlay.open, .modal-overlay.open');
      if (firstModal && firstModal.id) loadModalData(firstModal.id);
    }, 300);
  };

  // Expose for manual triggering and inline event handlers
  window.loadModalData = loadModalData;
  window.loadBudgetSplit = loadBudgetSplit;
  window.loadRideCost = loadRideCost;
  window.loadWalkingDistance = loadWalkingDistance;
  window.loadNearby = loadNearby;
  window.loadOffers = loadOffers;

})();
