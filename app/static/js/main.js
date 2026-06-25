let currentTheme = 'light';
let userVote = null;
const votes = {1:11,2:6,3:3};
const totalVotes = () => Object.values(votes).reduce((a,b)=>a+b,0);

// ── PASSWORD VISIBILITY TOGGLE ──
function togglePassword(inputId, btn) {
  var input = document.getElementById(inputId);
  if (!input) return;
  var isPassword = input.type === 'password';
  input.type = isPassword ? 'text' : 'password';
  btn.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
  // Swap icon: eye vs eye-off
  if (isPassword) {
    btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';
  } else {
    btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
  }
}

// ── AUTH FORM LOADING STATE ──
function handleAuthSubmit(form) {
  var btn = form.querySelector('button[type="submit"]');
  if (!btn) return true;
  var originalText = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<span style="display:inline-flex;align-items:center;gap:8px"><svg width="16" height="16" viewBox="0 0 24 24" style="animation:spin .8s linear infinite"><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="3" stroke-dasharray="32" stroke-linecap="round"/></svg> Please wait…</span>';
  // Allow form to submit normally
  return true;
}
 
function goTo(id){
  const current=document.querySelector('.screen.active');
  const next=document.getElementById(id);
  if(!next||next===current)return;
  if(current)current.classList.add('leaving');
  setTimeout(()=>{
    document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active','leaving'));
    next.classList.add('active');
  },180);
}
 
function navTo(pageId){
  const current=document.querySelector('.page.active');
  const page=document.getElementById('page-'+pageId);
  if(!page||page===current)return;
  if(current)current.classList.add('leaving');
  setTimeout(()=>{
    document.querySelectorAll('.page').forEach(p=>p.classList.remove('active','leaving'));
    page.classList.add('active');
  },170);
  document.querySelectorAll('.nav-btn').forEach(b=>{b.classList.remove('active');b.removeAttribute('aria-current');});
  const btn=document.querySelector('[data-page="'+pageId+'"]');
  if(btn){btn.classList.add('active');btn.setAttribute('aria-current','page');}
}
document.querySelectorAll('.nav-btn[data-page]').forEach(btn=>{
  btn.addEventListener('click',()=>navTo(btn.dataset.page));
});
 
var THEME_KEY = 'bhetamla-theme';
function applyTheme(t){
  currentTheme=t;
  document.documentElement.setAttribute('data-theme',t);
  document.getElementById('theme-label') && (document.getElementById('theme-label').textContent = t==='dark'?'Light':'Dark');
  try { localStorage.setItem(THEME_KEY, t); } catch(e) {}
}
// setTheme = an explicit user choice → persisted across sessions.
function setTheme(t){
  applyTheme(t);
}
function toggleTheme(){setTheme(currentTheme==='light'?'dark':'light');}
// On load: use the saved choice, else follow the OS (auto mode). Auto mode is
// not persisted, so it keeps tracking the system until the user picks one.
(function initTheme(){
  var saved=null; try { saved=localStorage.getItem(THEME_KEY); } catch(e) {}
  if(saved==='light'||saved==='dark'){ applyTheme(saved); return; }
  var mq = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)');
  applyTheme(mq && mq.matches ? 'dark' : 'light');
  if(mq && mq.addEventListener){
    mq.addEventListener('change', function(e){
      var s=null; try { s=localStorage.getItem(THEME_KEY); } catch(_){}
      if(s!=='light'&&s!=='dark') applyTheme(e.matches?'dark':'light');
    });
  }
})();
 
function applyLang(lang, showFeedback){
  currentLang=lang;
  document.documentElement.lang=lang==='ne'?'ne':'en';
  document.querySelectorAll('[data-en],[data-ne]').forEach(el=>{
    const val=el.getAttribute('data-'+lang);
    if(val!==null){
      if(el.tagName==='INPUT'||el.tagName==='TEXTAREA')el.value=val;
      else el.textContent=val;
    }
  });
  const lbl=document.getElementById('lang-setting');
  if(lbl)lbl.textContent=lang==='ne'?'नेपाली':'English';
  if(showFeedback){
    showToast(lang==='ne'?'नेपाली भाषामा परिवर्तन गरियो':'Switched to English');
  }
}
function toggleLang(){applyLang(currentLang==='en'?'ne':'en', true);}

function selectVenue(n){
  var all = document.querySelectorAll('#nearby-dynamic-list .venue-row, #modal-nearby-restaurants .venue-row');
  all.forEach(function(v, i){
    var sel = (i + 1) === n;
    v.classList.toggle('selected', sel);
    var nm = v.querySelector('.venue-name');
    if (nm) nm.style.color = sel ? 'var(--blue)' : '';
  });
  var selected = document.querySelector('#modal-nearby-restaurants .venue-row.selected .venue-name, #modal-nearby-restaurants .venue-row:nth-child(1) .venue-name');
  var name = selected ? selected.textContent : 'Venue';
  showToast('Selected: ' + name);
}
 
// ── VOTE NAMES MAP ──
const voteNames = {1:'Himalayan Java Coffee', 2:'Bhojan Griha', 3:'Thamel Thali'};
const voteEmojis = {1:'☕', 2:'🍽️', 3:'🥘'};

function castVote(id){
  if(userVote===id)return;
  if(userVote){
    votes[userVote]=Math.max(0,votes[userVote]-1);
    document.getElementById('vote-'+userVote).classList.remove('voted');
  }
  userVote=id;
  votes[id]++;
  const total=totalVotes();
  [1,2,3].forEach(i=>{
    const pct=Math.round((votes[i]/total)*100);
    document.getElementById('fill-'+i).style.width=pct+'%';
    document.getElementById('count-'+i).textContent=votes[i]+' votes ('+pct+'%)';
    document.getElementById('pct-'+i).textContent=pct+'%';
  });
  document.getElementById('vote-'+id).classList.add('voted');
  showToast('✅ Vote cast for '+voteNames[id]+'!');

  // Determine winner (leading by >10% or has >50%)
  let leaderId=1;
  [1,2,3].forEach(i=>{ if(votes[i]>votes[leaderId]) leaderId=i; });
  const leaderPct=Math.round((votes[leaderId]/total)*100);

  // Show winner banner
  const banner=document.getElementById('vote-winner-banner');
  if(banner){
    document.getElementById('winner-name-inline').textContent=voteEmojis[leaderId]+' '+voteNames[leaderId];
    document.getElementById('winner-pct-inline').textContent=leaderPct+'% of votes ('+votes[leaderId]+' of '+total+')';
    banner.style.display='flex';
  }

  // If leader has majority, trigger win popup after short delay
  if(leaderPct>=50 && total>=5){
    setTimeout(()=>openWinPopup(leaderId),900);
  }
  // Update saved places total vote display
  const svd=document.getElementById('saved-total-votes-display');
  if(svd) svd.textContent=total+' votes cast';
}

