// plan-dynamic.js — Dynamic data loading for the serial planner modals
// Fixed: correct container IDs, auto-calculate ride estimates, real cuisine/nearby data.

(function () {
  'use strict';

  const API = {
    cuisines:   '/place/api/cuisines',
    budgetRange:'/place/api/budget-range',
    ambiences:  '/place/api/ambiences',
    offers:     '/place/api/offers',
    nearby:     '/place/api/nearby',
    split:      (id) => `/ride/split/${id}`,
    calculate:  (id) => `/ride/calculate/${id}`,
  };

  function getMeetupId() {
    return (window.PLAN_CONTEXT || {}).meetupId || null;
  }

  function getMidpoint() {
    // Try PLAN_CONTEXT first, then read the live midpoint from the map
    const ctx = window.PLAN_CONTEXT || {};
    if (ctx.midpoint && ctx.midpoint.lat) return ctx.midpoint;
    // Fall back to what calcMidpoint() stored on the context object
    if (window._planMidpointCache) return window._planMidpointCache;
    return null;
  }

  function getUserLocation() {
    const ctx = window.PLAN_CONTEXT || {};
    const myId = ctx.currentUserId;
    const points = ctx.mapPoints || [];

    // Find the point that belongs to the current logged-in user.
    // mapPoints[0] is NOT reliably "me" — it's just whichever member's
    // DB row came back first (usually the meetup creator), so every
    // other member would otherwise see the creator's location.
    if (myId != null) {
      const mine = points.find(p => p.user_id === myId);
      if (mine) return { lat: mine.lat, lng: mine.lng, address: mine.address || '' };
    }

    // Fallback: pm-lat/pm-lng inputs (set if the user shared their browser location this session)
    const pmLat = document.getElementById('pm-lat');
    const pmLng = document.getElementById('pm-lng');
    if (pmLat && pmLng && pmLat.value && pmLng.value) {
      const addrEl = document.getElementById('pm-addr');
      return { lat: Number(pmLat.value), lng: Number(pmLng.value), address: addrEl ? addrEl.value : '' };
    }

    // Last resort: first available point (old behavior), only if nothing else matched
    if (points.length > 0) {
      const p = points[0];
      return { lat: p.lat, lng: p.lng, address: p.address || '' };
    }
    return null;
  }

  // ── Generic fetch helper ───────────────────────────────────────────
  async function fetchJSON(url, opts) {
    try {
      const res = await fetch(url, Object.assign({ headers: { 'X-Requested-With': 'XMLHttpRequest' } }, opts || {}));
      if (!res.ok) return null;
      return await res.json();
    } catch (e) {
      console.warn('fetchJSON failed:', url, e);
      return null;
    }
  }

  // ── Auto-calculate ride estimate for current user ─────────────────
  // Called before Walking Distance and Ride Cost modals open.
  // Uses the user's stored location → meetup midpoint as the route.
  async function ensureRideEstimate() {
    const meetupId = getMeetupId();
    if (!meetupId) return false;

    // Check if estimate already exists
    const existing = await fetchJSON(API.split(meetupId));
    const myId = (window.PLAN_CONTEXT || {}).currentUserId || 0;
    if (existing && existing.success && existing.data && existing.data.members) {
      const alreadyHas = existing.data.members.some(m => m.user_id === myId);
      if (alreadyHas) return true;
    }

    // Need to calculate — get user location and midpoint
    const userLoc = getUserLocation();
    const mid = getMidpoint();
    if (!userLoc || !mid) return false;

    const result = await fetchJSON(API.calculate(meetupId), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
      body: JSON.stringify({
        from_lat:     userLoc.lat,
        from_lng:     userLoc.lng,
        from_address: userLoc.address,
        to_lat:       mid.lat,
        to_lng:       mid.lng,
        to_address:   mid.address || 'Midpoint',
      }),
    });
    return !!(result && result.success);
  }

  // ── Modal 1: Midpoint Calculator ─────────────────────────────────
  // Handled by calcMidpoint() in plan.html — nothing to do here.

  // ── Modal 2: Restaurant Offers ────────────────────────────────────
  // The modal HTML uses id="featured-restaurant-offers".
  // plan.html's renderFeaturedRestaurantOffers() fills it from real DB data.
  // This function is the fallback when that renderer isn't available.
  async function loadOffers() {
    if (typeof window.renderFeaturedRestaurantOffers === 'function') {
      window.renderFeaturedRestaurantOffers();
      return;
    }
    const container = document.getElementById('featured-restaurant-offers');
    if (!container) return;
    container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--muted)">Loading offers…</div>';

    const data = await fetchJSON(API.offers);
    if (!data || !data.success || !data.offers || !data.offers.length) {
      container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--muted)">No active offers right now.</div>';
      return;
    }
    container.innerHTML = data.offers.map(o => `
      <div class="restaurant-card" style="margin-bottom:10px;cursor:pointer;"
           onclick="if(window.selectOfferRestaurant)selectOfferRestaurant(this);else this.style.borderColor='var(--green)'"
           data-offer-restaurant="${escapeHtml(o.restaurant_name)}">
        <div class="rest-emoji">${offerEmoji(o.cuisine)}</div>
        <div style="flex:1">
          <div class="rest-name">${escapeHtml(o.restaurant_name)}</div>
          <div class="rest-meta">${escapeHtml(o.title)}${o.discount_percent ? ' · ' + o.discount_percent + '% off' : ''}</div>
        </div>
        ${o.discount_percent ? `<span style="background:var(--green);color:#fff;font-size:10px;font-weight:700;padding:3px 8px;border-radius:8px">${o.discount_percent}% OFF</span>` : ''}
      </div>`).join('');
  }

  function offerEmoji(cuisine) {
    const map = { nepali:'🍛', indian:'🍛', italian:'🍕', cafe:'☕', 'coffee & cafe':'☕',
                  continental:'🥗', chinese:'🥡', japanese:'🍣', thai:'🍜',
                  asian:'🥡', 'fast food':'🍔', 'bakery & desserts':'🧁',
                  'vegetarian & vegan':'🌱' };
    return map[(cuisine || '').toLowerCase()] || '🍽️';
  }

  // ── Modal 3: Cuisine Preference ──────────────────────────────────
  // Loads real cuisine categories from the restaurants table.
  async function loadCuisines() {
    const container = document.getElementById('cuisine-dynamic-chips');
    if (!container) return;
    container.innerHTML = '<div style="font-size:12px;color:var(--muted);padding:8px">Loading cuisines…</div>';

    const data = await fetchJSON(API.cuisines);
    if (!data || !data.success || !data.cuisines || !data.cuisines.length) {
      // Fallback to sensible Kathmandu defaults
      container.innerHTML = ['🍛 Nepali','☕ Coffee & Cafe','🍕 Italian','🥗 Continental','🌱 Vegetarian & Vegan','🥡 Asian','🍔 Fast Food']
        .map(c => `<div class="filter-chip" onclick="toggleChip(this)">${c}</div>`).join('');
      return;
    }
    container.innerHTML = data.cuisines.map(c =>
      `<div class="filter-chip" onclick="toggleChip(this)">${cuisineEmoji(c)} ${escapeHtml(c)}</div>`
    ).join('');
  }

  function cuisineEmoji(c) {
    const map = { nepali:'🍛', indian:'🍛', italian:'🍕', cafe:'☕', 'coffee & cafe':'☕',
                  continental:'🥗', chinese:'🥡', japanese:'🍣', thai:'🍜',
                  asian:'🥡', 'fast food':'🍔', 'bakery & desserts':'🧁',
                  'vegetarian & vegan':'🌱', vegetarian:'🌱', mexican:'🌮' };
    return map[(c || '').toLowerCase()] || '🍽️';
  }

  // ── Modal 4: Budget Filter ───────────────────────────────────────
  // Loads real min/max cost from the restaurants table.
  async function loadBudgetRange() {
    const slider  = document.querySelector('#modal-budget-filter input[type=range]');
    const display = document.getElementById('budget-display');
    if (!slider) return;

    const data = await fetchJSON(API.budgetRange);
    if (data && data.success) {
      slider.min   = Math.max(200, Math.floor((data.min || 200) / 100) * 100);
      slider.max   = Math.ceil((data.max  || 5000) / 100) * 100 || 5000;
      slider.step  = 100;
      slider.value = Math.min(1000, slider.max);
      if (display) display.textContent = 'NPR ' + parseInt(slider.value).toLocaleString();
    }
  }

  // ── Modal 5: Nearby Restaurants ──────────────────────────────────
  // Shows restaurants sorted by distance from the calculated midpoint.
  // Respects cuisine + budget filters set in earlier steps, and lets
  // the user adjust the search radius right inside the modal.
  async function loadNearby() {
    // 1. Update the midpoint context pill at the top of the modal
    const mid = getMidpoint();
    const midLabel = document.getElementById('nearby-midpoint-label');
    if (midLabel) {
      midLabel.textContent = mid && mid.address
        ? mid.address
        : (mid ? (mid.lat.toFixed(4) + ', ' + mid.lng.toFixed(4)) : 'Midpoint not calculated yet');
    }

    // 2. Reflect active cuisine + budget filters from earlier steps
    _renderActiveFilterPills();

    // 3. Sync radius into global constant before fetching
    const radiusSel = document.getElementById('nearby-radius-select');
    if (radiusSel) {
      window.PLAN_RESTAURANT_RADIUS_KM = parseFloat(radiusSel.value) || 5.0;
    }

    // 4. Use plan.html's refreshMidpointRestaurants() if available
    if (typeof window.refreshMidpointRestaurants === 'function') {
      window.refreshMidpointRestaurants();
      return;
    }

    // 5. Fallback: call the API directly
    const container = document.getElementById('nearby-restaurant-results');
    if (!container) return;
    container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--muted)">Finding nearby spots…</div>';

    if (!mid || !mid.lat || !mid.lng) {
      container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--muted)">Calculate the midpoint first, then come back.</div>';
      return;
    }

    const radius = window.PLAN_RESTAURANT_RADIUS_KM || 5.0;
    const filters = (window.planRestaurantFilters || {});
    let url = `${API.nearby}?lat=${mid.lat}&lng=${mid.lng}&radius=${radius}`;
    if (filters.cuisines && filters.cuisines.length) {
      filters.cuisines.forEach(c => { url += `&cuisine=${encodeURIComponent(c)}`; });
    }
    if (filters.maxBudget) url += `&max_budget=${filters.maxBudget}`;
    if (filters.minRating) url += `&min_rating=${filters.minRating}`;

    const data = await fetchJSON(url);
    if (!data || !data.success || !data.restaurants || !data.restaurants.length) {
      container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--muted)">No restaurants found within ' + radius + ' km. Try a larger radius.</div>';
      return;
    }
    container.innerHTML = data.restaurants.slice(0, 8).map((r, i) => `
      <div class="venue-row ${i === 0 ? 'selected' : ''}"
           data-restaurant-name="${escapeHtml(r.name)}"
           data-lat="${r.latitude || ''}" data-lng="${r.longitude || ''}"
           onclick="if(window.selectVenueRow)selectVenueRow(this)">
        <div class="venue-emoji">${offerEmoji(r.cuisine)}</div>
        <div style="flex:1">
          <div class="venue-name">${escapeHtml(r.name)}</div>
          <div class="venue-rating">⭐ ${Number(r.rating||0).toFixed(1)}${r.distance_km != null ? ' · 📍 ' + Number(r.distance_km).toFixed(1) + ' km' : ''}${r.avg_cost_per_person ? ' · NPR ' + Math.round(r.avg_cost_per_person) + '/person' : ''}</div>
        </div>
      </div>`).join('');
  }

  // Render active-filter pills inside the nearby modal so users can see
  // which cuisine/budget constraints are being applied automatically.
  function _renderActiveFilterPills() {
    const pillsEl   = document.getElementById('nearby-filter-pills');
    const wrapperEl = document.getElementById('nearby-active-filters');
    if (!pillsEl || !wrapperEl) return;

    const filters = window.planRestaurantFilters || {};
    const pills = [];

    // Cuisine chips selected in modal-cuisine-preference
    (filters.cuisines || []).forEach(function(c) {
      pills.push({ label: '🍽️ ' + c, type: 'cuisine' });
    });

    // Budget set in modal-budget-filter
    if (filters.maxBudget && filters.maxBudget > 0) {
      pills.push({ label: '💰 ≤ NPR ' + Number(filters.maxBudget).toLocaleString() + '/person', type: 'budget' });
    }

    // Rating set in the modal itself
    const ratingEl = document.getElementById('restaurant-min-rating');
    const rating = ratingEl ? parseFloat(ratingEl.value) : 0;
    if (rating > 0) {
      pills.push({ label: '⭐ ' + rating + '+ stars', type: 'rating' });
    }

    if (!pills.length) {
      wrapperEl.style.display = 'none';
      return;
    }

    wrapperEl.style.display = 'block';
    pillsEl.innerHTML = pills.map(function(p) {
      return '<span style="display:inline-flex;align-items:center;gap:4px;background:rgba(21,101,192,.1);color:var(--blue);font-size:11px;font-weight:700;padding:3px 10px;border-radius:20px;border:1px solid rgba(21,101,192,.2);">' +
        escapeHtml(p.label) + '</span>';
    }).join('');
  }


  // ── Modal 7: Ride Cost Estimation ─────────────────────────────────
  // Auto-calculates estimate for current user if missing,
  // then shows real Pathao Bike / Car / Taxi costs.
  async function loadRideCost() {
    const container = document.getElementById('ride-dynamic-list');
    if (!container) return;
    const meetupId = getMeetupId();

    if (!meetupId) {
      container.innerHTML = '<div style="font-size:12px;color:var(--muted)">Create a meetup first to estimate ride costs.</div>';
      return;
    }

    container.innerHTML = '<div style="font-size:12px;color:var(--muted);padding:8px">Calculating ride costs…</div>';

    // Auto-calculate estimate for current user if missing
    await ensureRideEstimate();

    const data = await fetchJSON(API.split(meetupId));
    const myId = (window.PLAN_CONTEXT || {}).currentUserId || 0;

    if (!data || !data.success || !data.data || !data.data.members || !data.data.members.length) {
      // Fallback: compute costs from PLAN_CONTEXT directly
      const ctx = window.PLAN_CONTEXT || {};
      const mid = getMidpoint();
      const userLoc = getUserLocation();
      if (mid && userLoc) {
        const dist = haversineKm(userLoc.lat, userLoc.lng, mid.lat, mid.lng);
        renderRideCards(container, { distance: dist, bike_cost: bikeCost(dist), car_cost: carCost(dist), taxi_cost: taxiCost(dist), bike_mins: Math.round(dist/22*60)||5, car_mins: Math.round(dist/16*60)||7, is_peak: false });
        return;
      }
      container.innerHTML = ridePlaceholder();
      return;
    }

    const myEst = data.data.members.find(m => m.user_id === myId) || data.data.members[0];
    renderRideCards(container, myEst);
  }

  function renderRideCards(container, est) {
    const bikeMins = est.bike_mins != null ? est.bike_mins : Math.round((est.distance || 2) / 22 * 60) || 5;
    const carMins  = est.car_mins  != null ? est.car_mins  : Math.round((est.distance || 2) / 16 * 60) || 8;
    const peak     = est.is_peak ? ' · 🔴 Peak' : '';
    container.innerHTML = `
      <div class="restaurant-card selected" data-ride-option="Pathao Bike" onclick="selectRideOption(this)">
        <div class="rest-emoji">🛵</div>
        <div style="flex:1"><div class="rest-name">Pathao Bike</div>
          <div class="rest-meta">~${bikeMins} mins · NPR ${Math.round(est.bike_cost || 85)}${peak}</div></div>
      </div>
      <div class="restaurant-card" data-ride-option="Pathao Car" onclick="selectRideOption(this)">
        <div class="rest-emoji">🚗</div>
        <div style="flex:1"><div class="rest-name">Pathao Car</div>
          <div class="rest-meta">~${carMins} mins · NPR ${Math.round(est.car_cost || 200)}${peak}</div></div>
      </div>
      <div class="restaurant-card" data-ride-option="Taxi" onclick="selectRideOption(this)">
        <div class="rest-emoji">🚕</div>
        <div style="flex:1"><div class="rest-name">Taxi</div>
          <div class="rest-meta">Meter fare · NPR ${Math.round(est.taxi_cost || 220)}${peak}</div></div>
      </div>`;
  }

  function ridePlaceholder() {
    return `
      <div class="restaurant-card selected" data-ride-option="Pathao Bike" onclick="selectRideOption(this)">
        <div class="rest-emoji">🛵</div><div style="flex:1"><div class="rest-name">Pathao Bike</div><div class="rest-meta">Set your location to calculate</div></div>
      </div>
      <div class="restaurant-card" data-ride-option="Taxi" onclick="selectRideOption(this)">
        <div class="rest-emoji">🚕</div><div style="flex:1"><div class="rest-name">Taxi</div><div class="rest-meta">Set your location to calculate</div></div>
      </div>`;
  }


  // ── Ride option selection ─────────────────────────────────────────
  window.selectRideOption = function(card) {
    if (!card) return;
    const c = card.closest('#ride-dynamic-list');
    if (c) c.querySelectorAll('.restaurant-card').forEach(x => x.classList.remove('selected'));
    card.classList.add('selected');
  };

  // ── Local fare helpers (mirrors ride_controller.py constants) ────
  function bikeCost(km) { return Math.round(25 + 18 * km); }
  function carCost(km)  { return Math.round(50 + 35 * km); }
  function taxiCost(km) { return Math.round(50 + 45 * km); }

  function haversineKm(lat1, lng1, lat2, lng2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLng/2)**2;
    return R * 2 * Math.asin(Math.sqrt(a));
  }

  // ── Escape helper ─────────────────────────────────────────────────
  function escapeHtml(text) {
    if (text == null) return '';
    return String(text).replace(/[&<>"']/g, ch => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[ch]));
  }

  // ── Modal 1 (extra): Populate midpoint inputs from invited members ──
  function loadMidpointModal() {
    var list = document.getElementById('midpoint-location-list');
    if (!list) return;

    var ctx = window.PLAN_CONTEXT || {};
    var members = ctx.members || [];
    var mapPoints = ctx.mapPoints || [];

    // Build per-person data: mapPoints has lat/lng for those who shared location,
    // members has full_name for everyone including those who haven't shared yet.
    var inputs = [];

    if (members.length > 0) {
      // Remove existing hardcoded inputs, replace with one per member
      list.innerHTML = '';
      members.forEach(function(m, i) {
        // Find matching mapPoint (same user_id) for lat/lng
        var pt = mapPoints.find(function(p) { return p.name === m.full_name; }) || null;
        var hasLocation = m.latitude && m.longitude;

        var input = document.createElement('input');
        input.className = 'field-input mp-location-input';
        input.id = i === 0 ? 'mp-loc1' : (i === 1 ? 'mp-loc2' : 'mp-loc' + (i + 1));

        if (hasLocation) {
          // Member already has a location
          var addr = m.address || (m.full_name + "'s location");
          input.value = addr;
          input.dataset.lat = m.latitude;
          input.dataset.lng = m.longitude;
          input.dataset.name = m.full_name;
          input.dataset.address = addr;
          input.dataset.sourceValue = addr;
        } else {
          // Member invited but hasn't shared location yet
          input.value = '';
          input.placeholder = m.full_name + ' (location pending)';
          input.dataset.name = m.full_name;
        }

        input.addEventListener('input', function() {
          if (window.midpointDirty !== undefined) window.midpointDirty = true;
        });
        list.appendChild(input);
        inputs.push(input);
      });
    } else if (mapPoints.length > 0) {
      // No members array, fall back to mapPoints (creator only scenario)
      list.innerHTML = '';
      mapPoints.forEach(function(p, i) {
        var input = document.createElement('input');
        input.className = 'field-input mp-location-input';
        input.id = i === 0 ? 'mp-loc1' : ('mp-loc' + (i + 1));
        input.value = p.address || p.name || '';
        input.dataset.lat = p.lat;
        input.dataset.lng = p.lng;
        input.dataset.name = p.name || '';
        input.dataset.address = p.address || '';
        input.addEventListener('input', function() {
          if (window.midpointDirty !== undefined) window.midpointDirty = true;
        });
        list.appendChild(input);
      });
    }
    // If there are at least 2 inputs with coordinates, auto-calc
    var allHaveCoords = inputs.length >= 2 && inputs.every(function(inp) {
      return inp.dataset.lat && inp.dataset.lng;
    });
    if (allHaveCoords && typeof window.calcMidpoint === 'function') {
      window.calcMidpoint();
    }
  }

  // ── Modal data loader router ──────────────────────────────────────
  const MODAL_LOADERS = {
    'modal-midpoint':           loadMidpointModal,
    'modal-restaurant-offers':  loadOffers,
    'modal-cuisine-preference': loadCuisines,
    'modal-budget-filter':      loadBudgetRange,
    'modal-nearby-restaurants': loadNearby,
    'modal-ride-cost':          loadRideCost,
  };

  function loadModalData(modalId) {
    const loader = MODAL_LOADERS[modalId];
    if (loader) loader();
    // Extra: sync midpoint label whenever the nearby modal opens
    if (modalId === 'modal-nearby-restaurants') {
      const mid = getMidpoint();
      const midLabel = document.getElementById('nearby-midpoint-label');
      if (midLabel) {
        midLabel.textContent = (mid && mid.address)
          ? mid.address
          : (mid ? (Number(mid.lat).toFixed(4) + ', ' + Number(mid.lng).toFixed(4)) : 'Midpoint not set — calculate it first');
      }
    }
  }

  // ── MutationObserver — fire loader when modal gets class "open" ──
  const observer = new MutationObserver(mutations => {
    mutations.forEach(m => {
      if (m.type === 'attributes' && m.attributeName === 'class') {
        const el = m.target;
        if (el.classList.contains('open') && el.id && MODAL_LOADERS[el.id]) {
          loadModalData(el.id);
        }
      }
    });
  });

  document.querySelectorAll('.feat-modal-overlay, .modal-overlay').forEach(modal => {
    observer.observe(modal, { attributes: true, attributeFilter: ['class'] });
  });

  // ── Hook into startSerialPlan to pre-load first modal ────────────
  const _origStart = window.startSerialPlan;
  window.startSerialPlan = function() {
    if (_origStart) _origStart.apply(this, arguments);
    setTimeout(() => {
      const first = document.querySelector('.feat-modal-overlay.open, .modal-overlay.open');
      if (first && first.id) loadModalData(first.id);
    }, 300);
  };

  // ── Public API ────────────────────────────────────────────────────
  window.loadModalData        = loadModalData;
  window.loadRideCost         = loadRideCost;
  window.loadNearby           = loadNearby;
  window.loadOffers           = loadOffers;

  // Radius dropdown handler — updates the global radius then re-fetches
  window.updateNearbyRadius = function(val) {
    window.PLAN_RESTAURANT_RADIUS_KM = parseFloat(val) || 5.0;
    if (typeof window.refreshMidpointRestaurants === 'function') {
      window.refreshMidpointRestaurants();
    } else {
      loadNearby();
    }
  };

})();
