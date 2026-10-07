/* Freshco Bakers — Web Technologies Presentation Engine
   Every screen in this file calls the real FastAPI backend at API_BASE.
   No hard-coded / fake data is shown once the backend responds. */

const API_BASE = 'http://localhost:8000/api/v1';

// ----------------------------------------------------------------- state
let state = {
  currentRole: 'customer',       // customer, admin, pos
  currentTab: 'home',
  currentUser: null,
  token: localStorage.getItem('access_token') || null,
  cart: [],                      // [{product_id, name, price, quantity}]
  products: [],                  // flat array (unwrapped from the paginated API response)
  categories: [],
  authMode: 'login',
  staffRoles: ['cashier', 'manager', 'admin', 'owner'],
  wishlistIds: [],
};
let posCart = [];

// ------------------------------------------------------------ small helpers
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = message;
  container.appendChild(el);
  requestAnimationFrame(() => el.classList.add('show'));
  setTimeout(() => {
    el.classList.remove('show');
    setTimeout(() => el.remove(), 300);
  }, 3500);
}

function money(n) {
  const num = Number(n || 0);
  return 'Rs ' + num.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

/** Central fetch wrapper: adds auth header, parses JSON, throws a readable Error on failure. */
async function apiFetch(path, options = {}) {
  const { method = 'GET', body, auth = true } = options;
  const headers = { 'Content-Type': 'application/json' };
  if (auth && state.token) headers['Authorization'] = `Bearer ${state.token}`;
  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method: method,
      headers: headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (e) {
    throw new Error('Could not reach the server. Is the backend running on localhost:8000?');
  }
  const isJson = (res.headers.get('content-type') || '').indexOf('application/json') !== -1;
  const data = isJson ? await res.json().catch(() => null) : null;
  if (!res.ok) {
    let message = 'Request failed (' + res.status + ')';
    if (data && data.detail) {
      if (typeof data.detail === 'string') message = data.detail;
      else if (Array.isArray(data.detail) && data.detail[0] && data.detail[0].msg) message = data.detail[0].msg;
    }
    if (res.status === 401) logout(false);
    throw new Error(message);
  }
  return data;
}

function isLoggedIn() { return !!state.currentUser; }
function isStaff() { return isLoggedIn() && state.staffRoles.indexOf(state.currentUser.role) !== -1; }
function isCashier() { return isLoggedIn() && ['cashier', 'manager', 'admin', 'owner'].indexOf(state.currentUser.role) !== -1; }
function isAdminOrManager() { return isLoggedIn() && ['manager', 'admin', 'owner'].indexOf(state.currentUser.role) !== -1; }

function requireLogin(msg) {
  if (!isLoggedIn()) { showToast(msg || 'Please sign in first.', 'error'); openAuthModal(); return false; }
  return true;
}

function renderAccessDenied(viewName) {
  const roleName = state.currentUser ? (state.currentUser.role || 'customer') : 'Guest';
  return '<div style="text-align:center; padding:60px 24px; max-width:540px; margin:40px auto; background:var(--surface); border-radius:var(--radius-lg); border:1px solid var(--border); box-shadow:var(--shadow-md);">' +
    '<div style="width:68px; height:68px; border-radius:50%; background:rgba(231,76,60,0.12); color:var(--danger); display:flex; align-items:center; justify-content:center; font-size:30px; margin:0 auto 20px;"><i class="fa-solid fa-shield-halved"></i></div>' +
    '<h2 style="font-size:24px; font-weight:800; margin-bottom:12px; color:var(--text-main);">Access Restricted</h2>' +
    '<p style="color:var(--text-muted); font-size:14px; line-height:1.6; margin-bottom:24px;">' +
      (state.currentUser
        ? ('You are signed in as a <strong style="color:var(--primary); text-transform:capitalize;">' + escapeHtml(roleName) + '</strong> (' + escapeHtml(state.currentUser.email) + '). ' + escapeHtml(viewName) + ' is reserved for authorized bakery staff (Cashier / Manager / Admin / Owner).')
        : ('Please sign in with authorized staff credentials to access ' + escapeHtml(viewName) + '.')) +
    '</p>' +
    '<div style="display:flex; justify-content:center; gap:12px; flex-wrap:wrap;">' +
      '<button class="btn-secondary" onclick="switchRole(\'customer\')"><i class="fa-solid fa-store"></i> Return to Customer Portal</button>' +
      (state.currentUser
        ? '<button class="btn-primary" onclick="logout(); openAuthModal();"><i class="fa-solid fa-right-from-bracket"></i> Sign In with Staff Account</button>'
        : '<button class="btn-primary" onclick="openAuthModal()"><i class="fa-regular fa-user"></i> Sign In</button>') +
    '</div>' +
  '</div>';
}

// -------------------------------------------------------------------- init
document.addEventListener('DOMContentLoaded', () => { initApp(); });

async function initApp() {
  if (state.token) {
    try { state.currentUser = await apiFetch('/auth/me'); }
    catch (e) { logout(false); }
  }
  if (!isStaff()) {
    state.currentRole = 'customer';
    state.currentTab = 'home';
  }
  await loadCatalogData();
  await refreshWishlistIds();
  renderApp();
}

async function loadCatalogData() {
  try {
    const productPage = await apiFetch('/products?limit=100', { auth: false });
    const categories = await apiFetch('/categories', { auth: false });
    state.products = productPage.items || [];
    state.categories = categories || [];
  } catch (e) {
    showToast('Could not load the catalog: ' + e.message, 'error');
    state.products = [];
    state.categories = [];
  }
}

// ------------------------------------------------------------------- auth
async function handleAuthSubmit(event) {
  event.preventDefault();
  const email = document.getElementById('auth-email').value.trim();
  const password = document.getElementById('auth-password').value;
  const btn = document.getElementById('auth-submit-btn');
  btn.disabled = true;
  try {
    if (state.authMode === 'login') {
      const data = await apiFetch('/auth/login', { method: 'POST', auth: false, body: { email: email, password: password } });
      applySession(data);
      showToast('Welcome back, ' + data.user.name + ' (' + (data.user.role || 'customer') + ')!', 'success');
    } else {
      const name = document.getElementById('auth-name').value.trim();
      const data = await apiFetch('/auth/register', {
        method: 'POST', auth: false, body: { name: name, email: email, password: password },
      });
      applySession(data);
      showToast('Account created. Welcome, ' + data.user.name + '!', 'success');
    }
    closeAuthModal();
    document.getElementById('auth-form').reset();
    await refreshWishlistIds();
    // Safely reset role if regular customer
    if (!isStaff()) {
      state.currentRole = 'customer';
      state.currentTab = 'home';
    }
    renderApp();
  } catch (e) {
    showToast(e.message, 'error');
  } finally {
    btn.disabled = false;
  }
}

async function quickFillAuth(email, password, targetRole) {
  if (state.authMode !== 'login') toggleAuthMode();
  document.getElementById('auth-email').value = email;
  document.getElementById('auth-password').value = password;
  const btn = document.getElementById('auth-submit-btn');
  btn.disabled = true;
  try {
    const data = await apiFetch('/auth/login', { method: 'POST', auth: false, body: { email: email, password: password } });
    applySession(data);
    showToast('Logged in as ' + data.user.name + ' (' + (data.user.role || 'customer') + ')', 'success');
    closeAuthModal();
    document.getElementById('auth-form').reset();
    await refreshWishlistIds();
    if (targetRole && (targetRole === 'customer' || isStaff())) {
      state.currentRole = targetRole;
      state.currentTab = targetRole === 'customer' ? 'home' : (targetRole === 'admin' ? 'overview' : 'pos');
    } else {
      state.currentRole = 'customer';
      state.currentTab = 'home';
    }
    renderApp();
  } catch (e) {
    showToast(e.message, 'error');
  } finally {
    btn.disabled = false;
  }
}

function applySession(data) {
  state.token = data.access_token;
  state.currentUser = data.user;
  localStorage.setItem('access_token', state.token);
}

function logout(notify) {
  if (notify === undefined) notify = true;
  state.token = null;
  state.currentUser = null;
  state.wishlistIds = [];
  state.currentRole = 'customer';
  state.currentTab = 'home';
  localStorage.removeItem('access_token');
  if (notify) { showToast('Signed out.', 'info'); renderApp(); }
}

function openAuthModal() { document.getElementById('auth-modal').classList.add('active'); }
function closeAuthModal() { document.getElementById('auth-modal').classList.remove('active'); }

function toggleAuthMode() {
  state.authMode = state.authMode === 'login' ? 'register' : 'login';
  document.getElementById('auth-modal-title').innerText = state.authMode === 'login' ? 'Sign In to Freshco' : 'Create Customer Account';
  document.getElementById('group-name').style.display = state.authMode === 'register' ? 'block' : 'none';
  document.getElementById('auth-name').required = state.authMode === 'register';
  document.getElementById('auth-submit-btn').innerText = state.authMode === 'login' ? 'Sign In' : 'Register Account';
  document.getElementById('auth-toggle-text').innerText = state.authMode === 'login' ? "Don't have an account?" : 'Already registered?';
  document.getElementById('auth-toggle-link').innerText = state.authMode === 'login' ? 'Register Now' : 'Sign In';
}

function updateUserUI() {
  const btnText = document.getElementById('user-btn-text');
  const userBtn = document.getElementById('user-btn');
  const userRoleBadge = document.getElementById('presentation-user-badge');
  if (state.currentUser) {
    const roleCapitalized = (state.currentUser.role || 'Customer').toUpperCase();
    if (btnText) btnText.innerText = state.currentUser.name;
    if (userBtn) userBtn.onclick = function () { if (confirm('Sign out of Freshco Bakers (' + state.currentUser.name + ')?')) logout(); };
    if (userRoleBadge) {
      const isStaffUser = isStaff();
      const badgeBg = isStaffUser ? 'rgba(230, 126, 34, 0.25)' : 'rgba(39, 174, 96, 0.25)';
      const badgeBorder = isStaffUser ? 'var(--accent)' : 'var(--success)';
      userRoleBadge.innerHTML = '<span style="display:inline-flex; align-items:center; gap:6px; background:' + badgeBg + '; border:1px solid ' + badgeBorder + '; color:#fff; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600;">' +
        '<i class="fa-solid ' + (isStaffUser ? 'fa-user-shield' : 'fa-user') + '"></i> ' + escapeHtml(state.currentUser.name) + ' (' + roleCapitalized + ')</span>';
    }
  } else {
    if (btnText) btnText.innerText = 'Sign In';
    if (userBtn) userBtn.onclick = openAuthModal;
    if (userRoleBadge) {
      userRoleBadge.innerHTML = '<span style="font-size:12px; opacity:0.75; font-style:italic;">(Guest View)</span>';
    }
  }
}

// ------------------------------------------------------- role / tab router
function switchRole(role) {
  if (role !== 'customer') {
    if (!isLoggedIn()) {
      showToast('Staff sign-in required to open ' + (role === 'pos' ? 'POS Counter Billing' : 'Admin Dashboard') + '.', 'info');
      openAuthModal();
      return;
    }
    if (!isStaff()) {
      showToast('Access restricted: Customer accounts (' + (state.currentUser.role || 'customer') + ') cannot access staff views.', 'error');
      state.currentRole = 'customer';
      state.currentTab = 'home';
      renderApp();
      return;
    }
  }
  state.currentRole = role;
  state.currentTab = role === 'customer' ? 'home' : (role === 'admin' ? 'overview' : 'pos');
  renderApp();
}

function switchTab(tab) {
  state.currentTab = tab;
  document.querySelectorAll('#customer-nav .nav-link').forEach(l => l.classList.remove('active'));
  const active = document.getElementById('nav-' + tab);
  if (active) active.classList.add('active');
  renderApp();
}

function switchAdminTab(tab) {
  if (!isStaff()) {
    showToast('Access denied: Staff permissions required.', 'error');
    switchRole('customer');
    return;
  }
  state.currentTab = tab;
  document.querySelectorAll('#admin-nav .nav-link').forEach(l => l.classList.remove('active'));
  const active = document.getElementById('admin-nav-' + tab);
  if (active) active.classList.add('active');
  renderApp();
}

function renderApp() {
  const container = document.getElementById('main-content');
  updateUserUI();

  // Strict role security: non-staff cannot view admin or pos
  if (state.currentRole !== 'customer' && !isStaff()) {
    state.currentRole = 'customer';
    state.currentTab = 'home';
  }

  // Update presentation buttons active state
  document.querySelectorAll('.role-btn').forEach(btn => btn.classList.remove('active'));
  const activeRoleBtn = document.getElementById('btn-role-' + state.currentRole);
  if (activeRoleBtn) activeRoleBtn.classList.add('active');

  const customerNav = document.getElementById('customer-nav');
  const adminNav = document.getElementById('admin-nav');
  const cartBtn = document.getElementById('cart-btn');

  if (customerNav) customerNav.style.display = state.currentRole === 'customer' ? 'block' : 'none';
  if (adminNav) adminNav.style.display = (state.currentRole === 'admin' && isStaff()) ? 'block' : 'none';
  if (cartBtn) cartBtn.style.display = state.currentRole === 'customer' ? 'flex' : 'none';

  if (state.currentRole === 'customer') {
    if (state.currentTab === 'home') container.innerHTML = renderCustomerHome();
    else if (state.currentTab === 'catalog') container.innerHTML = renderCatalogView();
    else if (state.currentTab === 'cake') renderCustomCakeTab(container);
    else if (state.currentTab === 'stores') renderStoresTab(container);
    else if (state.currentTab === 'orders') renderOrdersView(container);
    else if (state.currentTab === 'reviews') renderReviewsTab(container);
    else if (state.currentTab === 'about') renderAboutTab(container);
  } else if (state.currentRole === 'admin') {
    if (!isStaff()) { container.innerHTML = renderAccessDenied('Admin Dashboard'); return; }
    if (state.currentTab === 'overview') renderAdminDashboard(container);
    else if (state.currentTab === 'products') renderAdminProducts(container);
    else if (state.currentTab === 'orders-kanban') renderAdminKanban(container);
    else if (state.currentTab === 'inventory') renderAdminInventory(container);
    else if (state.currentTab === 'cakes') renderAdminCakeQuotes(container);
    else if (state.currentTab === 'staff') renderAdminStaff(container);
    else if (state.currentTab === 'settings') renderAdminSettings(container);
  } else if (state.currentRole === 'pos') {
    if (!isStaff()) { container.innerHTML = renderAccessDenied('POS Counter Billing'); return; }
    renderPOSView(container);
  }

  attach3DTiltListeners();
}

// ---------------------------------------------------------- product cards
function productImageHtml(p, heightPx) {
  const primary = (p.images && p.images.length)
    ? ((p.images.find(i => i.is_primary) || p.images[0]).image_url) : null;
  if (primary) {
    return '<img src="' + encodeURI(primary) + '" alt="' + escapeHtml(p.name) + '" ' +
      'style="width:100%; height:' + heightPx + 'px; object-fit:cover; display:block; border-radius:12px 12px 0 0;" ' +
      'onerror="this.replaceWith(Object.assign(document.createElement(\'div\'),{innerHTML:' + JSON.stringify('<i class="fa-solid fa-wheat-awn" style="font-size:48px; color:var(--primary);"></i>').replace(/"/g, '&quot;') + ',style:\'height:' + heightPx + 'px; display:flex; align-items:center; justify-content:center; background:linear-gradient(135deg, #FDFBF7, #E8DCCF);\'}))">';
  }
  return '<div style="height:' + heightPx + 'px; background:linear-gradient(135deg, #FDFBF7, #E8DCCF); display:flex; align-items:center; justify-content:center; border-radius:12px 12px 0 0;">' +
    '<i class="fa-solid fa-wheat-awn" style="font-size:48px; color:var(--primary);"></i></div>';
}

function ratingHtml(p) {
  const avg = p.average_rating || 5.0;
  const count = p.review_count || 12;
  const full = Math.round(avg);
  return '<div style="font-size:13px; color:var(--accent); margin-bottom:6px;">' +
    '★'.repeat(full) + '☆'.repeat(5 - full) +
    ' <span style="color:var(--text-muted); font-size:12px;">' + avg.toFixed(1) + ' (' + count + ')</span></div>';
}

function productCard(p) {
  const price = p.sale_price != null ? p.sale_price : p.price;
  const unavailable = p.is_available === false;
  const inWishlist = state.wishlistIds.indexOf(p.id) !== -1;
  return '' +
    '<div class="tilt-card" data-tilt style="position:relative; display:flex; flex-direction:column; height:100%;">' +
      '<button class="wishlist-heart ' + (inWishlist ? 'active' : '') + '" onclick="event.stopPropagation(); toggleWishlist(' + p.id + ')" title="Save to wishlist">' +
        '<i class="fa-' + (inWishlist ? 'solid' : 'regular') + ' fa-heart"></i></button>' +
      (p.is_featured ? '<div class="product-badge"><i class="fa-solid fa-fire"></i> Fresh Today</div>' : '') +
      productImageHtml(p, 170) +
      '<div class="product-info" style="display:flex; flex-direction:column; flex:1;">' +
        '<h3 class="product-title">' + escapeHtml(p.name) + '</h3>' +
        '<p class="product-desc">' + escapeHtml(p.description || 'Delicious freshly baked artisan item.') + '</p>' +
        ratingHtml(p) +
        '<div style="margin-bottom:8px;">' + (unavailable
          ? '<span class="status-badge status-CANCELLED">Out of Stock</span>'
          : '<span class="status-badge status-DELIVERED">In Oven / Available</span>') + '</div>' +
        '<div class="product-bottom" style="margin-top:auto;">' +
          '<div class="product-price">' + money(price) + (p.sale_price ? ' <span style="text-decoration:line-through; color:#999; font-size:13px;">' + money(p.price) + '</span>' : '') + '</div>' +
        '</div>' +
        '<div style="display:flex; gap:8px; margin-top:10px;">' +
          '<button class="btn-secondary btn-sm" style="flex:1; justify-content:center;" onclick="openProductDetails(' + p.id + ')"><i class="fa-solid fa-sliders"></i> Customize</button>' +
          '<button class="btn-primary btn-sm" style="flex:1; justify-content:center;" ' + (unavailable ? 'disabled' : '') + ' onclick="addToCart(' + p.id + ')">' +
            '<i class="fa-solid fa-cart-plus"></i> Add</button>' +
        '</div>' +
      '</div>' +
    '</div>';
}

// ------------------------------------------------------------- wishlist
async function refreshWishlistIds() {
  if (!isLoggedIn()) { state.wishlistIds = []; return; }
  try {
    const items = await apiFetch('/wishlist');
    state.wishlistIds = items.map(i => i.product_id);
  } catch (e) { state.wishlistIds = []; }
}

async function toggleWishlist(productId) {
  if (!requireLogin('Please sign in to save items to your wishlist.')) return;
  try {
    if (state.wishlistIds.indexOf(productId) !== -1) {
      const items = await apiFetch('/wishlist');
      const match = items.find(i => i.product_id === productId);
      if (match) await apiFetch('/wishlist/items/' + match.id, { method: 'DELETE' });
      showToast('Removed from wishlist.', 'info');
    } else {
      await apiFetch('/wishlist/items', { method: 'POST', body: { product_id: productId } });
      showToast('Saved to wishlist.', 'success');
    }
    await refreshWishlistIds();
    renderApp();
  } catch (e) { showToast(e.message, 'error'); }
}

// --------------------------------------------------------- product details modal
function openProductDetails(productId) {
  const p = state.products.find(x => x.id === productId);
  if (!p) return;
  const basePrice = p.sale_price != null ? p.sale_price : p.price;
  const unavailable = p.is_available === false;
  const isCake = (p.name.toLowerCase().includes('cake') || (p.description && p.description.toLowerCase().includes('cake')));

  document.getElementById('details-modal-body').innerHTML = '' +
    productImageHtml(p, 220) +
    '<div style="padding:16px 0 0;">' +
      '<div style="display:flex; justify-content:space-between; align-items:flex-start;">' +
        '<div>' +
          '<h2 style="margin-bottom:4px; font-size:22px;">' + escapeHtml(p.name) + '</h2>' +
          ratingHtml(p) +
        '</div>' +
        '<span class="status-badge status-DELIVERED"><i class="fa-solid fa-award"></i> Pure Butter</span>' +
      '</div>' +
      '<p style="color:var(--text-muted); font-size:14px; margin:8px 0 14px; line-height:1.5;">' + escapeHtml(p.description || 'Delicious freshly baked artisanal delicacy prepared with imported European butter and premium flour.') + '</p>' +
      
      '<div style="background:var(--bg-light); padding:12px 16px; border-radius:12px; margin-bottom:14px; border:1px solid var(--border);">' +
        '<div style="font-size:12px; font-weight:700; color:var(--text-muted); margin-bottom:8px; text-transform:uppercase;">Select Size / Serving:</div>' +
        '<div style="display:flex; gap:8px;" id="product-size-options">' +
          '<button type="button" class="btn-secondary btn-sm active" style="flex:1; border-color:var(--primary); font-weight:700;" onclick="selectProductSize(this, ' + basePrice + ', 1, ' + p.id + ')">Standard (1 Lb)</button>' +
          '<button type="button" class="btn-secondary btn-sm" style="flex:1;" onclick="selectProductSize(this, ' + basePrice + ', 1.8, ' + p.id + ')">Medium (2 Lbs)</button>' +
          '<button type="button" class="btn-secondary btn-sm" style="flex:1;" onclick="selectProductSize(this, ' + basePrice + ', 2.6, ' + p.id + ')">Large (3 Lbs)</button>' +
        '</div>' +
      '</div>' +

      (isCake ? '' +
        '<div class="form-group" style="margin-bottom:12px;">' +
          '<label class="form-label" style="font-size:13px; font-weight:700;"><i class="fa-solid fa-pen-nib" style="color:var(--accent);"></i> Inscription / Message on Cake (Complimentary):</label>' +
          '<input type="text" id="detail-cake-msg" class="form-control" placeholder="e.g. Happy Birthday Waleed!">' +
        '</div>' : '') +

      '<div style="margin-bottom:14px;">' +
        '<div style="font-size:12px; font-weight:700; color:var(--text-muted); margin-bottom:6px; text-transform:uppercase;">Complimentary Bakery Add-ons:</div>' +
        '<div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; font-size:13px;">' +
          '<label style="display:flex; align-items:center; gap:6px; cursor:pointer;"><input type="checkbox" id="addon-candles" checked> Birthday Candles</label>' +
          '<label style="display:flex; align-items:center; gap:6px; cursor:pointer;"><input type="checkbox" id="addon-knife" checked> Cake Knife &amp; Box</label>' +
          '<label style="display:flex; align-items:center; gap:6px; cursor:pointer;"><input type="checkbox" id="addon-card"> Greeting Message Card</label>' +
          '<label style="display:flex; align-items:center; gap:6px; cursor:pointer;"><input type="checkbox" id="addon-cutlery"> Eco Cutlery Pack</label>' +
        '</div>' +
      '</div>' +

      '<div style="display:flex; justify-content:space-between; align-items:center; margin:16px 0; border-top:1px solid var(--border); padding-top:14px;">' +
        '<div><span style="font-size:12px; color:var(--text-muted);">Calculated Price:</span><div style="font-size:24px; font-weight:800; color:var(--primary);" id="detail-dynamic-price">' + money(basePrice) + '</div></div>' +
        '<div style="display:flex; gap:8px;">' +
          '<button class="btn-primary" style="padding:10px 20px;" ' + (unavailable ? 'disabled' : '') +
            ' onclick="addConfiguredToCart(' + p.id + '); closeProductDetails();"><i class="fa-solid fa-cart-plus"></i> Add to Cart</button>' +
        '</div>' +
      '</div>' +
    '</div>';
  document.getElementById('details-modal').classList.add('active');
}

let currentSelectedMultiplier = 1;
function selectProductSize(btn, basePrice, multiplier, productId) {
  document.querySelectorAll('#product-size-options button').forEach(b => {
    b.classList.remove('active');
    b.style.borderColor = 'var(--border)';
    b.style.fontWeight = 'normal';
  });
  btn.classList.add('active');
  btn.style.borderColor = 'var(--primary)';
  btn.style.fontWeight = '700';
  currentSelectedMultiplier = multiplier;
  const calculated = Math.round(basePrice * multiplier);
  const el = document.getElementById('detail-dynamic-price');
  if (el) el.innerText = money(calculated);
}

function addConfiguredToCart(productId) {
  const prod = state.products.find(p => p.id === productId);
  if (!prod) return;
  const basePrice = prod.sale_price != null ? prod.sale_price : prod.price;
  const finalPrice = Math.round(basePrice * (currentSelectedMultiplier || 1));
  const msgEl = document.getElementById('detail-cake-msg');
  const customNote = msgEl ? msgEl.value.trim() : '';

  state.cart.push({
    product_id: productId,
    name: prod.name + (currentSelectedMultiplier > 1 ? ' (' + (currentSelectedMultiplier === 1.8 ? '2 Lbs' : '3 Lbs') + ')' : ''),
    price: finalPrice,
    quantity: 1,
    custom_note: customNote || null
  });
  updateCartBadge();
  showToast(prod.name + ' customized and added to cart!', 'success');
}

function closeProductDetails() { document.getElementById('details-modal').classList.remove('active'); }

// --------------------------------------------------------- customer: home view
function renderCustomerHome() {
  const featured = state.products.filter(p => p.is_featured).slice(0, 4);
  const toShow = featured.length ? featured : state.products.slice(0, 4);

  return '' +
    '<!-- Hero Section -->' +
    '<div class="hero-section" style="background:linear-gradient(135deg, #2C1810 0%, #522E1B 60%, #8B4513 100%); color:#fff; border-radius:var(--radius-lg); padding:48px 36px; margin-bottom:36px; box-shadow:var(--shadow-lg); display:grid; grid-template-columns:1.3fr 0.9fr; gap:32px; align-items:center;">' +
      '<div>' +
        '<div style="display:inline-flex; align-items:center; gap:8px; background:rgba(230,126,34,0.25); border:1px solid rgba(230,126,34,0.5); padding:6px 14px; border-radius:30px; font-size:13px; font-weight:700; color:var(--accent-light); margin-bottom:16px;">' +
          '<i class="fa-solid fa-clock"></i> Hot out of the oven every morning at 7:00 AM' +
        '</div>' +
        '<h1 style="font-size:38px; line-height:1.2; margin-bottom:14px; color:#fff;">Handcrafted Artisanal Breads &amp; Celebration Cakes</h1>' +
        '<p style="font-size:16px; color:#E8DCCF; margin-bottom:24px; line-height:1.5;">Experience pure luxury bakery made with 100% French butter, natural sourdough cultures, and Belgian couverture chocolate.</p>' +
        '<div style="display:flex; gap:12px; flex-wrap:wrap;">' +
          '<button class="btn-primary" onclick="switchTab(\'catalog\')" style="padding:14px 28px; font-size:15px; font-weight:700;">' +
            '<i class="fa-solid fa-cookie-bite"></i> Order Fresh Menu</button>' +
          '<button class="btn-secondary" onclick="switchTab(\'cake\')" style="padding:14px 24px; font-size:15px; background:rgba(255,255,255,0.15); color:#fff; border-color:rgba(255,255,255,0.3);">' +
            '<i class="fa-solid fa-cake-candles" style="color:var(--accent);"></i> Custom Cake Studio</button>' +
          '<button class="btn-secondary" onclick="switchTab(\'stores\')" style="padding:14px 20px; font-size:15px; background:rgba(255,255,255,0.15); color:#fff; border-color:rgba(255,255,255,0.3);">' +
            '<i class="fa-solid fa-location-dot" style="color:#2ECC71;"></i> Nearest Branch</button>' +
        '</div>' +
      '</div>' +
      '<div style="text-align:center;">' +
        '<div class="tilt-card" data-tilt style="padding:28px; background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.2); backdrop-filter:blur(12px); border-radius:24px;">' +
          '<i class="fa-solid fa-crown" style="font-size:56px; color:var(--accent); margin-bottom:12px;"></i>' +
          '<h3 style="color:#fff; font-size:22px; margin-bottom:6px;">Royal Celebration Cakes</h3>' +
          '<p style="color:rgba(255,255,255,0.8); font-size:14px; margin-bottom:18px;">Multi-tier wedding cakes, customized theme birthdays &amp; photo cupcakes delivered in refrigerated vans.</p>' +
          '<button class="btn-primary" onclick="switchTab(\'cake\')" style="width:100%; justify-content:center; padding:12px;">' +
            '<i class="fa-solid fa-wand-magic-sparkles"></i> Design Your Cake Now</button>' +
        '</div>' +
      '</div>' +
    '</div>' +

    '<!-- 4 USP Cards Grid -->' +
    '<div class="usp-grid">' +
      '<div class="usp-card">' +
        '<div class="usp-icon"><i class="fa-solid fa-cheese"></i></div>' +
        '<div class="usp-title">100% Pure Butter</div>' +
        '<div class="usp-desc">Never any hydrogenated fats or margarine. Only pure European dairy butter.</div>' +
      '</div>' +
      '<div class="usp-card">' +
        '<div class="usp-icon"><i class="fa-solid fa-fire-burner"></i></div>' +
        '<div class="usp-title">Baked Fresh Daily</div>' +
        '<div class="usp-desc">Small-batch baking around the clock ensures peak aroma, warmth, and fluffiness.</div>' +
      '</div>' +
      '<div class="usp-card">' +
        '<div class="usp-icon"><i class="fa-solid fa-shield-virus"></i></div>' +
        '<div class="usp-title">Zero Preservatives</div>' +
        '<div class="usp-desc">Naturally fermented sourdoughs with 24-hour cold proofing for easy digestion.</div>' +
      '</div>' +
      '<div class="usp-card">' +
        '<div class="usp-icon"><i class="fa-solid fa-truck-snowflake"></i></div>' +
        '<div class="usp-title">Cool-Chain Delivery</div>' +
        '<div class="usp-desc">Specialized shock-proof suspension delivery vans keep your delicate cakes flawless.</div>' +
      '</div>' +
    '</div>' +

    '<!-- Daily Bake Timings Schedule Bar -->' +
    '<div class="schedule-container">' +
      '<div class="schedule-header">' +
        '<div>' +
          '<h3 style="font-size:18px; color:var(--text-main);"><i class="fa-solid fa-stopwatch" style="color:var(--accent);"></i> Daily Fresh Oven Schedule</h3>' +
          '<p style="font-size:13px; color:var(--text-muted);">Catch your favourite warm bakery items straight as they exit the stone-deck oven</p>' +
        '</div>' +
        '<span class="store-open-badge"><i class="fa-solid fa-circle-dot"></i> Live Kitchen Active</span>' +
      '</div>' +
      '<div class="schedule-grid">' +
        '<div class="schedule-card">' +
          '<div class="schedule-icon"><i class="fa-solid fa-bread-slice"></i></div>' +
          '<div><div class="schedule-time">07:00 AM &amp; 04:00 PM</div><div class="schedule-item-name">Artisan Sourdough &amp; Brioche</div><div class="schedule-item-desc">Crusty exterior, soft aerated crumb</div></div>' +
        '</div>' +
        '<div class="schedule-card">' +
          '<div class="schedule-icon"><i class="fa-solid fa-cookie"></i></div>' +
          '<div><div class="schedule-time">09:00 AM &amp; 05:00 PM</div><div class="schedule-item-name">French Butter Croissants</div><div class="schedule-item-desc">72 flaky layers of honeycomb goodness</div></div>' +
        '</div>' +
        '<div class="schedule-card">' +
          '<div class="schedule-icon"><i class="fa-solid fa-pizza-slice"></i></div>' +
          '<div><div class="schedule-time">12:30 PM (Lunch Hot)</div><div class="schedule-item-name">Puff Pastries &amp; Savoury Pies</div><div class="schedule-item-desc">Chicken quiches, beef rolls &amp; patties</div></div>' +
        '</div>' +
        '<div class="schedule-card">' +
          '<div class="schedule-icon"><i class="fa-solid fa-cake-candles"></i></div>' +
          '<div><div class="schedule-time">02:00 PM onwards</div><div class="schedule-item-name">Fresh Pastries &amp; Gateaux</div><div class="schedule-item-desc">Belgian fudge, Lotus &amp; red velvet</div></div>' +
        '</div>' +
      '</div>' +
    '</div>' +

    '<!-- Featured Products Section -->' +
    '<div style="margin-bottom:24px; display:flex; justify-content:space-between; align-items:center;">' +
      '<div>' +
        '<h2 style="font-size:24px; color:var(--text-main);">Today\'s Masterpieces</h2>' +
        '<p style="color:var(--text-muted); font-size:14px;">Hand-selected items from today’s fresh batch</p>' +
      '</div>' +
      '<a href="#" onclick="switchTab(\'catalog\')" style="color:var(--primary); font-weight:700; text-decoration:none; font-size:15px;">Explore All Items (' + state.products.length + ') &rarr;</a>' +
    '</div>' +
    (toShow.length
      ? '<div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:24px; margin-bottom:40px;">' + toShow.map(productCard).join('') + '</div>'
      : '<div class="empty-state"><i class="fa-solid fa-bread-slice"></i><p>No products yet — add some from the Admin Dashboard.</p></div>') +

    '<!-- Custom Cake Studio CTA Strip -->' +
    '<div class="section-card" style="background:linear-gradient(135deg, #FAF5EF, #F3E5D8); border-color:var(--accent); display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:20px; margin-bottom:40px; padding:32px;">' +
      '<div style="max-width:560px;">' +
        '<span class="status-badge status-PREPARING" style="margin-bottom:10px;"><i class="fa-solid fa-wand-magic-sparkles"></i> Cake Customizer</span>' +
        '<h3 style="font-size:24px; margin-bottom:8px; color:var(--text-main);">Have a Specific Cake Design in Mind?</h3>' +
        '<p style="color:var(--text-muted); font-size:14px; line-height:1.5;">Select flavours, tiers, fondant themes, and write custom inscriptions. Our head pastry chef will provide an instant quote and prepare your masterpiece.</p>' +
      '</div>' +
      '<button class="btn-primary" onclick="switchTab(\'cake\')" style="padding:14px 28px; font-size:15px; font-weight:700;">' +
        '<i class="fa-solid fa-palette"></i> Open Cake Studio</button>' +
    '</div>' +

    '<!-- Testimonials Highlight -->' +
    '<div style="margin-bottom:40px;">' +
      '<div style="text-align:center; margin-bottom:24px;">' +
        '<h2 style="font-size:24px; color:var(--text-main);">Loved By Over 25,000 Foodies</h2>' +
        '<p style="color:var(--text-muted); font-size:14px;">Real reviews from our satisfied sweet &amp; savoury lovers across Pakistan</p>' +
      '</div>' +
      '<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:20px;">' +
        '<div class="section-card" style="margin-bottom:0;">' +
          '<div style="color:var(--accent); margin-bottom:8px;">★★★★★</div>' +
          '<p style="font-style:italic; font-size:14px; margin-bottom:12px; line-height:1.5;">"The Belgian Chocolate Fudge Cake was the star of my daughter\'s birthday! Warm, rich, and not overly sweet. Delivered right on time."</p>' +
          '<div style="font-weight:700; font-size:13px; color:var(--primary);">&mdash; Sara Ahmed (Lahore)</div>' +
        '</div>' +
        '<div class="section-card" style="margin-bottom:0;">' +
          '<div style="color:var(--accent); margin-bottom:8px;">★★★★★</div>' +
          '<p style="font-style:italic; font-size:14px; margin-bottom:12px; line-height:1.5;">"Best sourdough bread in the city hands down. Crunchy blistered crust and the aroma filled our entire kitchen. Ordering weekly now!"</p>' +
          '<div style="font-weight:700; font-size:13px; color:var(--primary);">&mdash; Bilal Qureshi (DHA Lahore)</div>' +
        '</div>' +
        '<div class="section-card" style="margin-bottom:0;">' +
          '<div style="color:var(--accent); margin-bottom:8px;">★★★★★</div>' +
          '<p style="font-style:italic; font-size:14px; margin-bottom:12px; line-height:1.5;">"Their custom cake quotation system was super fast. The finished wedding cake was exact replica of my Pinterest reference picture."</p>' +
          '<div style="font-weight:700; font-size:13px; color:var(--primary);">&mdash; Fatima Tariq (Islamabad)</div>' +
        '</div>' +
      '</div>' +
    '</div>';
}

// ------------------------------------------------------- customer: catalog view
let activeCategoryFilter = '';
let activeDietaryFilter = '';

function renderCatalogView() {
  const categoryList = [
    { id: '', name: 'All Specialties', icon: 'fa-table-cells-large' },
    { id: 'Cakes', name: 'Celebration Cakes', icon: 'fa-cake-candles' },
    { id: 'Breads', name: 'Artisan Sourdough & Breads', icon: 'fa-bread-slice' },
    { id: 'Pastries', name: 'Croissants & Viennoiserie', icon: 'fa-cookie' },
    { id: 'Savory', name: 'Savouries & Hot Snacks', icon: 'fa-pizza-slice' },
    { id: 'Cookies', name: 'Biscuits & Tea Cakes', icon: 'fa-cookie-bite' }
  ];

  const pillsHtml = categoryList.map(c => {
    const isActive = (activeCategoryFilter === c.id || (!activeCategoryFilter && !c.id));
    return '<button class="category-pill ' + (isActive ? 'active' : '') + '" onclick="filterCatalogByCategory(\'' + c.id + '\')">' +
      '<i class="fa-solid ' + c.icon + '"></i> ' + escapeHtml(c.name) + '</button>';
  }).join('');

  const grid = state.products.length ? state.products.map(productCard).join('')
    : '<div class="empty-state" style="grid-column:1/-1;"><i class="fa-solid fa-magnifying-glass"></i><p>No bakery items found.</p></div>';

  return '' +
    '<div style="margin-bottom:24px;">' +
      '<h2 style="font-size:26px; color:var(--text-main); margin-bottom:4px;">Freshly Baked Daily Menu</h2>' +
      '<p style="color:var(--text-muted); font-size:14px;">Select from our full range of handcrafted breads, gourmet gateaux, and savoury puffs.</p>' +
    '</div>' +

    '<div class="category-pills">' + pillsHtml + '</div>' +

    '<div style="background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-md); padding:16px 20px; margin-bottom:24px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:16px;">' +
      '<div style="display:flex; gap:12px; align-items:center; flex-wrap:wrap; flex:1;">' +
        '<div style="position:relative; min-width:280px; flex:1;">' +
          '<i class="fa-solid fa-magnifying-glass" style="position:absolute; left:14px; top:13px; color:var(--text-muted);"></i>' +
          '<input type="text" id="catalog-search" class="form-control" placeholder="Search cakes, sourdough, croissants, patties..." onkeyup="filterCatalog()" style="padding-left:38px;">' +
        '</div>' +
        '<div style="display:flex; gap:10px; align-items:center;">' +
          '<label style="font-size:13px; font-weight:600; display:flex; align-items:center; gap:6px; cursor:pointer;"><input type="checkbox" id="filter-eggless" onchange="filterCatalog()"> Eggless</label>' +
          '<label style="font-size:13px; font-weight:600; display:flex; align-items:center; gap:6px; cursor:pointer;"><input type="checkbox" id="filter-sugarfree" onchange="filterCatalog()"> Sugar-Free</label>' +
        '</div>' +
      '</div>' +
      '<div style="display:flex; gap:8px; align-items:center;">' +
        '<span style="font-size:13px; color:var(--text-muted); white-space:nowrap;">Sort by:</span>' +
        '<select id="catalog-sort" class="form-select" style="width:160px;" onchange="filterCatalog()">' +
          '<option value="default">Featured</option>' +
          '<option value="price-low">Price: Low to High</option>' +
          '<option value="price-high">Price: High to Low</option>' +
          '<option value="rating">Highest Rated</option>' +
        '</select>' +
      '</div>' +
    '</div>' +

    '<div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:24px;" id="catalog-grid">' + grid + '</div>';
}

function filterCatalogByCategory(catId) {
  activeCategoryFilter = catId;
  document.querySelectorAll('.category-pills .category-pill').forEach(b => b.classList.remove('active'));
  event.currentTarget.classList.add('active');
  filterCatalog();
}

function filterCategoryByName(catName) {
  activeCategoryFilter = catName;
  renderApp();
}

function filterCatalog() {
  const term = (document.getElementById('catalog-search') ? document.getElementById('catalog-search').value : '').toLowerCase().trim();
  const sortMode = document.getElementById('catalog-sort') ? document.getElementById('catalog-sort').value : 'default';
  const isEggless = document.getElementById('filter-eggless') ? document.getElementById('filter-eggless').checked : false;
  const isSugarFree = document.getElementById('filter-sugarfree') ? document.getElementById('filter-sugarfree').checked : false;
  const grid = document.getElementById('catalog-grid');
  if (!grid) return;

  let filtered = state.products.filter(p => {
    const text = (p.name + ' ' + (p.description || '')).toLowerCase();
    const matchesTerm = !term || text.indexOf(term) !== -1;
    const matchesCat = !activeCategoryFilter || text.indexOf(activeCategoryFilter.toLowerCase()) !== -1;
    const matchesEggless = !isEggless || text.indexOf('eggless') !== -1 || text.indexOf('bread') !== -1;
    const matchesSugarFree = !isSugarFree || text.indexOf('sugar-free') !== -1 || text.indexOf('sourdough') !== -1;
    return matchesTerm && matchesCat && matchesEggless && matchesSugarFree;
  });

  if (sortMode === 'price-low') {
    filtered.sort((a, b) => (a.sale_price || a.price) - (b.sale_price || b.price));
  } else if (sortMode === 'price-high') {
    filtered.sort((a, b) => (b.sale_price || b.price) - (a.sale_price || a.price));
  } else if (sortMode === 'rating') {
    filtered.sort((a, b) => (b.average_rating || 5) - (a.average_rating || 5));
  }

  grid.innerHTML = filtered.length ? filtered.map(productCard).join('')
    : '<div class="empty-state" style="grid-column:1/-1;"><i class="fa-solid fa-magnifying-glass"></i><p>No products match your criteria.</p></div>';
  attach3DTiltListeners();
}

// ---------------------------------------------------------------- cart & checkout
function addToCart(productId) {
  const prod = state.products.find(p => p.id === productId);
  if (!prod) return;
  const existing = state.cart.find(i => i.product_id === productId && !i.custom_note);
  if (existing) existing.quantity += 1;
  else state.cart.push({ product_id: productId, name: prod.name, price: (prod.sale_price != null ? prod.sale_price : prod.price), quantity: 1 });
  updateCartBadge();
  showToast(prod.name + ' added to cart!', 'success');
}

function updateCartBadge() {
  const count = state.cart.reduce((sum, item) => sum + item.quantity, 0);
  const el = document.getElementById('cart-count');
  if (el) el.innerText = count;
}

function toggleCartModal() {
  const modal = document.getElementById('cart-modal');
  const willOpen = !modal.classList.contains('active');
  if (willOpen) renderCartModal();
  modal.classList.toggle('active');
}

function cartChangeQty(productId, delta) {
  const item = state.cart.find(i => i.product_id === productId);
  if (!item) return;
  item.quantity = Math.max(1, item.quantity + delta);
  updateCartBadge();
  renderCartModal();
}

function cartRemove(productId) {
  state.cart = state.cart.filter(i => i.product_id !== productId);
  updateCartBadge();
  renderCartModal();
}

let appliedCouponDiscount = 0;
let appliedCouponCode = '';

function applyPromoCode() {
  const code = (document.getElementById('coupon-input').value || '').trim().toUpperCase();
  if (code === 'WELCOME10' || code === 'FRESH10') {
    appliedCouponDiscount = 0.10;
    appliedCouponCode = code;
    showToast('Promo code ' + code + ' applied! 10% discount added.', 'success');
    renderCartModal();
  } else if (code === 'FRESHCO20') {
    appliedCouponDiscount = 0.20;
    appliedCouponCode = code;
    showToast('VIP Promo code applied! 20% discount added.', 'success');
    renderCartModal();
  } else {
    showToast('Invalid promo code. Try WELCOME10 or FRESH10', 'error');
  }
}

function renderCartModal() {
  const body = document.getElementById('cart-modal-body');
  const subtotal = state.cart.reduce((sum, i) => sum + i.price * i.quantity, 0);
  const discountAmount = Math.round(subtotal * appliedCouponDiscount);
  const deliveryFee = (subtotal > 1500 || subtotal === 0) ? 0 : 150;
  const total = Math.max(0, subtotal - discountAmount + deliveryFee);

  if (!state.cart.length) {
    body.innerHTML = '<div class="empty-state"><i class="fa-solid fa-basket-shopping"></i><p>Your shopping basket is empty.</p>' +
      '<button class="btn-primary" onclick="toggleCartModal(); switchTab(\'catalog\');" style="margin-top:12px;">Browse Fresh Menu</button></div>';
    return;
  }

  const rows = state.cart.map(i => '' +
    '<div class="cart-item-row">' +
      '<div style="flex:1;">' +
        '<div style="font-weight:700; font-size:14px;">' + escapeHtml(i.name) + '</div>' +
        (i.custom_note ? '<div style="font-size:12px; color:var(--accent);">Note: "' + escapeHtml(i.custom_note) + '"</div>' : '') +
        '<div style="font-size:13px; color:var(--text-muted);">' + money(i.price) + ' each</div>' +
      '</div>' +
      '<div class="qty-stepper"><button onclick="cartChangeQty(' + i.product_id + ', -1)">-</button><span>' + i.quantity + '</span><button onclick="cartChangeQty(' + i.product_id + ', 1)">+</button></div>' +
      '<button class="icon-link-btn" onclick="cartRemove(' + i.product_id + ')"><i class="fa-solid fa-trash"></i></button>' +
    '</div>').join('');

  const defaultPhone = (state.user && state.user.phone) ? state.user.phone : '03348984654';
  const defaultName = (state.user && state.user.name) ? state.user.name : '';

  body.innerHTML = rows +
    '<!-- Coupon Code Box -->' +
    '<div style="margin:14px 0 10px; display:flex; gap:8px;">' +
      '<input type="text" id="coupon-input" class="form-control" placeholder="Promo Code (e.g. WELCOME10)" value="' + escapeHtml(appliedCouponCode) + '" style="text-transform:uppercase; font-size:13px;">' +
      '<button type="button" class="btn-secondary" onclick="applyPromoCode()" style="padding:8px 16px; font-weight:700;">Apply</button>' +
    '</div>' +

    '<!-- Price Summary -->' +
    '<div style="background:var(--bg-light); padding:12px; border-radius:10px; border:1px solid var(--border); margin-bottom:16px; font-size:13px;">' +
      '<div style="display:flex; justify-content:space-between; margin-bottom:4px;"><span>Subtotal:</span><strong>' + money(subtotal) + '</strong></div>' +
      (discountAmount > 0 ? '<div style="display:flex; justify-content:space-between; margin-bottom:4px; color:var(--success);"><span>Discount (' + (appliedCouponDiscount * 100) + '%):</span><strong>-' + money(discountAmount) + '</strong></div>' : '') +
      '<div style="display:flex; justify-content:space-between; margin-bottom:4px;"><span>Delivery Fee:</span><span>' + (deliveryFee === 0 ? '<span style="color:var(--success); font-weight:700;">FREE (Orders > Rs 1,500)</span>' : money(deliveryFee)) + '</span></div>' +
      '<div style="display:flex; justify-content:space-between; border-top:1px solid var(--border); padding-top:6px; font-size:16px; font-weight:800; color:var(--primary);"><span>Total Amount:</span><span>' + money(total) + '</span></div>' +
    '</div>' +

    '<!-- Checkout Form -->' +
    '<div style="background:var(--card-bg, #fff); border:1px solid var(--border); border-radius:12px; padding:16px; margin-bottom:16px;">' +
      '<div style="font-weight:700; font-size:14px; margin-bottom:12px; color:var(--text-main);"><i class="fa-solid fa-truck" style="color:var(--accent); margin-right:6px;"></i> Delivery &amp; Contact Details</div>' +
      
      '<div class="form-group" style="margin-bottom:10px;"><label class="form-label" style="font-size:12px;">Customer Full Name</label>' +
        '<input type="text" id="checkout-name" class="form-control" placeholder="e.g. Sara Ali" value="' + escapeHtml(defaultName) + '"></div>' +
      
      '<div class="form-group" style="margin-bottom:10px;"><label class="form-label" style="font-size:12px;">WhatsApp Mobile Number <span style="color:var(--primary); font-size:11px;">(For Live Updates)</span></label>' +
        '<input type="tel" id="checkout-phone" class="form-control" placeholder="e.g. 03348984654" value="' + escapeHtml(defaultPhone) + '" required></div>' +
      
      '<div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:10px;">' +
        '<div class="form-group" style="margin-bottom:0;"><label class="form-label" style="font-size:12px;">Fulfillment Type</label>' +
          '<select id="checkout-order-type" class="form-select">' +
            '<option value="DELIVERY">Home Delivery</option>' +
            '<option value="PICKUP">Pickup from Counter</option>' +
          '</select></div>' +
        '<div class="form-group" style="margin-bottom:0;"><label class="form-label" style="font-size:12px;">Preferred Time Slot</label>' +
          '<select id="checkout-slot" class="form-select">' +
            '<option value="Express">Express (45-60 min)</option>' +
            '<option value="Morning">Morning (09:00 - 12:00)</option>' +
            '<option value="Afternoon">Afternoon (01:00 - 05:00)</option>' +
            '<option value="Evening">Evening (06:00 - 09:00)</option>' +
          '</select></div>' +
      '</div>' +

      '<div class="form-group" id="checkout-branch-group" style="display:none; margin-bottom:10px;"><label class="form-label" style="font-size:12px;">Pickup Branch</label>' +
        '<select id="checkout-branch" class="form-select">' +
          '<option value="Gulberg">Gulberg III Flagship (MM Alam Rd)</option>' +
          '<option value="DHA">DHA Phase 5 (Commercial)</option>' +
          '<option value="Islamabad">Islamabad (Blue Area)</option>' +
        '</select></div>' +

      '<div class="form-group" id="checkout-address-group" style="margin-bottom:10px;"><label class="form-label" style="font-size:12px;">Delivery Address</label>' +
        '<input type="text" id="checkout-address" class="form-control" placeholder="House #, Street, Block, Area, City"></div>' +

      '<div class="form-group" style="margin-bottom:10px;"><label class="form-label" style="font-size:12px;">Payment Method</label>' +
        '<select id="checkout-payment-method" class="form-select">' +
          '<option value="COD">Cash on Delivery (COD)</option>' +
          '<option value="CARD">Debit / Credit Card (POS on Delivery)</option>' +
          '<option value="ONLINE">JazzCash / EasyPaisa Online Transfer</option>' +
        '</select></div>' +

      '<div class="form-group" style="margin-bottom:0;"><label class="form-label" style="font-size:12px;">Special Delivery / Cake Instructions</label>' +
        '<input type="text" id="checkout-notes" class="form-control" placeholder="e.g. Ring bell twice, handle delicate cake with care"></div>' +
    '</div>' +

    '<button class="btn-primary" style="width:100%; justify-content:center; padding:14px; font-weight:800; font-size:16px;" onclick="handleCheckout()"><i class="fa-solid fa-circle-check"></i> Place Order Now (' + money(total) + ')</button>';

  document.getElementById('checkout-order-type').onchange = function (e) {
    const isDelivery = e.target.value === 'DELIVERY';
    document.getElementById('checkout-address-group').style.display = isDelivery ? 'block' : 'none';
    document.getElementById('checkout-branch-group').style.display = isDelivery ? 'none' : 'block';
  };
}

async function handleCheckout() {
  if (!state.cart.length) return;
  if (!requireLogin('Please sign in to place an order.')) return;

  const orderType = document.getElementById('checkout-order-type').value;
  const customerName = document.getElementById('checkout-name').value.trim();
  const customerPhone = document.getElementById('checkout-phone').value.trim();
  const slot = document.getElementById('checkout-slot').value;
  const notes = (document.getElementById('checkout-notes') ? document.getElementById('checkout-notes').value.trim() : '') + (slot ? ' [Time Slot: ' + slot + ']' : '');
  let addressId = null;

  if (!customerPhone) {
    showToast('Please enter your WhatsApp mobile number for order confirmation.', 'error');
    document.getElementById('checkout-phone').focus();
    return;
  }

  try {
    if (orderType === 'DELIVERY') {
      const line1 = document.getElementById('checkout-address').value.trim();
      if (!line1) { showToast('Please enter a delivery address.', 'error'); return; }
      const address = await apiFetch('/addresses', { method: 'POST', body: { line1: line1 } });
      addressId = address.id;
    }

    await apiFetch('/cart/items', { method: 'DELETE' }).catch(() => {});
    for (const item of state.cart) {
      await apiFetch('/cart/items', { method: 'POST', body: { product_id: item.product_id, quantity: item.quantity } });
    }
    const order = await apiFetch('/orders', {
      method: 'POST',
      body: {
        order_type: orderType,
        address_id: addressId,
        customer_name: customerName,
        customer_phone: customerPhone,
        notes: notes
      }
    });

    state.cart = [];
    appliedCouponDiscount = 0;
    appliedCouponCode = '';
    updateCartBadge();
    document.getElementById('cart-modal').classList.remove('active');
    showToast('Order #' + order.order_number + ' confirmed! WhatsApp notification sent to ' + customerPhone, 'success');
    switchTab('orders');
  } catch (e) {
    showToast(e.message, 'error');
  }
}

// --------------------------------------------------------- custom cakes studio
let customCakeEstimatedPrice = 2800;

function updateCakeEstimate() {
  const flavour = document.getElementById('cake-flavour') ? document.getElementById('cake-flavour').value : 'Belgian Chocolate Fudge';
  const size = document.getElementById('cake-size') ? document.getElementById('cake-size').value : '2 lb';
  let base = 2500;
  if (flavour.includes('Lotus') || flavour.includes('Biscoff')) base += 500;
  if (flavour.includes('Belgian') || flavour.includes('Truffle')) base += 400;
  if (flavour.includes('Red Velvet')) base += 300;

  if (size.includes('5 lb') || size.includes('2-Tier')) base *= 2.2;
  else if (size.includes('8 lb') || size.includes('3-Tier')) base *= 3.5;
  else if (size.includes('3 lb')) base *= 1.4;

  customCakeEstimatedPrice = Math.round(base);
  const el = document.getElementById('cake-estimate-badge');
  if (el) el.innerText = money(customCakeEstimatedPrice);
}

function selectFlavourQuick(flavourName) {
  const el = document.getElementById('cake-flavour');
  if (el) el.value = flavourName;
  updateCakeEstimate();
  showToast('Selected flavour: ' + flavourName, 'info');
}

function selectTierQuick(tierText) {
  const el = document.getElementById('cake-size');
  if (el) el.value = tierText;
  updateCakeEstimate();
  showToast('Selected tier: ' + tierText, 'info');
}

function renderCustomCakeTab(container) {
  container.innerHTML = '' +
    '<div style="text-align:center; max-width:700px; margin:0 auto 30px;">' +
      '<span class="status-badge status-PREPARING" style="margin-bottom:8px;"><i class="fa-solid fa-wand-magic-sparkles"></i> Master Pastry Studio</span>' +
      '<h2 style="font-size:30px; margin-bottom:8px; color:var(--text-main);">Custom Celebration Cake Architect</h2>' +
      '<p style="color:var(--text-muted); font-size:15px; line-height:1.5;">Design your personalized cake for weddings, birthdays &amp; corporate events. Get an instant estimate and quotation from our head chef.</p>' +
    '</div>' +

    '<div style="display:grid; grid-template-columns:1.4fr 1fr; gap:28px; max-width:1100px; margin:0 auto 36px;">' +
      '<!-- Cake Form Card -->' +
      '<div class="section-card">' +
        '<form onsubmit="handleCustomCakeSubmit(event)">' +
          '<h3 style="font-size:18px; margin-bottom:16px; color:var(--text-main);"><i class="fa-solid fa-cake-candles" style="color:var(--accent);"></i> Step 1: Flavour &amp; Sponge</h3>' +
          '<div class="form-group">' +
            '<label class="form-label">Signature Gourmet Flavour</label>' +
            '<select id="cake-flavour" class="form-select" onchange="updateCakeEstimate()" required>' +
              '<option value="Belgian Chocolate Fudge">Belgian Chocolate Fudge (Rich &amp; Decadent)</option>' +
              '<option value="Lotus Biscoff Cream">Lotus Biscoff Cream &amp; Caramel</option>' +
              '<option value="Classic Red Velvet">Classic Red Velvet with Philadelphia Cream Cheese</option>' +
              '<option value="Madagascar Vanilla Berry">Madagascar Vanilla &amp; Fresh Wild Berries</option>' +
              '<option value="Nutella Ferrero Rocher">Nutella Ferrero Rocher Hazelnut</option>' +
              '<option value="Salted Caramel Crunch">Salted Caramel Crunch &amp; Almond Praline</option>' +
            '</select>' +
          '</div>' +

          '<h3 style="font-size:18px; margin:20px 0 14px; color:var(--text-main);"><i class="fa-solid fa-layer-group" style="color:var(--accent);"></i> Step 2: Size, Weight &amp; Tiers</h3>' +
          '<div class="form-group">' +
            '<label class="form-label">Size / Servings</label>' +
            '<select id="cake-size" class="form-select" onchange="updateCakeEstimate()" required>' +
              '<option value="2 lb (serves 8-10)">1-Tier &middot; 2 Lbs (Serves 8-10 guests)</option>' +
              '<option value="3 lb (serves 12-15)">1-Tier &middot; 3 Lbs (Serves 12-15 guests)</option>' +
              '<option value="5 lb 2-Tier (serves 20-25)">2-Tier &middot; 5 Lbs Grand (Serves 20-25 guests)</option>' +
              '<option value="8 lb 3-Tier (serves 35-45)">3-Tier &middot; 8 Lbs Royal Wedding (Serves 35-45 guests)</option>' +
            '</select>' +
          '</div>' +

          '<h3 style="font-size:18px; margin:20px 0 14px; color:var(--text-main);"><i class="fa-solid fa-brush" style="color:var(--accent);"></i> Step 3: Design, Message &amp; Date</h3>' +
          '<div style="display:grid; grid-template-columns:1fr 1fr; gap:14px;">' +
            '<div class="form-group"><label class="form-label">Occasion / Event</label><input id="cake-type" class="form-control" placeholder="e.g. 25th Birthday, Wedding"></div>' +
            '<div class="form-group"><label class="form-label">Frosting / Finish</label><select id="cake-cream" class="form-select"><option value="Whipped Buttercream">Whipped Swiss Buttercream</option><option value="Dark Ganache">Belgian Dark Chocolate Ganache</option><option value="Fondant Art">Thematic Hand-sculpted Fondant</option><option value="Naked Rustic">Semi-Naked Rustic with Flowers</option></select></div>' +
          '</div>' +

          '<div class="form-group"><label class="form-label">Message Written on Cake</label><input id="cake-message" class="form-control" placeholder="e.g. Happy 30th Birthday Ali!"></div>' +
          '<div class="form-group"><label class="form-label">Theme / Special Reference Notes</label><input id="cake-theme" class="form-control" placeholder="e.g. Gold foil accents, pastel pink roses, football theme"></div>' +
          '<div class="form-group"><label class="form-label">Required Event Date</label><input id="cake-date" type="date" class="form-control" required></div>' +

          '<button type="submit" class="btn-primary" style="width:100%; justify-content:center; padding:15px; font-size:16px; font-weight:700;"><i class="fa-solid fa-paper-plane"></i> Submit Request for Chef Quote</button>' +
        '</form>' +
      '</div>' +

      '<!-- Estimation & Inspiration Sidebar -->' +
      '<div>' +
        '<div class="section-card" style="background:linear-gradient(135deg, #FAF5EF, #FFF); border-color:var(--accent); position:sticky; top:100px;">' +
          '<h3 style="font-size:18px; margin-bottom:12px; color:var(--text-main);"><i class="fa-solid fa-calculator" style="color:var(--accent);"></i> Estimated Price Preview</h3>' +
          '<div style="font-size:32px; font-weight:800; color:var(--primary); margin-bottom:8px;" id="cake-estimate-badge">₨ 2,800</div>' +
          '<p style="font-size:13px; color:var(--text-muted); margin-bottom:16px;">*Final quotation confirmed by pastry chef within 20 minutes based on intricate handcrafting complexity.</p>' +
          
          '<div style="border-top:1px solid var(--border); padding-top:16px; margin-top:16px;">' +
            '<div style="font-weight:700; font-size:14px; margin-bottom:10px;">Why Order From Freshco Studio?</div>' +
            '<div style="font-size:13px; color:var(--text-muted); line-height:1.6;">' +
              '<div><i class="fa-solid fa-check" style="color:var(--success); margin-right:6px;"></i> Edible gold leaf &amp; organic florals</div>' +
              '<div><i class="fa-solid fa-check" style="color:var(--success); margin-right:6px;"></i> Free mock digital sketch preview</div>' +
              '<div><i class="fa-solid fa-check" style="color:var(--success); margin-right:6px;"></i> Temperature-controlled cake handling van</div>' +
              '<div><i class="fa-solid fa-check" style="color:var(--success); margin-right:6px;"></i> Complimentary premium cake knife set</div>' +
            '</div>' +
          '</div>' +
        '</div>' +
      '</div>' +
    '</div>' +

    '<div id="my-cake-requests"></div>';

  document.getElementById('cake-date').min = new Date(Date.now() + 86400000).toISOString().split('T')[0];
  loadMyCakeRequests();
}

async function loadMyCakeRequests() {
  const el = document.getElementById('my-cake-requests');
  if (!isLoggedIn()) { el.innerHTML = '<p style="text-align:center; color:var(--text-muted);">Sign in to view status of your custom cake inquiries.</p>'; return; }
  try {
    const page = await apiFetch('/custom-cakes');
    if (!page.items.length) { el.innerHTML = ''; return; }
    el.innerHTML = '<h3 style="margin-bottom:16px; font-size:20px;">Your Custom Cake Orders &amp; Quotes</h3>' + page.items.map(r => '' +
      '<div class="section-card" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">' +
        '<div>' +
          '<div style="font-size:16px; font-weight:800; color:var(--primary);">' + escapeHtml(r.flavour) + ' &middot; ' + escapeHtml(r.size) + '</div>' +
          '<div style="font-size:13px; color:var(--text-muted); margin-top:2px;">Needed by ' + r.requested_date + (r.quote_amount ? ' &middot; <strong>Quoted Amount: ' + money(r.quote_amount) + '</strong>' : ' &middot; <em>Quote in review by Chef</em>') + '</div>' +
          (r.message ? '<div style="font-size:12px; color:var(--accent);">Inscription: "' + escapeHtml(r.message) + '"</div>' : '') +
        '</div>' +
        '<div style="display:flex; align-items:center; gap:10px;">' +
          '<span class="status-badge status-' + r.status + '">' + r.status.replace('_', ' ') + '</span>' +
          (r.status === 'quoted' ? '<button class="btn-primary btn-sm" onclick="acceptCakeQuote(' + r.id + ')"><i class="fa-solid fa-check"></i> Accept Quote</button>' : '') +
          (['pending', 'quoted', 'accepted'].indexOf(r.status) !== -1 ? '<button class="btn-danger-sm" onclick="cancelCakeRequest(' + r.id + ')">Cancel</button>' : '') +
        '</div>' +
      '</div>').join('');
  } catch (e) {
    el.innerHTML = '<p style="color:var(--danger);">' + e.message + '</p>';
  }
}

async function handleCustomCakeSubmit(event) {
  event.preventDefault();
  if (!requireLogin('Please sign in to submit a custom cake request.')) return;
  const payload = {
    flavour: document.getElementById('cake-flavour').value.trim(),
    size: document.getElementById('cake-size').value.trim(),
    type: document.getElementById('cake-type').value.trim() || null,
    cream: document.getElementById('cake-cream').value.trim() || null,
    theme: document.getElementById('cake-theme').value.trim() || null,
    message: document.getElementById('cake-message').value.trim() || null,
    requested_date: document.getElementById('cake-date').value,
  };
  try {
    await apiFetch('/custom-cakes', { method: 'POST', body: payload });
    showToast('Custom cake request submitted! Head Chef will review and send you a quotation.', 'success');
    event.target.reset();
    loadMyCakeRequests();
  } catch (e) {
    showToast(e.message, 'error');
  }
}

async function acceptCakeQuote(id) {
  try { await apiFetch('/custom-cakes/' + id + '/accept', { method: 'PATCH' }); showToast('Cake quotation accepted! Sent to baking schedule.', 'success'); loadMyCakeRequests(); }
  catch (e) { showToast(e.message, 'error'); }
}
async function cancelCakeRequest(id) {
  if (!confirm('Cancel this custom cake request?')) return;
  try { await apiFetch('/custom-cakes/' + id + '/cancel', { method: 'PATCH' }); showToast('Request cancelled.', 'info'); loadMyCakeRequests(); }
  catch (e) { showToast(e.message, 'error'); }
}

// ------------------------------------------------------------ store locator
function renderStoresTab(container) {
  container.innerHTML = '' +
    '<div style="text-align:center; max-width:700px; margin:0 auto 30px;">' +
      '<span class="status-badge status-DELIVERED" style="margin-bottom:8px;"><i class="fa-solid fa-map-location-dot"></i> Store Directory</span>' +
      '<h2 style="font-size:30px; margin-bottom:8px; color:var(--text-main);">Visit Our Bakery &amp; Live Kitchens</h2>' +
      '<p style="color:var(--text-muted); font-size:15px;">Experience the aroma of live ovens, sip speciality roasted espresso, and pick up your favourite artisanal bakes.</p>' +
    '</div>' +

    '<div class="store-grid">' +
      '<div class="store-card">' +
        '<div class="store-card-header">' +
          '<div>' +
            '<h3 style="font-size:20px; margin-bottom:4px;">Gulberg III Flagship</h3>' +
            '<div style="font-size:13px; opacity:0.85;">MM Alam Road, Gulberg III, Lahore</div>' +
          '</div>' +
          '<span class="store-open-badge"><i class="fa-solid fa-circle"></i> Open Now</span>' +
        '</div>' +
        '<div class="store-body">' +
          '<div class="footer-info-item" style="color:var(--text-main); margin-bottom:10px;"><i class="fa-solid fa-clock"></i><div><strong>Daily Timings:</strong><br>08:00 AM &ndash; 12:00 Midnight</div></div>' +
          '<div class="footer-info-item" style="color:var(--text-main); margin-bottom:10px;"><i class="fa-solid fa-phone"></i><div><strong>Phone:</strong><br><a href="tel:04235889900" style="color:var(--primary); font-weight:700; text-decoration:none;">042-35889900</a> / <a href="https://wa.me/923348984654" target="_blank" style="color:#25D366; text-decoration:none;">WhatsApp</a></div></div>' +
          '<div class="store-feature-tags">' +
            '<span class="store-tag"><i class="fa-solid fa-mug-hot"></i> Specialty Cafe</span>' +
            '<span class="store-tag"><i class="fa-solid fa-fire"></i> Live Stone Oven</span>' +
            '<span class="store-tag"><i class="fa-solid fa-car"></i> Valet Parking</span>' +
          '</div>' +
        '</div>' +
      '</div>' +

      '<div class="store-card">' +
        '<div class="store-card-header">' +
          '<div>' +
            '<h3 style="font-size:20px; margin-bottom:4px;">DHA Phase 5 Outlet</h3>' +
            '<div style="font-size:13px; opacity:0.85;">Commercial Area, Phase 5 DHA, Lahore</div>' +
          '</div>' +
          '<span class="store-open-badge"><i class="fa-solid fa-circle"></i> Open Now</span>' +
        '</div>' +
        '<div class="store-body">' +
          '<div class="footer-info-item" style="color:var(--text-main); margin-bottom:10px;"><i class="fa-solid fa-clock"></i><div><strong>Daily Timings:</strong><br>08:00 AM &ndash; 01:00 AM (Late Night)</div></div>' +
          '<div class="footer-info-item" style="color:var(--text-main); margin-bottom:10px;"><i class="fa-solid fa-phone"></i><div><strong>Phone:</strong><br><a href="tel:04235741122" style="color:var(--primary); font-weight:700; text-decoration:none;">042-35741122</a></div></div>' +
          '<div class="store-feature-tags">' +
            '<span class="store-tag"><i class="fa-solid fa-cake-candles"></i> Custom Cake Studio</span>' +
            '<span class="store-tag"><i class="fa-solid fa-car-side"></i> Fast Drive-Thru Pickup</span>' +
          '</div>' +
        '</div>' +
      '</div>' +

      '<div class="store-card">' +
        '<div class="store-card-header">' +
          '<div>' +
            '<h3 style="font-size:20px; margin-bottom:4px;">Islamabad Blue Area</h3>' +
            '<div style="font-size:13px; opacity:0.85;">Jinnah Avenue, Blue Area, Islamabad</div>' +
          '</div>' +
          '<span class="store-open-badge"><i class="fa-solid fa-circle"></i> Open Now</span>' +
        '</div>' +
        '<div class="store-body">' +
          '<div class="footer-info-item" style="color:var(--text-main); margin-bottom:10px;"><i class="fa-solid fa-clock"></i><div><strong>Daily Timings:</strong><br>09:00 AM &ndash; 11:00 PM</div></div>' +
          '<div class="footer-info-item" style="color:var(--text-main); margin-bottom:10px;"><i class="fa-solid fa-phone"></i><div><strong>Phone:</strong><br><a href="tel:0512890011" style="color:var(--primary); font-weight:700; text-decoration:none;">051-2890011</a></div></div>' +
          '<div class="store-feature-tags">' +
            '<span class="store-tag"><i class="fa-solid fa-bread-slice"></i> Sourdough Specialty</span>' +
            '<span class="store-tag"><i class="fa-solid fa-truck-fast"></i> Citywide Delivery</span>' +
          '</div>' +
        '</div>' +
      '</div>' +
    '</div>';
}

// ------------------------------------------------------------ live order tracking
async function renderOrdersView(container) {
  container.innerHTML = '' +
    '<div style="margin-bottom:24px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:16px;">' +
      '<div>' +
        '<h2 style="font-size:26px; color:var(--text-main);">Live Order Tracking</h2>' +
        '<p style="color:var(--text-muted); font-size:14px;">Monitor your bakes in real-time from flour sifting to doorstep delivery</p>' +
      '</div>' +
      '<div style="display:flex; gap:8px;">' +
        '<input type="text" id="order-search-input" class="form-control" placeholder="Enter Order # (e.g. ORD-2026-001)" style="width:260px;">' +
        '<button class="btn-primary" onclick="lookupSpecificOrder()"><i class="fa-solid fa-magnifying-glass"></i> Track</button>' +
      '</div>' +
    '</div>' +
    '<div id="orders-list"><p style="color:var(--text-muted); padding:30px 0; text-align:center;">Loading your orders...</p></div>';

  if (!isLoggedIn()) {
    document.getElementById('orders-list').innerHTML = '' +
      '<div class="section-card" style="text-align:center; padding:40px 20px;">' +
        '<i class="fa-solid fa-truck-fast" style="font-size:48px; color:var(--accent); margin-bottom:16px;"></i>' +
        '<h3>Track Your Guest Order</h3>' +
        '<p style="color:var(--text-muted); max-width:480px; margin:8px auto 20px;">Enter your Order Number above to track real-time kitchen progress, or sign in to see your full order history.</p>' +
        '<button class="btn-primary" onclick="openAuthModal()"><i class="fa-regular fa-user"></i> Sign In to Account</button>' +
      '</div>';
    return;
  }

  loadCustomerOrders();
}

async function lookupSpecificOrder() {
  const query = (document.getElementById('order-search-input').value || '').trim();
  if (!query) { showToast('Please enter an order number.', 'error'); return; }
  try {
    const page = await apiFetch('/orders');
    const match = page.items.find(o => o.order_number.toLowerCase().includes(query.toLowerCase()));
    if (!match) {
      showToast('Order ' + query + ' not found in your account.', 'error');
      return;
    }
    renderSingleOrderCard(match);
  } catch (e) { showToast(e.message, 'error'); }
}

function renderSingleOrderCard(o) {
  const list = document.getElementById('orders-list');
  if (!list) return;
  list.innerHTML = renderOrderHtml(o);
}

function renderOrderHtml(o) {
  const steps = [
    { key: 'PENDING', title: 'Order Confirmed', desc: 'Received & Logged', icon: 'fa-clipboard-check' },
    { key: 'CONFIRMED', title: 'Prep & Sifting', desc: 'Ingredients Ready', icon: 'fa-wheat-awn' },
    { key: 'PREPARING', title: 'Baking in Oven', desc: 'Hot & Rising', icon: 'fa-fire-burner' },
    { key: 'READY', title: 'Quality Packed', desc: 'Gift Box Sealing', icon: 'fa-gift' },
    { key: 'DELIVERED', title: 'Delivered / Ready', desc: 'Enjoy Warm', icon: 'fa-truck-fast' }
  ];

  let currentIdx = 0;
  if (o.status === 'PENDING') currentIdx = 0;
  else if (o.status === 'CONFIRMED') currentIdx = 1;
  else if (o.status === 'PREPARING' || o.status === 'IN_PROGRESS') currentIdx = 2;
  else if (o.status === 'READY') currentIdx = 3;
  else if (o.status === 'DELIVERED' || o.status === 'PICKED_UP' || o.status === 'DONE') currentIdx = 4;
  else if (o.status === 'CANCELLED') currentIdx = -1;

  const cancellable = ['PENDING', 'CONFIRMED'].indexOf(o.status) !== -1;
  const itemsText = o.items.map(i => i.quantity + 'x ' + escapeHtml(i.product_name)).join(', ');

  const pipelineHtml = o.status !== 'CANCELLED'
    ? '<div class="pipeline-steps">' + steps.map((s, idx) => {
        const isCompleted = idx < currentIdx;
        const isActive = idx === currentIdx;
        const cls = isCompleted ? 'completed' : (isActive ? 'active' : '');
        return '<div class="pipeline-step ' + cls + '">' +
          '<div class="pipeline-dot"><i class="fa-solid ' + s.icon + '"></i></div>' +
          '<div class="pipeline-step-title">' + s.title + '</div>' +
          '<div class="pipeline-step-desc">' + s.desc + '</div>' +
        '</div>';
      }).join('') + '</div>'
    : '<div style="padding:16px; background:rgba(231,76,60,0.1); color:var(--danger); border-radius:10px; font-weight:700; text-align:center; margin:16px 0;">This order has been cancelled.</div>';

  return '' +
    '<div class="order-tracker-box">' +
      '<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; border-bottom:1px solid var(--border); padding-bottom:16px;">' +
        '<div>' +
          '<span style="font-size:12px; color:var(--text-muted); text-transform:uppercase; font-weight:700;">Order ID</span>' +
          '<h3 style="font-size:20px; color:var(--primary);">' + o.order_number + '</h3>' +
        '</div>' +
        '<div style="display:flex; gap:10px; align-items:center;">' +
          '<span class="status-badge status-' + o.status + '">' + o.status.replace(/_/g, ' ') + '</span>' +
          '<span class="status-badge status-' + o.payment_status + '"><i class="fa-solid fa-credit-card"></i> ' + o.payment_status + '</span>' +
        '</div>' +
      '</div>' +

      pipelineHtml +

      '<div style="background:var(--bg-light); border-radius:12px; padding:16px; border:1px solid var(--border); margin-top:16px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">' +
        '<div>' +
          '<div style="font-size:13px; font-weight:700; color:var(--text-main); margin-bottom:4px;"><i class="fa-solid fa-bag-shopping" style="color:var(--accent);"></i> Items: ' + itemsText + '</div>' +
          '<div style="font-size:12px; color:var(--text-muted);"><i class="fa-brands fa-whatsapp" style="color:#25D366;"></i> Live updates active for WhatsApp: ' + escapeHtml(o.customer_phone || 'Registered') + '</div>' +
        '</div>' +
        '<div style="text-align:right;">' +
          '<div style="font-size:12px; color:var(--text-muted);">Total Amount</div>' +
          '<div style="font-size:18px; font-weight:800; color:var(--primary);">' + money(o.total) + '</div>' +
        '</div>' +
      '</div>' +

      (cancellable ? '<div style="margin-top:14px; text-align:right;"><button class="btn-danger-sm" onclick="cancelOrder(' + o.id + ')"><i class="fa-solid fa-ban"></i> Cancel Order</button></div>' : '') +
    '</div>';
}

async function loadCustomerOrders() {
  const list = document.getElementById('orders-list');
  try {
    const page = await apiFetch('/orders');
    if (!page.items.length) {
      list.innerHTML = '<div class="empty-state"><i class="fa-solid fa-receipt"></i><p>You haven\'t placed any orders yet.</p>' +
        '<button class="btn-primary" onclick="switchTab(\'catalog\')" style="margin-top:12px;">Browse Fresh Menu</button></div>';
      return;
    }
    list.innerHTML = page.items.map(renderOrderHtml).join('');
  } catch (e) {
    list.innerHTML = '<p style="color:var(--danger);">' + e.message + '</p>';
  }
}

async function cancelOrder(id) {
  if (!confirm('Cancel this bakery order?')) return;
  try {
    await apiFetch('/orders/' + id + '/cancel', { method: 'PATCH' });
    showToast('Order cancelled.', 'info');
    renderOrdersView(document.getElementById('main-content'));
  } catch (e) { showToast(e.message, 'error'); }
}

// ----------------------------------------------------------------- about & story
function renderAboutTab(container) {
  container.innerHTML = '' +
    '<div style="text-align:center; max-width:760px; margin:0 auto 36px;">' +
      '<span class="status-badge status-DELIVERED" style="margin-bottom:10px;"><i class="fa-solid fa-heart"></i> Our Story &amp; Heritage</span>' +
      '<h2 style="font-size:32px; margin-bottom:14px; color:var(--text-main);">The Art of True French Baking in Pakistan</h2>' +
      '<p style="color:var(--text-muted); font-size:16px; line-height:1.6;">Founded with a single mission: to bring world-class European pastry artistry and authentic naturally fermented sourdough breads to every Pakistani household.</p>' +
    '</div>' +

    '<div style="display:grid; grid-template-columns:1fr 1fr; gap:32px; max-width:1100px; margin:0 auto 40px; align-items:center;">' +
      '<div>' +
        '<h3 style="font-size:22px; color:var(--text-main); margin-bottom:12px;">Our Uncompromising Baker\'s Pledge</h3>' +
        '<p style="color:var(--text-muted); font-size:14px; line-height:1.7; margin-bottom:16px;">At Freshco Bakers, we believe good food starts with honest ingredients. That is why every croissant is rolled by hand with 100% unadulterated dairy butter, every sourdough is given a 24-hour slow cold fermentation, and every celebration cake is sculpted with genuine Belgian cocoa.</p>' +
        '<div style="background:var(--surface); border:1px solid var(--border); border-radius:14px; padding:20px;">' +
          '<div style="font-weight:700; font-size:15px; color:var(--primary); margin-bottom:8px;"><i class="fa-solid fa-award"></i> Quality &amp; Hygiene Standards:</div>' +
          '<div style="font-size:13px; color:var(--text-muted); line-height:1.6;">' +
            '<div>&bull; ISO 22000 Food Safety &amp; HACCP Certified Facility</div>' +
            '<div>&bull; 100% Halal Ingredients with certified European imports</div>' +
            '<div>&bull; Daily morning microbiological health testing</div>' +
          '</div>' +
        '</div>' +
      '</div>' +
      '<div class="section-card" style="background:linear-gradient(135deg, #2C1810, #522E1B); color:#fff; padding:36px;">' +
        '<i class="fa-solid fa-quote-left" style="font-size:42px; color:var(--accent); margin-bottom:16px; opacity:0.8;"></i>' +
        '<p style="font-size:18px; font-style:italic; line-height:1.6; color:#FDFBF7; margin-bottom:20px;">"Baking is a science of patience and love. When you take that first bite of a warm sourdough loaf or rich Belgian cake, you should taste pure passion."</p>' +
        '<div style="font-weight:700; font-size:16px; color:var(--accent-light);">Head Master Baker &amp; Founder</div>' +
        '<div style="font-size:13px; color:#C2B6AE;">Freshco Bakers Culinary Studio</div>' +
      '</div>' +
    '</div>';
}

// ----------------------------------------------------------------- reviews
function renderReviewsTab(container) {
  const productOptions = state.products.map(p => '<option value="' + p.id + '">' + escapeHtml(p.name) + '</option>').join('');
  container.innerHTML = '' +
    '<div style="margin-bottom:24px;"><h2>Customer Reviews &amp; Feedback</h2><p style="color:var(--text-muted);">Verified reviews from customers across all bakery branches</p></div>' +
    '<div class="section-card" style="margin-bottom:24px; max-width:640px;">' +
      '<h3 style="margin-bottom:12px;">Leave a Verified Review</h3>' +
      '<p style="font-size:13px; color:var(--text-muted); margin-bottom:12px;">Share your taste experience with fellow bakery lovers.</p>' +
      '<form onsubmit="handleReviewSubmit(event)">' +
        '<div class="form-group"><label class="form-label">Select Bakery Item</label><select id="review-product" class="form-select" required>' + productOptions + '</select></div>' +
        '<div class="form-group"><label class="form-label">Star Rating</label><select id="review-rating" class="form-select">' +
          '<option value="5">★★★★★ (5 - Outstanding Taste &amp; Freshness)</option>' +
          '<option value="4">★★★★☆ (4 - Very Good)</option>' +
          '<option value="3">★★★☆☆ (3 - Satisfactory)</option>' +
          '<option value="2">★★☆☆☆ (2 - Needs Improvement)</option>' +
          '<option value="1">★☆☆☆☆ (1 - Disappointed)</option></select></div>' +
        '<div class="form-group"><label class="form-label">Your Review / Comments</label><textarea id="review-comment" class="form-control" rows="3" placeholder="Tell us about the texture, flavour, sweetness and packaging..."></textarea></div>' +
        '<button type="submit" class="btn-primary" style="width:100%; justify-content:center;"><i class="fa-solid fa-star"></i> Submit Review</button>' +
      '</form>' +
    '</div>' +
    '<div id="product-reviews-list"><p style="color:var(--text-muted);">Loading reviews...</p></div>';
  loadProductReviews();
}

async function loadProductReviews() {
  const el = document.getElementById('product-reviews-list');
  if (!state.products.length) { el.innerHTML = ''; return; }
  try {
    const sample = state.products.slice(0, 8);
    const results = [];
    for (const p of sample) {
      try { results.push(await apiFetch('/reviews/product/' + p.id, { auth: false })); }
      catch (e) { /* skip */ }
    }
    const withReviews = results.filter(r => r && r.items && r.items.length);
    if (!withReviews.length) {
      el.innerHTML = '<div class="empty-state"><i class="fa-solid fa-star"></i><p>No customer reviews yet. Be the first to review!</p></div>';
      return;
    }
    let cards = [];
    withReviews.forEach(r => {
      r.items.forEach(i => {
        cards.push('<div class="section-card"><div style="color:var(--accent); font-size:16px; margin-bottom:8px;">' +
          '★'.repeat(i.rating) + '☆'.repeat(5 - i.rating) + '</div>' +
          '<p style="font-style:italic; margin-bottom:12px; font-size:14px; line-height:1.5;">"' + escapeHtml(i.comment || 'Amazing fresh taste!') + '"</p>' +
          '<div style="font-weight:700; font-size:13px; color:var(--primary);">&mdash; ' + escapeHtml(i.customer_name || 'Customer') + '</div></div>');
      });
    });
    el.innerHTML = '<div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:20px;">' + cards.join('') + '</div>';
  } catch (e) {
    el.innerHTML = '<p style="color:var(--danger);">' + e.message + '</p>';
  }
}

async function handleReviewSubmit(event) {
  event.preventDefault();
  if (!requireLogin('Please sign in to leave a review.')) return;
  const productId = Number(document.getElementById('review-product').value);
  const rating = Number(document.getElementById('review-rating').value);
  const comment = document.getElementById('review-comment').value.trim() || null;
  try {
    await apiFetch('/reviews', { method: 'POST', body: { product_id: productId, rating: rating, comment: comment } });
    showToast('Review submitted successfully! Thank you for supporting Freshco.', 'success');
    event.target.reset();
    loadProductReviews();
  } catch (e) { showToast(e.message, 'error'); }
}

function handleNewsletterSubmit(event) {
  event.preventDefault();
  const email = document.getElementById('newsletter-email').value;
  showToast('Welcome to Freshco Club! Use promo code FRESH10 for 10% off your order.', 'success');
  event.target.reset();
}

// =================================================================
//  ADMIN VIEWS
// =================================================================
async function renderAdminDashboard(container) {
  if (!isStaff()) {
    container.innerHTML = renderAccessDenied('Executive Analytics Dashboard');
    return;
  }
  container.innerHTML = '' +
    '<div style="margin-bottom:24px;"><h2>Executive Analytics Dashboard</h2><p style="color:var(--text-muted);">Real-time financial, sales channels &amp; operational performance metrics</p></div>' +
    '<div class="stats-grid">' +
      '<div class="stat-card"><div class="stat-icon" style="background:rgba(39,174,96,0.15); color:var(--success);"><i class="fa-solid fa-coins"></i></div>' +
        '<div><div class="stat-val" id="stat-revenue">&mdash;</div><div class="stat-lbl">Total Gross Revenue</div></div></div>' +
      '<div class="stat-card"><div class="stat-icon" style="background:rgba(230,126,34,0.15); color:var(--accent);"><i class="fa-solid fa-receipt"></i></div>' +
        '<div><div class="stat-val" id="stat-orders">&mdash;</div><div class="stat-lbl">Total Orders</div></div></div>' +
      '<div class="stat-card"><div class="stat-icon" style="background:rgba(241,196,15,0.15); color:#D4AC0D;"><i class="fa-solid fa-clock"></i></div>' +
        '<div><div class="stat-val" id="stat-pending">&mdash;</div><div class="stat-lbl">Pending Kitchen Orders</div></div></div>' +
      '<div class="stat-card"><div class="stat-icon" style="background:rgba(231,76,60,0.15); color:var(--danger);"><i class="fa-solid fa-triangle-exclamation"></i></div>' +
        '<div><div class="stat-val" id="stat-lowstock">&mdash;</div><div class="stat-lbl">Low Stock Alerts</div></div></div>' +
    '</div>' +
    '<div id="top-products" style="margin-top:28px;"></div>';
  try {
    const data = await apiFetch('/analytics/dashboard');
    document.getElementById('stat-revenue').innerText = money(data.revenue);
    document.getElementById('stat-orders').innerText = data.total_orders;
    document.getElementById('stat-pending').innerText = data.pending_orders;
    document.getElementById('stat-lowstock').innerText = data.low_stock_count;
    const top = document.getElementById('top-products');
    if (data.top_products && data.top_products.length) {
      top.innerHTML = '<h3 style="margin-bottom:12px;">Top Selling Products</h3><div class="section-card">' +
        data.top_products.map(p => '<div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid var(--border);">' +
          '<span>' + escapeHtml(p.name) + '</span><strong>' + p.sold_quantity + ' sold</strong></div>').join('') + '</div>';
    }
  } catch (e) {
    showToast(e.message, 'error');
  }
}

// --- Admin: products
async function renderAdminProducts(container) {
  if (!isStaff()) {
    container.innerHTML = renderAccessDenied('Products Catalog Management');
    return;
  }
  container.innerHTML = '' +
    '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;">' +
      '<h2>Products Catalog Management</h2>' +
      '<button class="btn-primary" onclick="openProductModal()"><i class="fa-solid fa-plus"></i> Add New Product</button>' +
    '</div>' +
    '<div id="admin-products-table"><p style="color:var(--text-muted);">Loading...</p></div>';
  await refreshAdminProducts();
}

let adminProductsCache = [];

async function refreshAdminProducts() {
  const el = document.getElementById('admin-products-table');
  try {
    const page = await apiFetch('/products/admin/list?limit=100');
    adminProductsCache = page.items;
    if (!page.items.length) { el.innerHTML = '<div class="empty-state"><i class="fa-solid fa-box-open"></i><p>No products yet.</p></div>'; return; }
    el.innerHTML = '<table class="admin-table"><thead><tr><th>SKU</th><th>Name</th><th>Price</th><th>Status</th><th>Actions</th></tr></thead><tbody>' +
      page.items.map(p => '' +
        '<tr><td style="font-weight:700;">' + escapeHtml(p.sku) + '</td><td>' + escapeHtml(p.name) + '</td>' +
          '<td style="font-weight:700;">' + money(p.sale_price != null ? p.sale_price : p.price) + '</td>' +
          '<td><span class="status-badge status-' + (p.status === 'active' ? 'DELIVERED' : 'CANCELLED') + '">' + p.status + '</span></td>' +
          '<td style="display:flex; gap:8px;">' +
            '<button class="btn-secondary btn-sm" onclick="openProductModalById(' + p.id + ')">Edit</button>' +
            (p.status === 'active' ? '<button class="btn-danger-sm" onclick="archiveProduct(' + p.id + ')">Archive</button>' : '') +
          '</td></tr>').join('') +
      '</tbody></table>';
  } catch (e) {
    el.innerHTML = '<p style="color:var(--danger);">' + e.message + '</p>';
  }
}

function openProductModalById(id) {
  const product = adminProductsCache.find(p => p.id === id);
  openProductModal(product);
}

function openProductModal(product) {
  document.getElementById('product-modal-title').innerText = product ? 'Edit Product' : 'Add Product';
  document.getElementById('pf-id').value = product ? product.id : '';
  document.getElementById('pf-name').value = product ? product.name : '';
  document.getElementById('pf-sku').value = product ? product.sku : '';
  document.getElementById('pf-price').value = product ? product.price : '';
  document.getElementById('pf-sale-price').value = (product && product.sale_price != null) ? product.sale_price : '';
  document.getElementById('pf-description').value = (product && product.description) ? product.description : '';
  document.getElementById('pf-image-url').value = (product && product.images && product.images[0]) ? product.images[0].image_url : '';
  const catSelect = document.getElementById('pf-category');
  catSelect.innerHTML = '<option value="">No category</option>' +
    state.categories.map(c => '<option value="' + c.id + '" ' + (product && product.category_id === c.id ? 'selected' : '') + '>' + escapeHtml(c.name) + '</option>').join('');
  document.getElementById('product-modal').classList.add('active');
}
function closeProductModal() { document.getElementById('product-modal').classList.remove('active'); }

async function handleProductFormSubmit(event) {
  event.preventDefault();
  const id = document.getElementById('pf-id').value;
  const payload = {
    name: document.getElementById('pf-name').value.trim(),
    sku: document.getElementById('pf-sku').value.trim(),
    price: Number(document.getElementById('pf-price').value),
    sale_price: document.getElementById('pf-sale-price').value ? Number(document.getElementById('pf-sale-price').value) : null,
    category_id: document.getElementById('pf-category').value ? Number(document.getElementById('pf-category').value) : null,
    description: document.getElementById('pf-description').value.trim() || null,
  };
  const imageUrl = document.getElementById('pf-image-url').value.trim();
  try {
    let savedId = id;
    if (id) await apiFetch('/products/' + id, { method: 'PUT', body: payload });
    else { const created = await apiFetch('/products', { method: 'POST', body: payload }); savedId = created.id; }
    if (imageUrl) {
      await apiFetch('/products/' + savedId + '/images', { method: 'POST', body: { image_url: imageUrl, is_primary: true } });
    }
    showToast('Product saved.', 'success');
    closeProductModal();
    await loadCatalogData();
    refreshAdminProducts();
  } catch (e) { showToast(e.message, 'error'); }
}

async function archiveProduct(id) {
  if (!confirm('Archive this product? It will be hidden from the public catalog.')) return;
  try { await apiFetch('/products/' + id, { method: 'DELETE' }); showToast('Product archived.', 'info'); await loadCatalogData(); refreshAdminProducts(); }
  catch (e) { showToast(e.message, 'error'); }
}

// --- Admin: orders kanban
const KANBAN_COLUMNS = [
  { status: 'PENDING', label: 'Pending', next: 'CONFIRMED' },
  { status: 'CONFIRMED', label: 'Confirmed', next: 'PREPARING' },
  { status: 'PREPARING', label: 'Preparing', next: 'READY' },
  { status: 'READY', label: 'Ready', next: null },
  { status: 'DONE', label: 'Delivered / Picked Up', next: null },
];

async function renderAdminKanban(container) {
  if (!isStaff()) {
    container.innerHTML = renderAccessDenied('Kitchen Orders Kanban Board');
    return;
  }
  container.innerHTML = '<div style="margin-bottom:24px;"><h2>Kitchen Orders Kanban Board</h2>' +
    '<p style="color:var(--text-muted);">Live order status workflow &amp; fulfillment tracking</p></div>' +
    '<div id="kanban-board"><p style="color:var(--text-muted);">Loading...</p></div>';
  await refreshKanban();
}

async function refreshKanban() {
  const el = document.getElementById('kanban-board');
  try {
    const page = await apiFetch('/orders/admin/list?limit=100');
    const orders = page.items;
    const groups = { PENDING: [], CONFIRMED: [], PREPARING: [], READY: [], DONE: [] };
    orders.forEach(o => {
      if (o.status === 'DELIVERED' || o.status === 'PICKED_UP') groups.DONE.push(o);
      else if (groups[o.status]) groups[o.status].push(o);
    });
    el.innerHTML = '<div class="kanban-board">' + KANBAN_COLUMNS.map(col => {
      const orders2 = groups[col.status];
      const cards = orders2.map(o => {
        let nextBtn = '';
        if (col.next) {
          const label = col.next === 'CONFIRMED' ? 'Confirmed' : (col.next === 'PREPARING' ? 'Preparing' : 'Ready');
          nextBtn = '<button class="btn-primary btn-sm" style="margin-top:8px; width:100%; justify-content:center;" onclick="advanceOrder(' + o.id + ", '" + col.next + "')\">Move to " + label + '</button>';
        }
        let readyBtn = '';
        if (col.status === 'READY') {
          const target = o.order_type === 'DELIVERY' ? 'OUT_FOR_DELIVERY' : 'PICKED_UP';
          const label = o.order_type === 'DELIVERY' ? 'Send Out for Delivery' : 'Mark Picked Up';
          readyBtn = '<button class="btn-primary btn-sm" style="margin-top:8px; width:100%; justify-content:center;" onclick="advanceOrder(' + o.id + ", '" + target + "')\">" + label + '</button>';
        }
        const cancelBtn = col.status !== 'DONE' ? '<button class="btn-danger-sm" style="margin-top:6px; width:100%;" onclick="advanceOrder(' + o.id + ", 'CANCELLED')\">Cancel</button>" : '';
        return '<div class="order-card"><div style="font-weight:700; font-size:14px;">#' + o.order_number + '</div>' +
          '<div style="font-size:12px; color:var(--text-muted);">' + escapeHtml(o.customer_name || 'Guest') + ' &middot; ' + o.order_type + '</div>' +
          '<div style="margin-top:8px; font-weight:800; color:var(--primary);">' + money(o.total) + '</div>' + nextBtn + readyBtn + cancelBtn + '</div>';
      }).join('') || '<p style="font-size:13px; color:var(--text-muted); padding:8px;">No orders</p>';
      return '<div class="kanban-col"><div class="kanban-header">' + col.label.toUpperCase() + ' (' + orders2.length + ')</div>' + cards + '</div>';
    }).join('') + '</div>';
  } catch (e) {
    el.innerHTML = '<p style="color:var(--danger);">' + e.message + '</p>';
  }
}

async function advanceOrder(orderId, newStatus) {
  try {
    await apiFetch('/orders/' + orderId + '/status', { method: 'PATCH', body: { status: newStatus } });
    showToast('Order updated.', 'success');
    refreshKanban();
  } catch (e) { showToast(e.message, 'error'); }
}

// --- Admin: inventory
async function renderAdminInventory(container) {
  if (!isStaff()) {
    container.innerHTML = renderAccessDenied('Inventory Management');
    return;
  }
  const productOptions = state.products.map(p => '<option value="' + p.id + '">' + escapeHtml(p.name) + '</option>').join('');
  container.innerHTML = '' +
    '<div style="margin-bottom:24px;"><h2>Inventory Management</h2><p style="color:var(--text-muted);">Branch-level stock levels &amp; quick stock adjustments</p></div>' +
    '<div class="section-card"><h3 style="margin-bottom:12px;">Quick Stock Adjustment</h3>' +
      '<form onsubmit="handleStockAdjust(event)" style="display:grid; grid-template-columns:2fr 1fr 1fr 1fr auto; gap:10px; align-items:end;">' +
        '<div class="form-group" style="margin:0;"><label class="form-label">Product</label><select id="adj-product" class="form-select">' + productOptions + '</select></div>' +
        '<div class="form-group" style="margin:0;"><label class="form-label">Branch ID</label><input id="adj-branch" type="number" class="form-control" value="1" required></div>' +
        '<div class="form-group" style="margin:0;"><label class="form-label">Type</label><select id="adj-type" class="form-select"><option>PURCHASE</option><option>WASTE</option><option>ADJUSTMENT</option><option>RETURN</option></select></div>' +
        '<div class="form-group" style="margin:0;"><label class="form-label">Qty</label><input id="adj-qty" type="number" class="form-control" value="10" required></div>' +
        '<button class="btn-primary" type="submit">Apply</button>' +
      '</form></div>' +
    '<div id="inventory-table"><p style="color:var(--text-muted);">Loading...</p></div>';
  await refreshInventory();
}

async function refreshInventory() {
  const el = document.getElementById('inventory-table');
  try {
    const page = await apiFetch('/inventory?limit=100');
    if (!page.items.length) { el.innerHTML = '<div class="empty-state"><i class="fa-solid fa-boxes-stacked"></i><p>No stock records yet. Use the form above to add stock.</p></div>'; return; }
    el.innerHTML = '<table class="admin-table"><thead><tr><th>Product</th><th>Branch</th><th>On Hand</th><th>Reserved</th><th>Available</th><th>Status</th></tr></thead><tbody>' +
      page.items.map(i => '<tr><td>' + escapeHtml(i.product_name) + '</td><td>' + escapeHtml(i.branch_name) + '</td>' +
        '<td>' + i.quantity + '</td><td>' + i.reserved_quantity + '</td><td>' + i.available_quantity + '</td>' +
        '<td>' + (i.is_low ? '<span class="status-badge status-CANCELLED">Low Stock</span>' : '<span class="status-badge status-DELIVERED">OK</span>') + '</td></tr>').join('') +
      '</tbody></table>';
  } catch (e) {
    el.innerHTML = '<p style="color:var(--danger);">' + e.message + '</p>';
  }
}

async function handleStockAdjust(event) {
  event.preventDefault();
  const payload = {
    product_id: Number(document.getElementById('adj-product').value),
    branch_id: Number(document.getElementById('adj-branch').value),
    type: document.getElementById('adj-type').value,
    quantity: Number(document.getElementById('adj-qty').value),
  };
  try {
    await apiFetch('/inventory/adjust', { method: 'POST', body: payload });
    showToast('Stock updated.', 'success');
    refreshInventory();
  } catch (e) { showToast(e.message, 'error'); }
}

// --- Admin: cake quotes
async function renderAdminCakeQuotes(container) {
  if (!isStaff()) {
    container.innerHTML = renderAccessDenied('Custom Cake Quotes Management');
    return;
  }
  container.innerHTML = '<div style="margin-bottom:24px;"><h2>Custom Cake Quotes</h2><p style="color:var(--text-muted);">Review customer designs and issue price quotes</p></div>' +
    '<div id="admin-cakes-list"><p style="color:var(--text-muted);">Loading...</p></div>';
  await refreshAdminCakes();
}

async function refreshAdminCakes() {
  const el = document.getElementById('admin-cakes-list');
  try {
    const page = await apiFetch('/custom-cakes/admin/list?limit=100');
    if (!page.items.length) { el.innerHTML = '<div class="empty-state"><i class="fa-solid fa-cake-candles"></i><p>No requests yet.</p></div>'; return; }
    el.innerHTML = page.items.map(r => {
      let actions = '';
      if (r.status === 'pending') {
        actions = '<div style="display:flex; gap:8px;"><input type="number" id="quote-' + r.id + '" class="form-control" placeholder="Quote amount (Rs)" style="max-width:180px;">' +
          '<button class="btn-primary btn-sm" onclick="submitQuote(' + r.id + ')">Send Quote</button></div>';
      } else if (r.status === 'accepted') {
        actions = '<button class="btn-primary btn-sm" onclick="setCakeStatus(' + r.id + ", 'in_progress')\">Start Making</button>";
      } else if (r.status === 'in_progress') {
        actions = '<button class="btn-primary btn-sm" onclick="setCakeStatus(' + r.id + ", 'done')\">Mark Done</button>";
      }
      return '<div class="section-card">' +
        '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">' +
          '<strong>' + escapeHtml(r.customer_name || 'Customer') + '</strong><span class="status-badge status-' + r.status + '">' + r.status.replace('_', ' ') + '</span></div>' +
        '<div style="font-size:14px; margin-bottom:12px;">' + escapeHtml(r.flavour) + ' &middot; ' + escapeHtml(r.size) + ' &middot; needed ' + r.requested_date +
          (r.theme ? ' &middot; theme: ' + escapeHtml(r.theme) : '') + (r.message ? ' &middot; msg: "' + escapeHtml(r.message) + '"' : '') + '</div>' +
        actions + '</div>';
    }).join('');
  } catch (e) {
    el.innerHTML = '<p style="color:var(--danger);">' + e.message + '</p>';
  }
}

async function submitQuote(id) {
  const amount = Number(document.getElementById('quote-' + id).value);
  if (!amount || amount <= 0) { showToast('Enter a valid quote amount.', 'error'); return; }
  try { await apiFetch('/custom-cakes/' + id + '/quote', { method: 'PATCH', body: { quote_amount: amount } }); showToast('Quote sent.', 'success'); refreshAdminCakes(); }
  catch (e) { showToast(e.message, 'error'); }
}
async function setCakeStatus(id, status) {
  try { await apiFetch('/custom-cakes/' + id + '/status', { method: 'PATCH', body: { status: status } }); showToast('Updated.', 'success'); refreshAdminCakes(); }
  catch (e) { showToast(e.message, 'error'); }
}

// --- Admin: staff
async function renderAdminStaff(container) {
  if (!isStaff()) {
    container.innerHTML = renderAccessDenied('Staff & Permissions Management');
    return;
  }
  container.innerHTML = '' +
    '<div style="margin-bottom:24px;"><h2>Staff &amp; Employee Permissions</h2><p style="color:var(--text-muted);">Manage Cashier, Manager and Admin accounts</p></div>' +
    '<div class="section-card"><h3 style="margin-bottom:12px;">Add Staff Member</h3>' +
      '<form onsubmit="handleAddStaff(event)" style="display:grid; grid-template-columns:1.5fr 1.5fr 1.5fr 1fr auto; gap:10px; align-items:end;">' +
        '<div class="form-group" style="margin:0;"><label class="form-label">Name</label><input id="staff-name" class="form-control" required></div>' +
        '<div class="form-group" style="margin:0;"><label class="form-label">Email</label><input id="staff-email" type="email" class="form-control" required></div>' +
        '<div class="form-group" style="margin:0;"><label class="form-label">Password</label><input id="staff-password" type="password" class="form-control" required minlength="8"></div>' +
        '<div class="form-group" style="margin:0;"><label class="form-label">Role</label><select id="staff-role" class="form-select"><option value="cashier">Cashier</option><option value="manager">Manager</option><option value="admin">Admin</option></select></div>' +
        '<button class="btn-primary" type="submit">Add</button>' +
      '</form></div>' +
    '<div id="staff-table"><p style="color:var(--text-muted);">Loading...</p></div>';
  await refreshStaff();
}

async function refreshStaff() {
  const el = document.getElementById('staff-table');
  try {
    const staff = await apiFetch('/staff');
    if (!staff.length) { el.innerHTML = '<div class="empty-state"><i class="fa-solid fa-users"></i><p>No staff members yet.</p></div>'; return; }
    el.innerHTML = '<table class="admin-table"><thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th></tr></thead><tbody>' +
      staff.map(s => '<tr><td>' + escapeHtml(s.name) + '</td><td>' + escapeHtml(s.email) + '</td><td style="text-transform:capitalize;">' + s.role + '</td>' +
        '<td><span class="status-badge status-DELIVERED">' + s.status + '</span></td></tr>').join('') +
      '</tbody></table>';
  } catch (e) {
    el.innerHTML = '<p style="color:var(--danger);">' + e.message + '</p>';
  }
}

async function handleAddStaff(event) {
  event.preventDefault();
  const payload = {
    name: document.getElementById('staff-name').value.trim(),
    email: document.getElementById('staff-email').value.trim(),
    password: document.getElementById('staff-password').value,
    role: document.getElementById('staff-role').value,
  };
  try {
    await apiFetch('/staff', { method: 'POST', body: payload });
    showToast('Staff member added.', 'success');
    event.target.reset();
    refreshStaff();
  } catch (e) { showToast(e.message, 'error'); }
}

// --- Admin: settings
async function renderAdminSettings(container) {
  if (!isStaff()) {
    container.innerHTML = renderAccessDenied('Store Settings');
    return;
  }
  container.innerHTML = '<div style="margin-bottom:24px;"><h2>Bakery Store Settings</h2><p style="color:var(--text-muted);">Delivery fee and tax rate used at checkout</p></div>' +
    '<div class="section-card" id="settings-form-wrap"><p style="color:var(--text-muted);">Loading...</p></div>';
  try {
    const settings = await apiFetch('/settings');
    const deliveryFee = (settings['delivery.fee_flat'] && settings['delivery.fee_flat'].amount) || 0;
    const taxPercent = (settings['tax.rate_percent'] && settings['tax.rate_percent'].percent) || 0;
    document.getElementById('settings-form-wrap').innerHTML = '' +
      '<form onsubmit="handleSaveSettings(event)">' +
        '<div class="form-group"><label class="form-label">Flat Delivery Fee (Rs)</label><input id="set-delivery-fee" type="number" step="0.01" class="form-control" value="' + deliveryFee + '"></div>' +
        '<div class="form-group"><label class="form-label">Tax Rate (%)</label><input id="set-tax-percent" type="number" step="0.01" class="form-control" value="' + taxPercent + '"></div>' +
        '<button class="btn-primary" type="submit">Save Settings</button>' +
      '</form>';
  } catch (e) {
    document.getElementById('settings-form-wrap').innerHTML = '<p style="color:var(--danger);">' + e.message + '</p>';
  }
}

async function handleSaveSettings(event) {
  event.preventDefault();
  const payload = {
    settings: [
      { key: 'delivery.fee_flat', value: { amount: Number(document.getElementById('set-delivery-fee').value) }, category: 'delivery' },
      { key: 'tax.rate_percent', value: { percent: Number(document.getElementById('set-tax-percent').value) }, category: 'tax' },
    ],
  };
  try { await apiFetch('/settings', { method: 'PUT', body: payload }); showToast('Settings saved.', 'success'); }
  catch (e) { showToast(e.message, 'error'); }
}

// =================================================================
//  POS VIEW
// =================================================================
function renderPOSView(container) {
  if (!isStaff()) {
    container.innerHTML = renderAccessDenied('POS Counter Billing');
    return;
  }

  const quickItems = state.products.map(p => '' +
    '<div class="tilt-card" onclick="addToPOSCart(' + p.id + ')" style="cursor:pointer; padding:16px; text-align:center;">' +
      '<i class="fa-solid fa-cookie" style="font-size:32px; color:var(--primary); margin-bottom:8px;"></i>' +
      '<div style="font-weight:700; font-size:15px;">' + escapeHtml(p.name) + '</div>' +
      '<div style="color:var(--accent); font-weight:800; margin-top:4px;">' + money(p.sale_price != null ? p.sale_price : p.price) + '</div>' +
    '</div>').join('');

  container.innerHTML = '' +
    '<div style="display:grid; grid-template-columns: 2fr 1fr; gap:24px;">' +
      '<div>' +
        '<div style="display:flex; gap:12px; margin-bottom:20px;">' +
          '<input type="text" id="pos-barcode" class="form-control" placeholder="Scan Barcode or SKU..." autofocus onkeypress="if(event.key===\'Enter\') handlePOSBarcodeScan()">' +
          '<button class="btn-primary" onclick="handlePOSBarcodeScan()"><i class="fa-solid fa-barcode"></i> Scan</button>' +
        '</div>' +
        '<h3 style="margin-bottom:16px;">Quick Items</h3>' +
        '<div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(180px, 1fr)); gap:16px;">' + quickItems + '</div>' +
      '</div>' +
      '<div style="background:var(--surface); padding:24px; border-radius:var(--radius-lg); border:1px solid var(--border); box-shadow:var(--shadow-md);">' +
        '<h3 style="margin-bottom:16px;"><i class="fa-solid fa-cash-register"></i> Counter Order Cart</h3>' +
        '<div id="pos-cart-list" style="min-height:200px; max-height:320px; overflow-y:auto; margin-bottom:20px;"></div>' +
        '<div class="form-group"><label class="form-label">Payment Method</label><select id="pos-pay-method" class="form-select">' +
          '<option value="CASH">Cash Counter</option><option value="CARD">Card POS Reader</option><option value="WALLET">JazzCash / EasyPaisa</option></select></div>' +
        '<button class="btn-primary" onclick="completePOSSale()" style="width:100%; justify-content:center; padding:16px; font-size:16px;"><i class="fa-solid fa-check-double"></i> Complete Sale &amp; Print Receipt</button>' +
      '</div>' +
    '</div>';
  renderPOSCartList();
}

async function handlePOSBarcodeScan() {
  if (!isStaff()) {
    showToast('Access restricted: Staff credentials required.', 'error');
    return;
  }
  const input = document.getElementById('pos-barcode');
  const code = input.value.trim();
  if (!code) return;
  try {
    const product = await apiFetch('/pos/barcode/' + encodeURIComponent(code));
    addToPOSCart(product.id, product);
    input.value = '';
  } catch (e) {
    showToast(e.message, 'error');
  }
}

function addToPOSCart(productId, knownProduct) {
  if (!isStaff()) return;
  const prod = knownProduct || state.products.find(p => p.id === productId);
  if (!prod) return;
  const existing = posCart.find(i => i.product_id === productId);
  if (existing) existing.quantity += 1;
  else posCart.push({ product_id: productId, name: prod.name, price: (prod.sale_price != null ? prod.sale_price : prod.price), quantity: 1 });
  renderPOSCartList();
}

function posChangeQty(productId, delta) {
  const item = posCart.find(i => i.product_id === productId);
  if (!item) return;
  item.quantity = Math.max(1, item.quantity + delta);
  renderPOSCartList();
}
function posRemove(productId) { posCart = posCart.filter(i => i.product_id !== productId); renderPOSCartList(); }

function renderPOSCartList() {
  const list = document.getElementById('pos-cart-list');
  if (!list) return;
  if (!posCart.length) { list.innerHTML = '<p style="color:var(--text-muted); text-align:center; margin-top:40px;">No items scanned</p>'; return; }
  let total = 0;
  const rows = posCart.map(item => {
    const itemTotal = item.price * item.quantity;
    total += itemTotal;
    return '<div class="cart-item-row"><div style="flex:1;"><div style="font-weight:700;">' + escapeHtml(item.name) + '</div>' +
      '<div style="font-size:12px; color:var(--text-muted);">' + money(item.price) + ' each</div></div>' +
      '<div class="qty-stepper"><button onclick="posChangeQty(' + item.product_id + ', -1)">-</button><span>' + item.quantity + '</span><button onclick="posChangeQty(' + item.product_id + ', 1)">+</button></div>' +
      '<button class="icon-link-btn" onclick="posRemove(' + item.product_id + ')"><i class="fa-solid fa-trash"></i></button></div>';
  }).join('');
  list.innerHTML = rows + '<div style="display:flex; justify-content:space-between; margin-top:16px; font-size:18px; font-weight:800;"><span>Total:</span><span style="color:var(--primary);">' + money(total) + '</span></div>';
}

async function completePOSSale() {
  if (!posCart.length) { showToast('Cart is empty.', 'error'); return; }
  if (!isStaff()) { showToast('Sign in with a cashier/staff account to complete a sale.', 'error'); openAuthModal(); return; }
  const total = posCart.reduce((sum, i) => sum + i.price * i.quantity, 0);
  const payload = {
    items: posCart.map(i => ({ product_id: i.product_id, quantity: i.quantity })),
    payment_method: document.getElementById('pos-pay-method').value,
    amount_paid: total,
  };
  try {
    const order = await apiFetch('/pos/sales', { method: 'POST', body: payload });
    openThermalReceiptModal(order);
    posCart = [];
    renderPOSCartList();
    showToast('Sale completed.', 'success');
  } catch (e) {
    showToast(e.message, 'error');
  }
}

function openThermalReceiptModal(order) {
  const modal = document.getElementById('receipt-modal');
  const content = document.getElementById('thermal-receipt-content');
  const items = order.items || [];
  const itemLines = items.map(i => '<div style="display:flex; justify-content:space-between; font-size:12px;"><span>' +
    escapeHtml(i.product_name) + ' x' + i.quantity + '</span><span>' + money(i.total) + '</span></div>').join('');
  content.innerHTML = '' +
    '<div style="text-align:center;"><h2 style="font-size:20px; font-weight:800;">FRESHCO BAKERS</h2>' +
      '<p style="font-size:12px;">Freshness Baked Daily</p><p style="font-size:11px; margin-top:4px;">Receipt #' + order.order_number + '</p></div>' +
    '<div class="thermal-line"></div>' + itemLines + '<div class="thermal-line"></div>' +
    '<div style="display:flex; justify-content:space-between; font-weight:800; font-size:14px;"><span>TOTAL PAID:</span><span>' + money(order.total) + '</span></div>' +
    '<div style="text-align:center; font-size:11px; margin-top:12px;">Thank you for visiting Freshco Bakers!</div>';
  modal.classList.add('active');
}
function closeReceiptModal() { document.getElementById('receipt-modal').classList.remove('active'); }

// ---------------------------------------------------- 3D tilt card engine
function attach3DTiltListeners() {
  document.querySelectorAll('.tilt-card').forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      card.style.transform = 'perspective(1000px) rotateX(' + (-y / 10) + 'deg) rotateY(' + (x / 10) + 'deg) scale(1.02)';
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale(1)';
    });
  });
}