// ── WIN POPUP ──
let currentWinnerId = 1;
function openWinPopup(id){
  if(id) currentWinnerId=id;
  const total=totalVotes();
  const wv=votes[currentWinnerId];
  const wpct=Math.round((wv/total)*100);
  document.getElementById('win-popup-place-name').textContent=voteEmojis[currentWinnerId]+' '+voteNames[currentWinnerId];
  document.getElementById('win-popup-place-desc').textContent=voteNames[currentWinnerId];
  document.getElementById('win-popup-votes').textContent=wv;
  document.getElementById('win-popup-pct').textContent=wpct+'%';
  document.getElementById('win-popup-total').textContent=total;
  document.getElementById('win-popup-overlay').classList.add('open');
}
function closeWinPopup(){
  document.getElementById('win-popup-overlay').classList.remove('open');
}
function proceedToPlanWithWinner(){
  closeWinPopup();
  // Pre-fill the plan meetup fields with the winning location
  const winner=voteNames[currentWinnerId];
  const loc2=document.getElementById('field-loc2');
  if(loc2){ loc2.value=winner; loc2.closest('.setup-field').classList.add('filled'); }
  // Also update the summary midpoint display
  const sumMid=document.getElementById('sum-mid');
  if(sumMid){ sumMid.textContent=winner; }
  navTo('plan');
  setTimeout(()=>{
    checkSetupBar&&checkSetupBar();
    showToast('🗺️ Vote winner pre-filled: '+winner);
  },300);
}

// ── NEW VOTE SESSION ──
let selectedDuration='2h';
function selectDuration(btn,val){
  selectedDuration=val;
  ['1h','2h','6h','24h'].forEach(d=>{
    const b=document.getElementById('dur-'+d);
    if(b){
      if(d===val){
        b.style.borderColor='var(--blue)'; b.style.background='var(--blue-light)'; b.style.color='var(--blue)';
        b.textContent=val+' ✓';
      } else {
        b.style.borderColor='var(--border)'; b.style.background='var(--input-bg)'; b.style.color='var(--muted)';
        b.textContent=d;
      }
    }
  });
}

function addVoteOption(){
  const inp=document.getElementById('new-location-input');
  const name=inp.value.trim();
  if(!name){showToast('Please enter a location name.');return;}
  const list=document.getElementById('new-vote-locations-list');
  if(list.children.length>=4){showToast('Maximum 4 options allowed.');return;}
  const row=document.createElement('div');
  row.className='vote-session-row';
  row.innerHTML='<span class="vs-emoji">📍</span><span class="vs-name">'+name+'</span><button class="vs-remove" onclick="removeVoteOption(this)" title="Remove">✕</button>';
  list.appendChild(row);
  inp.value='';
  showToast('Added: '+name);
}
function removeVoteOption(btn){
  const row=btn.closest('.vote-session-row');
  const list=document.getElementById('new-vote-locations-list');
  if(list.children.length<=2){showToast('Minimum 2 options required.');return;}
  row.remove();
}
function launchVoteSession(){
  const q=document.getElementById('vote-session-question').value.trim();
  if(!q){showToast('Please enter a vote question.');return;}
  const list=document.getElementById('new-vote-locations-list');
  if(list.children.length<2){showToast('Please add at least 2 locations.');return;}
  closeModal('modal-new-vote-session');
  // Update the vote question text in the groups page
  const qt=document.getElementById('vote-question-text');
  if(qt) qt.textContent=q;
  // Update timer badge
  const tb=document.getElementById('vote-timer-badge');
  if(tb) tb.textContent='Closes in '+selectedDuration;
  showToast('🗳️ Vote session launched! Members notified.');
}

// ── VOTE FOR CURRENT PLACE FROM SAVED PLACES ──
function voteForCurrentPlace(){
  // Himalayan Java Coffee = vote option 1
  castVote(1);
  showToast('✅ Voted for Himalayan Java Coffee in group poll!');
  // Update the sidebar vote status
  const status=document.getElementById('saved-place-vote-status');
  if(status){
    status.style.background='var(--green-light)';
    status.style.borderColor='rgba(27,107,58,.2)';
    status.querySelector('span[style*="color:var(--blue)"]') && (status.querySelector('span[style*="color"]').style.color='var(--green)');
  }
}
 
function acceptInvite(btn){
  const row=btn.closest('.invite-row');
  row.style.opacity='0';row.style.transition='opacity .3s';
  setTimeout(()=>{row.remove();showToast('Invite accepted!');},300);
}
 
function toggleSwitch(btn){
  const checked=btn.getAttribute('aria-checked')==='true';
  btn.setAttribute('aria-checked',checked?'false':'true');
  btn.style.background=checked?'var(--border)':'var(--blue)';
}
 
let toastTimer;
function showToast(msg){
  const t=document.getElementById('toast');
  t.textContent=msg;t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer=setTimeout(()=>t.classList.remove('show'),2800);
}
 
document.addEventListener('keydown',e=>{
  if(e.key==='Enter'||e.key===' '){
    if(e.target.classList.contains('vote-option')){e.preventDefault();castVote(parseInt(e.target.id.replace('vote-','')));}
    if(e.target.classList.contains('venue-row')){e.preventDefault();selectVenue(parseInt(e.target.id.replace('venue','')));}
    if(e.target.classList.contains('spot-card')){e.preventDefault();navTo('saved');}
  }
});

