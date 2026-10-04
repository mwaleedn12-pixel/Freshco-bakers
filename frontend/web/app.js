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
function requireLogin(msg) {
  if (!isLoggedIn()) { showToast(msg || 'Please sign in first.', 'error'); openAuthModal(); return false; }
  return true;
}

// -------------------------------------------------------------------- init
document.addEventListener('DOMContentLoaded', () => { initApp(); });

async function initApp() {
  if (state.token) {
    try { state.currentUser = await apiFetch('/auth/me'); }
    catch (e) { logout(false); }
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
      showToast('Welcome back, ' + data.user.name + '!', 'success');
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
  if (!btnText) return;
  if (state.currentUser) {
    btnText.innerText = state.currentUser.name;
    userBtn.onclick = function () { if (confirm('Sign out of Freshco Bakers?')) logout(); };
  } else {
    btnText.innerText = 'Sign In';
    userBtn.onclick = openAuthModal;
  }
}

// ------------------------------------------------------- role / tab router
function switchRole(role) {
  if (role !== 'customer' && !isStaff()) {
    showToast('Sign in with a staff account (cashier/manager/admin/owner) to open this view.', 'error');
    openAuthModal();
    return;
  }
  state.currentRole = role;
  document.querySelectorAll('.role-btn').forEach(btn => btn.classList.remove('active'));
  document.getElementById('btn-role-' + role).classList.add('active');

  const customerNav = document.getElementById('customer-nav');
  const adminNav = document.getElementById('admin-nav');
  const cartBtn = document.getElementById('cart-btn');

  customerNav.style.display = role === 'customer' ? 'block' : 'none';
  adminNav.style.display = role === 'admin' ? 'block' : 'none';
  cartBtn.style.display = role === 'customer' ? 'flex' : 'none';
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
  state.currentTab = tab;
  document.querySelectorAll('#admin-nav .nav-link').forEach(l => l.classList.remove('active'));
  const active = document.getElementById('admin-nav-' + tab);
  if (active) active.classList.add('active');
  renderApp();
}

function renderApp() {
  const container = document.getElementById('main-content');
  updateUserUI();

  if (state.currentRole === 'customer') {
    if (state.currentTab === 'home') container.innerHTML = renderCustomerHome();
    else if (state.currentTab === 'catalog') container.innerHTML = renderCatalogView();
    else if (state.currentTab === 'cake') renderCustomCakeTab(container);
    else if (state.currentTab === 'orders') renderOrdersView(container);
    else if (state.currentTab === 'reviews') renderReviewsTab(container);
  } else if (state.currentRole === 'admin') {
    if (state.currentTab === 'overview') renderAdminDashboard(container);
    else if (state.currentTab === 'products') renderAdminProducts(container);
    else if (state.currentTab === 'orders-kanban') renderAdminKanban(container);
    else if (state.currentTab === 'inventory') renderAdminInventory(container);
    else if (state.currentTab === 'cakes') renderAdminCakeQuotes(container);
    else if (state.currentTab === 'staff') renderAdminStaff(container);
    else if (state.currentTab === 'settings') renderAdminSettings(container);
  } else if (state.currentRole === 'pos') {
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
      'style="width:100%; height:' + heightPx + 'px; object-fit:cover; display:block;" ' +
      'onerror="this.replaceWith(Object.assign(document.createElement(\'div\'),{innerHTML:' + JSON.stringify('<i class="fa-solid fa-wheat-awn" style="font-size:48px; color:var(--primary);"></i>').replace(/"/g, '&quot;') + ',style:\'height:' + heightPx + 'px; display:flex; align-items:center; justify-content:center; background:linear-gradient(135deg, #FDFBF7, #E8DCCF);\'}))">';
  }
  return '<div style="height:' + heightPx + 'px; background:linear-gradient(135deg, #FDFBF7, #E8DCCF); display:flex; align-items:center; justify-content:center;">' +
    '<i class="fa-solid fa-wheat-awn" style="font-size:48px; color:var(--primary);"></i></div>';
}

function ratingHtml(p) {
  const avg = p.average_rating || 0;
  const count = p.review_count || 0;
  if (!count) return '<div style="font-size:12px; color:var(--text-muted); margin-bottom:6px;">No reviews yet</div>';
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
    '<div class="tilt-card" data-tilt style="position:relative;">' +
      '<button class="wishlist-heart ' + (inWishlist ? 'active' : '') + '" onclick="event.stopPropagation(); toggleWishlist(' + p.id + ')" title="Save to wishlist">' +
        '<i class="fa-' + (inWishlist ? 'solid' : 'regular') + ' fa-heart"></i></button>' +
      (p.is_featured ? '<div class="product-badge">Featured</div>' : '') +
      productImageHtml(p, 160) +
      '<div class="product-info">' +
        '<h3 class="product-title">' + escapeHtml(p.name) + '</h3>' +
        '<p class="product-desc">' + escapeHtml(p.description || 'Delicious freshly baked artisan item.') + '</p>' +
        ratingHtml(p) +
        '<div style="margin-bottom:8px;">' + (unavailable
          ? '<span class="status-badge status-CANCELLED">Out of Stock</span>'
          : '<span class="status-badge status-DELIVERED">Available</span>') + '</div>' +
        '<div class="product-bottom">' +
          '<div class="product-price">' + money(price) + (p.sale_price ? ' <span style="text-decoration:line-through; color:#999; font-size:13px;">' + money(p.price) + '</span>' : '') + '</div>' +
        '</div>' +
        '<div style="display:flex; gap:8px; margin-top:10px;">' +
          '<button class="btn-secondary btn-sm" style="flex:1; justify-content:center;" onclick="openProductDetails(' + p.id + ')">View Details</button>' +
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

// --------------------------------------------------------- product details
function openProductDetails(productId) {
  const p = state.products.find(x => x.id === productId);
  if (!p) return;
  const price = p.sale_price != null ? p.sale_price : p.price;
  const unavailable = p.is_available === false;
  document.getElementById('details-modal-body').innerHTML = '' +
    productImageHtml(p, 240) +
    '<div style="padding:20px 0 0;">' +
      '<h2 style="margin-bottom:6px;">' + escapeHtml(p.name) + '</h2>' +
      ratingHtml(p) +
      '<p style="color:var(--text-muted); margin:10px 0;">' + escapeHtml(p.description || 'Delicious freshly baked artisan item.') + '</p>' +
      '<div style="font-size:24px; font-weight:800; color:var(--primary); margin:10px 0;">' + money(price) +
        (p.sale_price ? ' <span style="text-decoration:line-through; color:#999; font-size:15px;">' + money(p.price) + '</span>' : '') + '</div>' +
      '<div style="margin-bottom:16px;">' + (unavailable
        ? '<span class="status-badge status-CANCELLED">Out of Stock</span>'
        : '<span class="status-badge status-DELIVERED">Available</span>') + '</div>' +
      '<div style="display:flex; gap:10px;">' +
        '<button class="btn-primary" style="flex:1; justify-content:center;" ' + (unavailable ? 'disabled' : '') +
          ' onclick="addToCart(' + p.id + '); closeProductDetails();"><i class="fa-solid fa-cart-plus"></i> Add to Cart</button>' +
        '<button class="btn-secondary" onclick="toggleWishlist(' + p.id + '); closeProductDetails();"><i class="fa-regular fa-heart"></i></button>' +
      '</div>' +
    '</div>';
  document.getElementById('details-modal').classList.add('active');
}
function closeProductDetails() { document.getElementById('details-modal').classList.remove('active'); }

// --------------------------------------------------------- customer: home
function renderCustomerHome() {
  const featured = state.products.filter(p => p.is_featured).slice(0, 4);
  const toShow = featured.length ? featured : state.products.slice(0, 4);
  return '' +
    '<div class="hero-section">' +
      '<div>' +
        '<h1 class="hero-title">Freshness Baked Daily in 3D Perspective</h1>' +
        '<p class="hero-subtitle">Order hand-crafted artisan sourdoughs, gourmet cakes, and pastries warm to your doorstep.</p>' +
        '<button class="btn-primary" onclick="switchTab(\'catalog\')" style="padding:14px 28px; font-size:16px;">' +
          '<i class="fa-solid fa-basket-shopping"></i> Explore Full Catalog</button>' +
      '</div>' +
      '<div style="text-align:center;">' +
        '<div class="tilt-card" style="padding:24px; background:rgba(255,255,255,0.1); border-color:rgba(255,255,255,0.2); backdrop-filter:blur(10px);">' +
          '<i class="fa-solid fa-cake-candles" style="font-size:72px; color:var(--accent); margin-bottom:16px;"></i>' +
          '<h3 style="color:#fff; font-size:22px;">Custom Celebration Cakes</h3>' +
          '<p style="color:rgba(255,255,255,0.7); margin:8px 0 16px;">Design your dream cake with real-time quote generation</p>' +
          '<button class="btn-secondary" onclick="switchTab(\'cake\')">Order Custom Cake</button>' +
        '</div>' +
      '</div>' +
    '</div>' +
    '<div style="margin-bottom:24px; display:flex; justify-content:space-between; align-items:center;">' +
      '<h2>Featured Today</h2>' +
      '<a href="#" onclick="switchTab(\'catalog\')" style="color:var(--primary); font-weight:700; text-decoration:none;">View All (' + state.products.length + ') &rarr;</a>' +
    '</div>' +
    (toShow.length
      ? '<div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:24px;">' + toShow.map(productCard).join('') + '</div>'
      : '<div class="empty-state"><i class="fa-solid fa-bread-slice"></i><p>No products yet — add some from the Admin Dashboard.</p></div>');
}

// ------------------------------------------------------- customer: catalog
function renderCatalogView() {
  const categoryOptions = state.categories.map(c => '<option value="' + c.id + '">' + escapeHtml(c.name) + '</option>').join('');
  const grid = state.products.length ? state.products.map(productCard).join('')
    : '<div class="empty-state" style="grid-column:1/-1;"><i class="fa-solid fa-magnifying-glass"></i><p>No products found.</p></div>';
  return '' +
    '<div style="margin-bottom:24px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:16px;">' +
      '<div><h2>Fresh Bakery Menu</h2><p style="color:var(--text-muted);">Browse our complete selection of fresh breads, cakes &amp; pastries</p></div>' +
      '<div style="display:flex; gap:10px; flex-wrap:wrap;">' +
        '<select id="catalog-category" class="form-select" style="width:180px;" onchange="filterCatalog()"><option value="">All categories</option>' + categoryOptions + '</select>' +
        '<input type="text" id="catalog-search" class="form-control" placeholder="Search cakes, sourdough, croissants..." onkeyup="filterCatalog()" style="width:260px;">' +
      '</div>' +
    '</div>' +
    '<div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:24px;" id="catalog-grid">' + grid + '</div>';
}

function filterCatalog() {
  const term = (document.getElementById('catalog-search').value || '').toLowerCase();
  const categoryId = document.getElementById('catalog-category').value;
  const grid = document.getElementById('catalog-grid');
  const filtered = state.products.filter(p => {
    const matchesTerm = !term || p.name.toLowerCase().indexOf(term) !== -1 || (p.description || '').toLowerCase().indexOf(term) !== -1;
    const matchesCat = !categoryId || String(p.category_id) === categoryId;
    return matchesTerm && matchesCat;
  });
  grid.innerHTML = filtered.length ? filtered.map(productCard).join('')
    : '<div class="empty-state" style="grid-column:1/-1;"><i class="fa-solid fa-magnifying-glass"></i><p>No products match your search.</p></div>';
  attach3DTiltListeners();
}

// ---------------------------------------------------------------- cart
function addToCart(productId) {
  const prod = state.products.find(p => p.id === productId);
  if (!prod) return;
  const existing = state.cart.find(i => i.product_id === productId);
  if (existing) existing.quantity += 1;
  else state.cart.push({ product_id: productId, name: prod.name, price: (prod.sale_price != null ? prod.sale_price : prod.price), quantity: 1 });
  updateCartBadge();
  showToast(prod.name + ' added to cart', 'success');
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

function renderCartModal() {
  const body = document.getElementById('cart-modal-body');
  const total = state.cart.reduce((sum, i) => sum + i.price * i.quantity, 0);
  if (!state.cart.length) {
    body.innerHTML = '<div class="empty-state"><i class="fa-solid fa-basket-shopping"></i><p>Your cart is empty.</p></div>';
    return;
  }
  const rows = state.cart.map(i => '' +
    '<div class="cart-item-row">' +
      '<div style="flex:1;"><div style="font-weight:700;">' + escapeHtml(i.name) + '</div><div style="font-size:13px; color:var(--text-muted);">' + money(i.price) + ' each</div></div>' +
      '<div class="qty-stepper"><button onclick="cartChangeQty(' + i.product_id + ', -1)">-</button><span>' + i.quantity + '</span><button onclick="cartChangeQty(' + i.product_id + ', 1)">+</button></div>' +
      '<button class="icon-link-btn" onclick="cartRemove(' + i.product_id + ')"><i class="fa-solid fa-trash"></i></button>' +
    '</div>').join('');

  body.innerHTML = rows +
    '<div style="display:flex; justify-content:space-between; margin:16px 0; font-size:18px; font-weight:800;"><span>Total</span><span style="color:var(--primary);">' + money(total) + '</span></div>' +
    '<div class="form-group"><label class="form-label">Order Type</label>' +
      '<select id="checkout-order-type" class="form-select"><option value="PICKUP">Pickup from bakery</option><option value="DELIVERY">Delivery</option></select></div>' +
    '<div class="form-group" id="checkout-address-group" style="display:none;"><label class="form-label">Delivery Address</label>' +
      '<input type="text" id="checkout-address" class="form-control" placeholder="House, street, city"></div>' +
    '<button class="btn-primary" style="width:100%; justify-content:center; padding:14px;" onclick="handleCheckout()"><i class="fa-solid fa-circle-check"></i> Place Order</button>';

  document.getElementById('checkout-order-type').onchange = function (e) {
    document.getElementById('checkout-address-group').style.display = e.target.value === 'DELIVERY' ? 'block' : 'none';
  };
}

async function handleCheckout() {
  if (!state.cart.length) return;
  if (!requireLogin('Please sign in to place an order.')) return;

  const orderType = document.getElementById('checkout-order-type').value;
  let addressId = null;

  try {
    if (orderType === 'DELIVERY') {
      const line1 = document.getElementById('checkout-address').value.trim();
      if (!line1) { showToast('Please enter a delivery address.', 'error'); return; }
      const address = await apiFetch('/addresses', { method: 'POST', body: { line1: line1 } });
      addressId = address.id;
    }

    for (const item of state.cart) {
      await apiFetch('/cart/items', { method: 'POST', body: { product_id: item.product_id, quantity: item.quantity } });
    }
    const order = await apiFetch('/orders', { method: 'POST', body: { order_type: orderType, address_id: addressId } });

    state.cart = [];
    updateCartBadge();
    document.getElementById('cart-modal').classList.remove('active');
    showToast('Order ' + order.order_number + ' placed! Track it under "Track Orders".', 'success');
    switchTab('orders');
  } catch (e) {
    showToast(e.message, 'error');
  }
}

// --------------------------------------------------------- custom cakes
function renderCustomCakeTab(container) {
  container.innerHTML = '' +
    '<div class="section-card" style="max-width:640px; margin:0 auto 24px;">' +
      '<h2 style="margin-bottom:8px;">Custom Cake Request</h2>' +
      '<p style="color:var(--text-muted); margin-bottom:24px;">Submit your custom design and receive a price quotation from our head chef.</p>' +
      '<form onsubmit="handleCustomCakeSubmit(event)">' +
        '<div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">' +
          '<div class="form-group"><label class="form-label">Flavour</label><input id="cake-flavour" class="form-control" placeholder="e.g. Belgian Chocolate Fudge" required></div>' +
          '<div class="form-group"><label class="form-label">Size</label><input id="cake-size" class="form-control" placeholder="e.g. 2 lb, serves 10" required></div>' +
        '</div>' +
        '<div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">' +
          '<div class="form-group"><label class="form-label">Type / Occasion</label><input id="cake-type" class="form-control" placeholder="e.g. Birthday, Wedding"></div>' +
          '<div class="form-group"><label class="form-label">Cream</label><input id="cake-cream" class="form-control" placeholder="e.g. Whipped, Fondant"></div>' +
        '</div>' +
        '<div class="form-group"><label class="form-label">Theme / Event</label><input id="cake-theme" class="form-control" placeholder="e.g. 21st Birthday, Graduation"></div>' +
        '<div class="form-group"><label class="form-label">Message on Cake</label><input id="cake-message" class="form-control" placeholder="e.g. Happy Birthday Sarah!"></div>' +
        '<div class="form-group"><label class="form-label">Needed By Date</label><input id="cake-date" type="date" class="form-control" required></div>' +
        '<button type="submit" class="btn-primary" style="width:100%; justify-content:center; padding:14px;"><i class="fa-solid fa-paper-plane"></i> Submit Request for Quotation</button>' +
      '</form>' +
    '</div>' +
    '<div id="my-cake-requests"></div>';
  document.getElementById('cake-date').min = new Date(Date.now() + 86400000).toISOString().split('T')[0];
  loadMyCakeRequests();
}

async function loadMyCakeRequests() {
  const el = document.getElementById('my-cake-requests');
  if (!isLoggedIn()) { el.innerHTML = '<p style="text-align:center; color:var(--text-muted);">Sign in to see your past custom cake requests.</p>'; return; }
  try {
    const page = await apiFetch('/custom-cakes');
    if (!page.items.length) { el.innerHTML = ''; return; }
    el.innerHTML = '<h3 style="margin-bottom:12px;">Your Requests</h3>' + page.items.map(r => '' +
      '<div class="section-card" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">' +
        '<div><strong>' + escapeHtml(r.flavour) + '</strong> &middot; ' + escapeHtml(r.size) +
          '<div style="font-size:13px; color:var(--text-muted);">Needed by ' + r.requested_date + (r.quote_amount ? ' &middot; Quote: ' + money(r.quote_amount) : '') + '</div></div>' +
        '<div style="display:flex; align-items:center; gap:10px;">' +
          '<span class="status-badge status-' + r.status + '">' + r.status.replace('_', ' ') + '</span>' +
          (r.status === 'quoted' ? '<button class="btn-primary btn-sm" onclick="acceptCakeQuote(' + r.id + ')">Accept</button>' : '') +
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
    showToast('Request submitted! We will send you a quotation soon.', 'success');
    event.target.reset();
    loadMyCakeRequests();
  } catch (e) {
    showToast(e.message, 'error');
  }
}

async function acceptCakeQuote(id) {
  try { await apiFetch('/custom-cakes/' + id + '/accept', { method: 'PATCH' }); showToast('Quote accepted!', 'success'); loadMyCakeRequests(); }
  catch (e) { showToast(e.message, 'error'); }
}
async function cancelCakeRequest(id) {
  if (!confirm('Cancel this custom cake request?')) return;
  try { await apiFetch('/custom-cakes/' + id + '/cancel', { method: 'PATCH' }); showToast('Request cancelled.', 'info'); loadMyCakeRequests(); }
  catch (e) { showToast(e.message, 'error'); }
}

// ------------------------------------------------------------ track orders
async function renderOrdersView(container) {
  if (!isLoggedIn()) {
    container.innerHTML = '<div class="empty-state"><i class="fa-solid fa-lock"></i><p>Please sign in to see your orders.</p>' +
      '<button class="btn-primary" onclick="openAuthModal()" style="margin-top:12px;">Sign In</button></div>';
    return;
  }
  container.innerHTML = '<div style="margin-bottom:24px;"><h2>Track Your Bakery Orders</h2>' +
    '<p style="color:var(--text-muted);">Real-time status updates from kitchen to delivery</p></div>' +
    '<div id="orders-list"><p style="color:var(--text-muted);">Loading...</p></div>';

  try {
    const page = await apiFetch('/orders');
    const list = document.getElementById('orders-list');
    if (!page.items.length) {
      list.innerHTML = '<div class="empty-state"><i class="fa-solid fa-receipt"></i><p>You haven\'t placed any orders yet.</p>' +
        '<button class="btn-primary" onclick="switchTab(\'catalog\')" style="margin-top:12px;">Browse Catalog</button></div>';
      return;
    }
    const steps = ['PENDING', 'CONFIRMED', 'PREPARING', 'READY', 'DELIVERED'];
    list.innerHTML = page.items.map(o => {
      let idx = steps.indexOf(o.status);
      if (idx === -1 && o.status === 'PICKED_UP') idx = 4;
      const cancellable = ['PENDING', 'CONFIRMED'].indexOf(o.status) !== -1;
      const itemsText = o.items.map(i => i.quantity + 'x ' + escapeHtml(i.product_name)).join(', ');
      const progressBar = o.status !== 'CANCELLED'
        ? '<div style="display:flex; gap:8px;">' + steps.map((s, i) =>
            '<div style="flex:1; height:6px; background:' + (i <= idx ? 'var(--success)' : 'var(--border)') + '; border-radius:3px;"></div>').join('') + '</div>'
        : '';
      return '' +
        '<div class="section-card">' +
          '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; flex-wrap:wrap; gap:8px;">' +
            '<div><strong>Order #' + o.order_number + '</strong> <span style="color:var(--text-muted); font-size:13px;">(' + o.order_source + ')</span></div>' +
            '<span class="status-badge status-' + o.status + '">' + o.status.replace(/_/g, ' ') + '</span>' +
          '</div>' +
          '<div style="font-size:14px; color:var(--text-muted); margin-bottom:12px;">' + itemsText + ' &middot; Total: ' + money(o.total) +
            ' &middot; Payment: <span class="status-badge status-' + o.payment_status + '">' + o.payment_status + '</span></div>' +
          progressBar +
          (cancellable ? '<button class="btn-danger-sm" style="margin-top:12px;" onclick="cancelOrder(' + o.id + ')">Cancel Order</button>' : '') +
        '</div>';
    }).join('');
  } catch (e) {
    document.getElementById('orders-list').innerHTML = '<p style="color:var(--danger);">' + e.message + '</p>';
  }
}

async function cancelOrder(id) {
  if (!confirm('Cancel this order?')) return;
  try {
    await apiFetch('/orders/' + id + '/cancel', { method: 'PATCH' });
    showToast('Order cancelled.', 'info');
    renderOrdersView(document.getElementById('main-content'));
  } catch (e) { showToast(e.message, 'error'); }
}

// ----------------------------------------------------------------- reviews
function renderReviewsTab(container) {
  const productOptions = state.products.map(p => '<option value="' + p.id + '">' + escapeHtml(p.name) + '</option>').join('');
  container.innerHTML = '' +
    '<div style="margin-bottom:24px;"><h2>Customer Reviews &amp; Feedback</h2><p style="color:var(--text-muted);">Reviews from customers who received their order</p></div>' +
    '<div class="section-card" style="margin-bottom:24px;">' +
      '<h3 style="margin-bottom:12px;">Leave a Review</h3>' +
      '<p style="font-size:13px; color:var(--text-muted); margin-bottom:12px;">You can review a product after it has been delivered or picked up.</p>' +
      '<form onsubmit="handleReviewSubmit(event)">' +
        '<div class="form-group"><label class="form-label">Product</label><select id="review-product" class="form-select" required>' + productOptions + '</select></div>' +
        '<div class="form-group"><label class="form-label">Rating</label><select id="review-rating" class="form-select">' +
          '<option value="5">5 - Excellent</option><option value="4">4 - Good</option><option value="3">3 - Okay</option>' +
          '<option value="2">2 - Poor</option><option value="1">1 - Bad</option></select></div>' +
        '<div class="form-group"><label class="form-label">Comment</label><input id="review-comment" class="form-control" placeholder="Share your experience..."></div>' +
        '<button type="submit" class="btn-primary">Submit Review</button>' +
      '</form>' +
    '</div>' +
    '<div id="product-reviews-list"><p style="color:var(--text-muted);">Loading reviews...</p></div>';
  loadProductReviews();
}

async function loadProductReviews() {
  const el = document.getElementById('product-reviews-list');
  if (!state.products.length) { el.innerHTML = ''; return; }
  try {
    const sample = state.products.slice(0, 6);
    const results = [];
    for (const p of sample) {
      try { results.push(await apiFetch('/reviews/product/' + p.id, { auth: false })); }
      catch (e) { /* skip product on error */ }
    }
    const withReviews = results.filter(r => r && r.items.length);
    if (!withReviews.length) { el.innerHTML = '<div class="empty-state"><i class="fa-solid fa-star"></i><p>No reviews yet. Be the first!</p></div>'; return; }
    let cards = [];
    withReviews.forEach(r => {
      r.items.forEach(i => {
        cards.push('<div class="section-card"><div style="color:var(--accent); margin-bottom:8px;">' +
          '★'.repeat(i.rating) + '☆'.repeat(5 - i.rating) + '</div>' +
          '<p style="font-style:italic; margin-bottom:12px;">"' + escapeHtml(i.comment || 'Great product!') + '"</p>' +
          '<div style="font-weight:700; font-size:14px;">&mdash; ' + escapeHtml(i.customer_name || 'Customer') + '</div></div>');
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
    showToast('Review submitted for moderation. Thank you!', 'success');
    event.target.reset();
    loadProductReviews();
  } catch (e) { showToast(e.message, 'error'); }
}

// =================================================================
//  ADMIN VIEWS
// =================================================================
async function renderAdminDashboard(container) {
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
  if (!isLoggedIn()) { showToast('Sign in with a cashier/staff account to complete a sale.', 'error'); openAuthModal(); return; }
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