// MINI CALENDAR
let calDate = new Date();
const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const DAYS_SHORT = ['Su','Mo','Tu','We','Th','Fr','Sa'];
const MEETUP_DAYS = [new Date().getDate(), new Date().getDate()+2]; // today and in 2 days
function renderCalendar(){
  const y = calDate.getFullYear(), m = calDate.getMonth();
  const label = document.getElementById('cal-month-label');
  if(label) label.textContent = MONTHS[m] + ' ' + y;
  const grid = document.getElementById('cal-grid');
  if(!grid) return;
  const today = new Date();
  const firstDay = new Date(y,m,1).getDay();
  const daysInMonth = new Date(y,m+1,0).getDate();
  let html = DAYS_SHORT.map(d=>`<div style="font-weight:700;font-size:10px;color:var(--muted);padding:3px 0">${d}</div>`).join('');
  for(let i=0;i<firstDay;i++) html += '<div></div>';
  for(let d=1;d<=daysInMonth;d++){
    const isToday = y===today.getFullYear()&&m===today.getMonth()&&d===today.getDate();
    const hasMeetup = MEETUP_DAYS.includes(d) && m===today.getMonth() && y===today.getFullYear();
    const baseStyle = 'padding:4px 2px;border-radius:6px;cursor:default;font-size:11px;position:relative;';
    let style = baseStyle;
    if(isToday) style += 'background:var(--primary);color:#fff;font-weight:700;';
    else if(hasMeetup) style += 'background:var(--blue-light);color:var(--blue);font-weight:600;';
    else style += 'color:var(--text);';
    const dot = hasMeetup && !isToday ? '<div style="width:4px;height:4px;border-radius:50%;background:var(--blue);margin:1px auto 0"></div>' : '';
    html += `<div style="${style}" ${isToday?'aria-current="date"':''} title="${isToday?'Today':(hasMeetup?'Meetup scheduled':'')}">${d}${dot}</div>`;
  }
  grid.innerHTML = html;
}
function calPrev(){calDate.setMonth(calDate.getMonth()-1);renderCalendar();}
function calNext(){calDate.setMonth(calDate.getMonth()+1);renderCalendar();}
renderCalendar();

// UPDATE LOGIN LOGO to use uploaded image
(function(){
  const loginImg = document.querySelector('.login-center-wrap img');
  if(loginImg){
    // Show the text name if image fails
    loginImg.onerror = function(){
      this.style.display='none';
      const nameEl = this.nextElementSibling;
      if(nameEl) nameEl.style.display='block';
    };
  }
})();

// SUPPORT TOPIC ACCORDION
function toggleTopic(n){
  const body = document.getElementById('topic-body-'+n);
  const arrow = document.getElementById('topic-arrow-'+n);
  const btn = body.previousElementSibling;
  const isOpen = body.style.display !== 'none';
  // close all
  for(let i=1;i<=6;i++){
    const b=document.getElementById('topic-body-'+i);
    const a=document.getElementById('topic-arrow-'+i);
    const tb=b&&b.previousElementSibling;
    if(b){b.style.display='none';}
    if(a){a.style.transform='';} 
    if(tb){tb.setAttribute('aria-expanded','false');}
  }
  if(!isOpen){
    body.style.display='block';
    arrow.style.transform='rotate(90deg)';
    btn.setAttribute('aria-expanded','true');
  }
}

// SUPPORT PAGE NAV
function navTo(page){
  const pg=document.getElementById('page-'+page);
  const current=document.querySelector('.page.active');
  if(!pg||pg===current)return;
  if(current)current.classList.add('leaving');
  setTimeout(()=>{
    document.querySelectorAll('.page').forEach(p=>p.classList.remove('active','leaving'));
    pg.classList.add('active');
  },170);
  document.querySelectorAll('.nav-btn').forEach(b=>{b.classList.remove('active');b.removeAttribute('aria-current');});
  const btn=document.querySelector('.nav-btn[data-page="'+page+'"]');
  if(btn){btn.classList.add('active');btn.setAttribute('aria-current','page');}
}

// SOS TRIGGER
let sosActive = false;
function triggerSOS(){
  if(sosActive){
    sosActive = false;
    const badge = document.getElementById('sos-status-badge');
    if(badge){ badge.innerHTML = '<div style="width:9px;height:9px;border-radius:50%;background:var(--green);flex-shrink:0;"></div><span style="font-size:12.5px;font-weight:700;color:var(--green)">All Safe</span>'; badge.style.background='#E8F5E9'; }
    showToast('SOS deactivated. All safe.');
  } else {
    sosActive = true;
    const badge = document.getElementById('sos-status-badge');
    if(badge){ badge.innerHTML = '<div style="width:9px;height:9px;border-radius:50%;background:var(--red);flex-shrink:0;"></div><span style="font-size:12.5px;font-weight:700;color:var(--red)">SOS ACTIVE</span>'; badge.style.background='#FFEBEE'; }
    showToast('🆘 SOS Alert Sent! Emergency contacts notified.');
  }
}
// EMERGENCY CONTACT ADD
function addEmergencyContact(){
  const name = document.getElementById('ec-name').value.trim();
  const phone = document.getElementById('ec-phone').value.trim();
  if(!name||!phone){showToast('Please fill in name and phone.');return;}
  document.getElementById('ec-name').value='';
  document.getElementById('ec-phone').value='';
  showToast('Emergency contact added: '+name);
}

// MODAL HELPERS
function openModal(id){document.getElementById(id).classList.add('open');}
function closeModal(id){document.getElementById(id).classList.remove('open');}

// NOTIFICATION PANEL
function openNotifPanel(){
  document.getElementById('notif-panel').classList.add('open');
  document.getElementById('notif-overlay').style.display='block';
  const badge=document.getElementById('notif-badge');
  if(badge)badge.style.display='none';
}
function closeNotifPanel(){
  document.getElementById('notif-panel').classList.remove('open');
  document.getElementById('notif-overlay').style.display='none';
}

// SOS TRIGGER — sends live location to the backend, which logs the alert
// and notifies the user's emergency contacts. Surfaces the cancel PIN.
function triggerSOS(){
  closeModal('modal-sos');
  showToast('🚨 Sending SOS…');

  var send = function(lat, lng){
    fetch('/notification/trigger-sos', {
      method: 'POST',
      headers: {'Content-Type':'application/json','X-Requested-With':'XMLHttpRequest'},
      body: JSON.stringify({latitude: lat, longitude: lng})
    })
    .then(function(r){ return r.json(); })
    .then(function(d){
      if(d && d.success){
        if(typeof sosActive !== 'undefined') sosActive = true;
        var badge = document.getElementById('sos-status-badge');
        if(badge){
          badge.innerHTML = '<div style="width:9px;height:9px;border-radius:50%;background:var(--red);flex-shrink:0;"></div><span style="font-size:12.5px;font-weight:700;color:var(--red)">SOS ACTIVE</span>';
          badge.style.background = '#FFEBEE';
        }
        showToast('🚨 SOS sent! Emergency contacts notified.');
        if(d.cancel_pin){
          alert('SOS alert active.\n\nYour cancel PIN is: ' + d.cancel_pin +
                '\n\nKeep this PIN to deactivate the alert from the Safety page.');
        }
      } else {
        showToast((d && d.message) || 'Could not send SOS.');
      }
    })
    .catch(function(){ showToast('Could not send SOS. Check your connection.'); });
  };

  if(navigator.geolocation){
    navigator.geolocation.getCurrentPosition(
      function(pos){ send(pos.coords.latitude, pos.coords.longitude); },
      function(){ send(null, null); },
      {timeout: 4000}
    );
  } else {
    send(null, null);
  }
}

// FORGOT PASSWORD
function submitForgot(){
  const email=document.getElementById('forgot-email').value.trim();
  if(!email){showToast('Please enter your email address.');return;}
  closeModal('modal-forgot');
  showToast('Reset link sent to '+email+' — check your inbox!');
}

// RESET PASSWORD
function submitReset(){
  const pw=document.getElementById('reset-new').value;
  const cf=document.getElementById('reset-confirm').value;
  if(!pw||pw.length<8){showToast('Password must be at least 8 characters.');return;}
  if(pw!==cf){showToast('Passwords do not match.');return;}
  closeModal('modal-reset');
  showToast('Password updated successfully!');
}

// EMERGENCY CONTACT SAVE
function saveEmergencyContact(){
  const name=document.getElementById('ec-name').value.trim();
  const phone=document.getElementById('ec-phone').value.trim();
  if(!name){showToast('Please enter a name.');return;}
  if(!phone||phone.length<8){showToast('Please enter a valid phone number.');return;}
  closeModal('modal-emergency-contact');
  showToast(name+' added as emergency contact!');
}

// LOGOUT
function confirmLogout(){openModal('modal-logout');}
function doLogout(){closeModal('modal-logout');goTo('login');showToast('Logged out successfully.');}

// Close modals on overlay click
document.querySelectorAll('.modal-overlay').forEach(overlay=>{
  overlay.addEventListener('click',function(e){if(e.target===this)this.classList.remove('open');});
});

// ── FEATURE MODAL HELPERS ──
function openFeatModal(id){
  document.getElementById(id).classList.add('open');
  document.getElementById(id).focus && document.getElementById(id).focus();
}
function closeFeatModal(id){
  document.getElementById(id).classList.remove('open');
}
// Close feat modals on overlay click
document.addEventListener('click',function(e){
  if(e.target && e.target.classList.contains('feat-modal-overlay')){
    e.target.classList.remove('open');
  }
});
// Close feat modals on Escape key
document.addEventListener('keydown',function(e){
  if(e.key==='Escape'){
    document.querySelectorAll('.feat-modal-overlay.open').forEach(m=>m.classList.remove('open'));
  }
});

// ── FRIEND AVAILABILITY ──
function pickSlot(el){
  document.querySelectorAll('.time-slot').forEach(s=>s.classList.remove('picked'));
  el.classList.add('picked');
  showToast('Time slot selected: '+el.textContent.replace('\n',' '));
}

// ── MIDPOINT CALCULATOR ──
// NOTE: Real calcMidpoint is defined in plan.html extra_js (async with geocoding).
// This stub is removed so the real implementation is used on the plan page.

// ── BUDGET FILTER ──
function updateBudget(val){
  const display=document.getElementById('budget-display');
  if(display)display.textContent='NPR '+parseInt(val).toLocaleString();
}
function setBudgetPreset(el,val){
  document.querySelectorAll('#modal-budget-filter .filter-chip').forEach(c=>c.classList.remove('active'));
  el.classList.add('active');
  const slider=document.querySelector('#modal-budget-filter input[type=range]');
  if(slider){slider.value=val;updateBudget(val);}
}

// ── AMBIENCE FILTER ──
function toggleAmbience(el){
  el.classList.toggle('active');
}

// ── RATING & REVIEW ──
let currentStars=0;
function setStars(n){
  currentStars=n;
  document.querySelectorAll('#star-row .rating-star').forEach((s,i)=>{
    s.textContent=i<n?'★':'☆';
    s.style.color=i<n?'var(--amber)':'var(--muted)';
  });
}
function submitReview(){
  const text=document.getElementById('review-text').value.trim();
  if(!currentStars){showToast('Please select a star rating!');return;}
  if(!text){showToast('Please write a short review!');return;}
  closeFeatModal('modal-rating-review');
  showToast('✅ Review submitted! Thanks for sharing.');
  setStars(0);
  document.getElementById('review-text').value='';
  currentStars=0;
}
function submitReviewSerial(){
  var text=document.getElementById('review-text').value.trim();
  if(!currentStars){showToast('Please select a star rating!');return;}
  if(!text){showToast('Please write a short review!');return;}
  showToast('✅ Review submitted! Thanks for sharing.');
  setStars(0);
  document.getElementById('review-text').value='';
  currentStars=0;
  serialNext('modal-rating-review');
}

// ── FAVOURITE PLACES ──
const favourites=new Set(['Himalayan Java Coffee','Museum Garden Café']);
function addFavourite(name){
  if(favourites.has(name)){showToast(name+' is already saved!');return;}
  favourites.add(name);
  document.getElementById('fav-count').textContent=favourites.size;
  const list=document.getElementById('fav-list');
  const card=document.createElement('div');
  card.className='restaurant-card saved-fav';
  card.innerHTML=`<div class="rest-emoji">☕</div><div style="flex:1"><div class="rest-name">${name}</div><div class="rest-meta">Just saved</div></div><button class="rest-fav-btn" onclick="removeFavourite(this,'${name}')" title="Remove">❤️</button>`;
  list.appendChild(card);
  document.getElementById('fav-empty').style.display='none';
  showToast('❤️ '+name+' saved to favourites!');
}
function removeFavourite(btn,name){
  favourites.delete(name);
  btn.closest('.restaurant-card').remove();
  document.getElementById('fav-count').textContent=favourites.size;
  if(favourites.size===0)document.getElementById('fav-empty').style.display='block';
  showToast('Removed from favourites.');
}
function toggleFav(btn,name){
  if(favourites.has(name)){
    favourites.delete(name);
    btn.textContent='🤍';
    showToast('Removed from favourites.');
  } else {
    favourites.add(name);
    btn.textContent='❤️';
    showToast('❤️ '+name+' saved to favourites!');
  }
}

function filterGallery(cat,btn){
  ['all','food','people','ambience'].forEach(function(t){
    var el=document.getElementById('gal-tab-'+t);
    if(!el)return;
    if(t===cat){el.style.background='var(--primary)';el.style.borderColor='var(--primary)';el.style.color='#fff';}
    else{el.style.background='transparent';el.style.borderColor='var(--border)';el.style.color='var(--muted)';}
  });
  document.querySelectorAll('.gal-card').forEach(function(c){
    c.style.display=(cat==='all'||c.dataset.cat===cat)?'':'none';
  });
}

/* ===== Section Break ===== */

// ═══════════════════════════════════════
//  PLAN MEETUP — Phase 1 → Phase 2
// ═══════════════════════════════════════
// NOTE: Real calcMidpoint and detectPMLocation are defined in plan.html extra_js.
// The main.js versions have been removed to avoid overriding the real implementations.

var selectedNearbyVenue = null;

function loadNearbyRestaurants(){
  var list = document.getElementById('nearby-venue-list');
  if(!list) return;
  var ctx = window.PLAN_CONTEXT || {};
  var mid = ctx.midpoint;
  if(!mid || !Number.isFinite(Number(mid.lat)) || !Number.isFinite(Number(mid.lng))){
    list.innerHTML = '<div style="font-size:13px;color:var(--muted);text-align:center;padding:14px 0;">Calculate the midpoint first.</div>';
    return;
  }
  list.innerHTML = '<div style="font-size:13px;color:var(--muted);text-align:center;padding:14px 0;">Loading nearby places...</div>';

  fetch('/place/api/nearby-midpoint?lat=' + mid.lat + '&lng=' + mid.lng + '&radius=100.0')
    .then(function(r){ return r.json(); })
    .then(function(data){
      if(!data.success || !data.restaurants.length){
        list.innerHTML = '<div style="font-size:13px;color:var(--muted);text-align:center;padding:14px 0;">No restaurants found.</div>';
        return;
      }
      selectedNearbyVenue = data.restaurants[0];
      list.innerHTML = data.restaurants.map(function(r, i){
        return '<div class="venue-row' + (i === 0 ? ' selected' : '') + '" data-id="' + r.id + '" onclick="selectNearbyVenue(' + r.id + ')">' +
          '<div class="venue-emoji">🍽️</div>' +
          '<div style="flex:1"><div class="venue-name">' + escapePlanHtml(r.name) + '</div>' +
          '<div class="venue-rating">⭐ ' + r.rating.toFixed(1) + ' · ' + r.distance_km.toFixed(2) + ' km · NPR ' + Math.round(r.avg_cost_per_person) + '</div></div>' +
        '</div>';
      }).join('');
    })
    .catch(function(){
      list.innerHTML = '<div style="font-size:13px;color:var(--muted);text-align:center;padding:14px 0;">Could not load restaurants.</div>';
    });
}

function selectNearbyVenue(id){
  selectedNearbyVenue = { id: id };
  document.querySelectorAll('#nearby-venue-list .venue-row').forEach(function(row){
    row.classList.toggle('selected', row.dataset.id === String(id));
  });
}

function setNearbyVenue(){
  if(!selectedNearbyVenue){
    showToast('Please select a restaurant.');
    return;
  }
  showToast('Venue updated!');
  completeSerialStep('modal-nearby-restaurants', 'venue selected');
}


function createMeetupAndProceed(){
  var title = document.getElementById('pm-title') ? document.getElementById('pm-title').value.trim() : '';
  if(!title){
    showToast('⚠️ Please enter a meetup title first!');
    document.getElementById('pm-title').focus();
    return;
  }
  // Show success toast then transition to advanced planning
  showToast('✅ Meetup "'+title+'" created! Now let\'s plan the details.');
  setTimeout(function(){
    document.getElementById('plan-phase-create').style.display = 'none';
    var adv = document.getElementById('plan-phase-advanced');
    adv.style.display = 'flex';
    // pre-fill the setup bar location with meetup title hint
  }, 600);
}

/* ===== Section Break ===== */

// ═══════════════════════════════════════
//  SETUP BAR — fill all fields to unlock
// ═══════════════════════════════════════
var MIDPOINTS = ['Patan Durbar Square','Garden of Dreams','Sankhamul Park','Naxal Central Park','Boudha Area'];
var midIdx = 0;

function checkSetupBar(){
  var l1  = document.getElementById('field-loc1') ? document.getElementById('field-loc1').value.trim() : 'Thamel';
  var l2  = document.getElementById('field-loc2') ? document.getElementById('field-loc2').value.trim() : '';
  var dt  = document.getElementById('field-datetime') ? document.getElementById('field-datetime').value : '';
  var ppl = document.getElementById('field-people') ? document.getElementById('field-people').value : '';
  var typ = document.getElementById('field-type') ? document.getElementById('field-type').value : '';

  markField('field-loc1',  !!l1);
  markField('field-loc2',  !!l2);
  markField('field-datetime', !!dt);
  markField('field-people',   !!ppl);
  markField('field-type',     !!typ);

  var btn = document.getElementById('setup-go-btn');
  if(!btn) return;
  var allDone = l2 && dt && ppl && typ;
  if(allDone){
    btn.classList.add('ready');
    btn.style.opacity = '1';
    btn.style.cursor  = 'pointer';
    btn.style.pointerEvents = 'all';
  } else {
    btn.classList.remove('ready');
    btn.style.opacity = '.35';
    btn.style.cursor  = 'not-allowed';
    btn.style.pointerEvents = 'none';
  }
}

function markField(id, filled){
  var inp = document.getElementById(id);
  if(!inp) return;
  var cell = inp.closest('.setup-field');
  if(filled){ inp.classList.add('done'); if(cell) cell.classList.add('filled'); }
  else       { inp.classList.remove('done'); if(cell) cell.classList.remove('filled'); }
}

function openSetupSummary(){
  var l2  = document.getElementById('field-loc2') ? document.getElementById('field-loc2').value.trim() : '';
  var dt  = document.getElementById('field-datetime') ? document.getElementById('field-datetime').value : '';
  var ppl = document.getElementById('field-people') ? document.getElementById('field-people').value : '';
  var typ = document.getElementById('field-type') ? document.getElementById('field-type').value : '';

  if(document.getElementById('sum-loc2')) document.getElementById('sum-loc2').textContent = l2;
  if(document.getElementById('sum-people')) document.getElementById('sum-people').textContent = ppl + ' people';
  if(document.getElementById('sum-type')) document.getElementById('sum-type').textContent = typ;

  if(dt && document.getElementById('sum-dt')){
    var d = new Date(dt);
    document.getElementById('sum-dt').textContent =
      d.toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric'}) +
      ' at ' + d.toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit'});
  }

  midIdx = (midIdx + 1) % MIDPOINTS.length;
  var mid = document.getElementById('sum-mid');
  if(mid){ mid.textContent = 'Calculating…'; setTimeout(function(){ mid.textContent = '📍 ' + MIDPOINTS[midIdx]; }, 600); }

  var overlay = document.getElementById('setup-summary-overlay');
  if(overlay) { overlay.style.display = 'flex'; }
}

function closeSetupSummary(){
  document.getElementById('setup-summary-overlay').style.display = 'none';
}

// close on overlay click
document.addEventListener('click', function(e){
  var overlay = document.getElementById('setup-summary-overlay');
  if(e.target === overlay) closeSetupSummary();
});

/* ===== Section Break ===== */

// ═══════════════════════════════════════
//  SERIAL PLANNER — clean rewrite
// ═══════════════════════════════════════
var STEPS = [
  { id:'modal-midpoint',           label:'Midpoint Meeting Calculator'     },
  { id:'modal-cuisine-preference', label:'Cuisine Preference Selection'     },
  { id:'modal-budget-filter',      label:'Budget-Based Restaurant Filter'   },
  { id:'modal-nearby-restaurants', label:'Nearby Restaurant Recommendations'},
  { id:'modal-restaurant-offers',  label:'Restaurant Offers Check'          }, 
  { id:'modal-ride-cost',          label:'Ride Cost Estimation'             }
];
var stepIdx = -1; // -1 = not started

/* ── helpers ── */
function _rawOpen(id){
  var el = document.getElementById(id);
  if(el) el.classList.add('open');
  if(id === 'modal-nearby-restaurants' && typeof window.refreshMidpointRestaurants === 'function'){
    window.refreshMidpointRestaurants();
  }
  if(id === 'modal-restaurant-offers' && typeof window.renderFeaturedRestaurantOffers === 'function'){
    window.renderFeaturedRestaurantOffers();
  }
  if(id === 'modal-budget-split' && typeof window.loadBudgetSplit === 'function'){
    window.loadBudgetSplit();
  }
  if(id === 'modal-multistop-route' && typeof window.loadMultiStopRoute === 'function'){
    window.loadMultiStopRoute();
  }
}


function _rawClose(id){
  var el = document.getElementById(id);
  if(el) el.classList.remove('open');
}

/* ── build the step list in the sidebar ── */
function buildSteps(){
  var list = document.getElementById('serial-steps-list');
  if(!list) return;
  list.innerHTML = '';
  STEPS.forEach(function(s, i){
    var d = document.createElement('div');
    d.className = 'serial-step-item';
    d.id = 'ssi-'+i;
    d.innerHTML =
      '<div class="step-circle" id="sc-'+i+'">'+(i+1)+'</div>'+
      '<span class="step-label" id="sl-'+i+'">'+s.label+'</span>'+
      '<span class="step-status" id="ss-'+i+'">○</span>';
    list.appendChild(d);
  });
}

/* ── update sidebar visuals ── */
function refreshSteps(){
  STEPS.forEach(function(_, i){
    var row = document.getElementById('ssi-'+i);
    var circ = document.getElementById('sc-'+i);
    var stat = document.getElementById('ss-'+i);
    if(!row) return;
    row.classList.remove('active','done');
    if(i < stepIdx){
      row.classList.add('done');
      if(stat) stat.textContent = '✓';
    } else if(i === stepIdx){
      row.classList.add('active');
      if(stat) stat.textContent = '▶';
      row.scrollIntoView({behavior:'smooth', block:'nearest'});
    } else {
      if(stat) stat.textContent = '○';
    }
  });
  // progress bar
  var pct = stepIdx < 0 ? 0 : Math.round((stepIdx / STEPS.length) * 100);
  var bar = document.getElementById('serial-progress');
  if(bar) bar.style.width = pct + '%';
  // badge
  var badge = document.getElementById('serial-step-badge');
  if(badge && stepIdx >= 0 && stepIdx < STEPS.length)
    badge.textContent = 'Step '+(stepIdx+1)+' of '+STEPS.length;
}

/* ── START ── */
function startSerialPlan(){
  stepIdx = 0;
  // swap panels
  document.getElementById('plan-start-card').style.display = 'none';
  document.getElementById('plan-active-card').style.display = 'flex';
  document.getElementById('plan-done-card').style.display = 'none';
  buildSteps();
  refreshSteps();
  // open first popup with tiny delay so panel transition is visible
  setTimeout(function(){ _rawOpen(STEPS[0].id); }, 200);
}

/* ── called by every modal button ── */
function serialNext(closingId){
  _rawClose(closingId);
  stepIdx++;
  if(stepIdx >= STEPS.length){
    finishSerialPlan();
    return;
  }
  refreshSteps();
  // slight delay between close and open so it feels like a real popup sequence
  setTimeout(function(){ _rawOpen(STEPS[stepIdx].id); }, 320);
}

/* ── FINISH ── */
function finishSerialPlan(){
  // close anything still open
  document.querySelectorAll('.feat-modal-overlay.open,.modal-overlay.open').forEach(function(m){ m.classList.remove('open'); });
  stepIdx = STEPS.length;
  // mark all done
  STEPS.forEach(function(_, i){
    var row = document.getElementById('ssi-'+i);
    var stat = document.getElementById('ss-'+i);
    if(row){ row.classList.remove('active'); row.classList.add('done'); }
    if(stat) stat.textContent = '✓';
  });
  var bar = document.getElementById('serial-progress');
  if(bar) bar.style.width = '100%';
  // swap to done card
  document.getElementById('plan-active-card').style.display = 'none';
  document.getElementById('plan-done-card').style.display = 'flex';
  showToast('🎉 Meetup fully planned! Ready to send invites.');
}

/* ── RESET ── goes all the way back to the create meetup form ── */
function resetSerialPlan(){
  stepIdx = -1;
  // Close all serial modals
  document.querySelectorAll('.feat-modal-overlay.open,.modal-overlay.open').forEach(function(m){ m.classList.remove('open'); });
  // Reset sidebar cards
  var startCard = document.getElementById('plan-start-card');
  var activeCard = document.getElementById('plan-active-card');
  var doneCard = document.getElementById('plan-done-card');
  if(startCard) startCard.style.display = 'flex';
  if(activeCard) activeCard.style.display = 'none';
  if(doneCard) doneCard.style.display = 'none';
  // Go back to phase 1
  var phase1 = document.getElementById('plan-phase-create');
  var phase2 = document.getElementById('plan-phase-advanced');
  if(phase1) phase1.style.display = 'block';
  if(phase2) phase2.style.display = 'none';
  // Clear the create form
  var titleEl = document.getElementById('pm-title');
  var descEl = document.getElementById('pm-desc');
  if(titleEl) titleEl.value = '';
  if(descEl) descEl.value = '';
}
/* ── EXIT TO MAP ── closes any open popup and returns to the map view,
   without sending the user back to the create-meetup form ── */
function exitSerialToMap(){
  stepIdx = -1;
  // Close all serial modals
  document.querySelectorAll('.feat-modal-overlay.open,.modal-overlay.open').forEach(function(m){ m.classList.remove('open'); });
  // Reset sidebar cards back to the "start" card (so re-opening starts fresh)
  var startCard = document.getElementById('plan-start-card');
  var activeCard = document.getElementById('plan-active-card');
  var doneCard = document.getElementById('plan-done-card');
  if(startCard) startCard.style.display = 'flex';
  if(activeCard) activeCard.style.display = 'none';
  if(doneCard) doneCard.style.display = 'none';
  // Stay on the map — do NOT touch plan-phase-create / plan-phase-advanced
}
/* ── × button always closes and exits back to the map; it never advances the serial flow ── */
var _baseFeatClose = closeFeatModal;
closeFeatModal = function(id){
  // If a serial flow is running, exit it entirely so the user lands back on the map.
  if(stepIdx >= 0 && stepIdx < STEPS.length && STEPS[stepIdx].id === id){
    exitSerialToMap();
  }
  _baseFeatClose(id);
};
/* ── × button always closes and exits the serial flow if one is active ── */
var _baseModalClose = closeModal;
closeModal = function(id){
  if(stepIdx >= 0 && stepIdx < STEPS.length && STEPS[stepIdx].id === id){
    exitSerialToMap();
  }
  _baseModalClose(id);
};

/* ── init step list on load ── */
document.addEventListener('DOMContentLoaded', buildSteps);
if(document.readyState !== 'loading') buildSteps();
// BUDGET SPLIT
let splitMode = 'equal';
function setSplitMode(mode, btn) {
  splitMode = mode;
  document.querySelectorAll('#modal-budget-split .plan-tool-btn').forEach(b => {
    b.style.borderColor = 'var(--border)';
    b.style.background = 'transparent';
    b.style.color = 'var(--text)';
    b.textContent = b.textContent.replace(' ✓','');
  });
  btn.style.borderColor = 'var(--blue)';
  btn.style.background = 'var(--blue-light)';
  btn.style.color = 'var(--blue)';
  btn.textContent += ' ✓';
  calcSplit();
}
function calcSplit() {
  const total = parseFloat(document.getElementById('budget-total').value) || 0;
  const members = document.querySelectorAll('#split-dynamic-members .split-member-row, #split-members .split-member-row');
  const n = members.length;
  const perPerson = Math.floor(total / n);
  const remainder = total - perPerson * (n - 1);
  members.forEach((row, i) => {
    const amt = row.querySelector('.split-amount');
    if (amt) amt.textContent = 'NPR ' + (i === n-1 ? remainder : perPerson).toLocaleString();
  });
  const summary = document.getElementById('split-dynamic-summary') || document.getElementById('split-summary');
  if (summary) summary.textContent = 'Equal split: NPR ' + perPerson.toLocaleString() + ' / person';
}

// CUISINE PREFERENCE
function toggleCuisine(btn) {
  const active = btn.classList.contains('selected');
  if (active) {
    btn.classList.remove('selected');
    btn.style.borderColor = 'var(--border)';
    btn.style.background = 'var(--input-bg)';
    btn.style.color = 'var(--text)';
  } else {
    btn.classList.add('selected');
    btn.style.borderColor = 'var(--blue)';
    btn.style.background = 'var(--blue-light)';
    btn.style.color = 'var(--blue)';
  }
}
function selectPriceRange(btn, mode) {
  document.querySelectorAll('#modal-cuisine-pref .plan-tool-btn').forEach(b => {
    b.style.borderColor = 'var(--border)';
    b.style.background = 'transparent';
    b.style.color = 'var(--text)';
    b.textContent = b.textContent.replace(' ✓','');
  });
  btn.style.borderColor = 'var(--blue)';
  btn.style.background = 'var(--blue-light)';
  btn.style.color = 'var(--blue)';
  btn.textContent += ' ✓';
}

// GROUP CHAT SEND
function sendChatMsg() {
  const input = document.getElementById('chat-input');
  const msg = (input.value || '').trim();
  if (!msg) return;
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.style.cssText = 'display:flex;gap:8px;align-items:flex-start;flex-direction:row-reverse;';
  const now = new Date();
  const time = now.getHours() + ':' + String(now.getMinutes()).padStart(2,'0');
  div.innerHTML = `<div class="avatar" style="width:28px;height:28px;background:var(--primary);font-size:10px;flex-shrink:0;">S</div>
    <div style="align-items:flex-end;display:flex;flex-direction:column;">
      <div style="font-size:10px;color:var(--muted);margin-bottom:2px;">You · ${time}</div>
      <div style="background:var(--primary);color:#fff;border-radius:10px 0 10px 10px;padding:8px 11px;font-size:12.5px;max-width:180px;">${msg}</div>
    </div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  input.value = '';
}

/* ===== Section Break ===== */

/* Edit Profile Modal tab switching */
function switchEPTab(tab) {
  const tabs = ['profile','password','appearance'];
  tabs.forEach(t => {
    const btn = document.getElementById('ep-tab-' + t);
    const panel = document.getElementById('ep-panel-' + t);
    if (t === tab) {
      btn.style.background = 'rgba(255,255,255,.95)';
      btn.style.color = '#14322A';
      panel.style.display = 'block';
    } else {
      btn.style.background = 'rgba(255,255,255,.15)';
      btn.style.color = 'rgba(255,255,255,.85)';
      panel.style.display = 'none';
    }
  });
}
/* Final Meetup Summary popup */
function openFinalSummary(){
  // Pull meetup title from create form if available
  var titleEl = document.getElementById('pm-title');
  var title = (titleEl && titleEl.value.trim()) ? titleEl.value.trim() : 'Kathmandu Hangout';
  document.getElementById('fsum-title').textContent = title;

  // Pull venue from the venue selection modal if something was selected
  var selectedVenue = document.querySelector('.venue-row.selected .venue-name');
  document.getElementById('fsum-venue').textContent = selectedVenue ? selectedVenue.textContent : 'Himalayan Java Coffee';

  // Midpoint
  var midEl = document.getElementById('sum-mid');
  var mid = (midEl && midEl.textContent && midEl.textContent !== 'Calculating…') ? midEl.textContent : '📍 Asan Tole';
  document.getElementById('fsum-mid').textContent = mid;

  // Steps completed — count how many serial steps are marked done
  var doneSteps = document.querySelectorAll('.serial-step-item.done');
  var stepLabels = [];
  doneSteps.forEach(function(s){
    var lbl = s.querySelector('.step-label');
    if(lbl) stepLabels.push(lbl.textContent.trim());
  });
  if(stepLabels.length > 0){
    var container = document.getElementById('fsum-steps');
    container.innerHTML = '';
    stepLabels.forEach(function(l){
      var span = document.createElement('span');
      span.style.cssText = 'background:var(--green-light);color:var(--green);border:1px solid rgba(14,106,58,.2);font-size:11px;font-weight:700;padding:4px 10px;border-radius:20px;';
      span.textContent = '✓ ' + l;
      container.appendChild(span);
    });
  }

  openModal('modal-final-summary');
}

/* Place Rating & Feedback Modal */
var _prateVal = 0;
var _prateLabels = ['','Disappointing 😕','Not Great 😐','It was OK 🙂','Really Enjoyed It 😊','Absolutely Loved It! 🤩'];
function openPlaceRating(icon, name, meta, existingRating) {
  document.getElementById('prate-icon').textContent = icon;
  document.getElementById('prate-name').textContent = name;
  document.getElementById('prate-meta').textContent = meta;
  _prateVal = Math.round(existingRating) || 0;
  updatePRateStars(_prateVal);
  document.getElementById('prate-feedback').value = '';
  document.querySelectorAll('.prate-tag').forEach(t => {
    t.style.background = 'var(--input-bg)';
    t.style.borderColor = 'var(--border)';
    t.style.color = 'var(--text)';
  });
  openModal('modal-place-rating');
}
function setPRateStar(val) {
  _prateVal = val;
  updatePRateStars(val);
}
function updatePRateStars(val) {
  document.querySelectorAll('.prate-star').forEach(function(s) {
    var sv = parseInt(s.getAttribute('data-val'));
    if (sv <= val) {
      s.style.filter = 'none';
      s.style.opacity = '1';
      s.style.transform = 'scale(1.15)';
    } else {
      s.style.filter = 'grayscale(1)';
      s.style.opacity = '.4';
      s.style.transform = 'scale(1)';
    }
  });
  document.getElementById('prate-label').textContent = _prateLabels[val] || '';
}
function togglePRateTag(el) {
  var active = el.getAttribute('data-active') === '1';
  if (active) {
    el.setAttribute('data-active','0');
    el.style.background = 'var(--input-bg)';
    el.style.borderColor = 'var(--border)';
    el.style.color = 'var(--text)';
  } else {
    el.setAttribute('data-active','1');
    el.style.background = 'var(--green-light)';
    el.style.borderColor = 'var(--green)';
    el.style.color = 'var(--green)';
  }
}
function submitPlaceRating() {
  if (!_prateVal) { showToast('⭐ Please select a star rating first!'); return; }
  var name = document.getElementById('prate-name').textContent;
  closeModal('modal-place-rating');
  showToast('✅ Thanks! Your rating for ' + name + ' has been saved.');
}

function setEPTheme(theme) {
  const lightBtn = document.getElementById('ep-theme-light');
  const darkBtn = document.getElementById('ep-theme-dark');
  if (theme === 'light') {
    lightBtn.style.border = '2px solid var(--blue)';
    lightBtn.style.background = 'var(--blue-light)';
    lightBtn.style.color = 'var(--blue)';
    darkBtn.style.border = '2px solid var(--border)';
    darkBtn.style.background = 'var(--input-bg)';
    darkBtn.style.color = 'var(--muted)';
    document.documentElement.setAttribute('data-theme','light');
  } else {
    darkBtn.style.border = '2px solid var(--blue)';
    darkBtn.style.background = '#1a2e40';
    darkBtn.style.color = '#7ec8e3';
    lightBtn.style.border = '2px solid var(--border)';
    lightBtn.style.background = 'var(--input-bg)';
    lightBtn.style.color = 'var(--muted)';
    document.documentElement.setAttribute('data-theme','dark');
  }
  currentTheme = theme;
  try { localStorage.setItem('bhetamla-theme', theme); } catch(e) {}
}
