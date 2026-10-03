/* Freshco Bakers — Web Technologies Presentation Engine */

const API_BASE = 'http://localhost:8000/api/v1';

// Application State
let state = {
  currentRole: 'customer', // customer, admin, pos
  currentTab: 'home',
  currentUser: null,
  token: localStorage.getItem('access_token') || null,
  cart: [],
  products: [],
  categories: [],
  orders: [],
  cakes: [],
  reviews: [],
  staff: [],
  authMode: 'login' // login, register
};

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

async function initApp() {
  if (state.token) {
    await fetchCurrentUser();
  }
  await loadCatalogData();
  renderApp();
}

async function fetchCurrentUser() {
  try {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (res.ok) {
      state.currentUser = await res.json();
    } else {
      logout();
    }
  } catch (e) {
    console.log('Auth check error:', e);
  }
}

async function loadCatalogData() {
  try {
    const [prodRes, catRes] = await Promise.all([
      fetch(`${API_BASE}/products`),
      fetch(`${API_BASE}/categories`)
    ]);
    if (prodRes.ok) state.products = await prodRes.json();
    if (catRes.ok) state.categories = await catRes.json();
  } catch (e) {
    console.log('Catalog fetch error:', e);
    state.products = [
      { id: 1, name: 'Artisanal Sourdough Loaf', price: 450, sale_price: 400, description: 'Naturally fermented for 24h with a golden crust', category: 'Breads', sku: 'SD-01', stock: 15 },
      { id: 2, name: 'Belgian Chocolate Cake', price: 1800, sale_price: 1650, description: 'Layers of dark Belgian fudge and cocoa velvet', category: 'Cakes', sku: 'BCC-02', stock: 8 },
      { id: 3, name: 'Butter Croissant Pack (6)', price: 900, sale_price: null, description: 'Flaky 81-layer French butter croissants', category: 'Pastries', sku: 'BC-03', stock: 20 },
      { id: 4, name: 'Red Velvet Supreme', price: 2200, sale_price: 1950, description: 'Classic red velvet with vanilla cream cheese frost', category: 'Cakes', sku: 'RVS-04', stock: 5 }
    ];
  }
}

// Role Switcher
function switchRole(role) {
  state.currentRole = role;
  document.querySelectorAll('.role-btn').forEach(btn => btn.classList.remove('active'));
  document.getElementById(`btn-role-${role}`).classList.add('active');

  const customerNav = document.getElementById('customer-nav');
  const adminNav = document.getElementById('admin-nav');
  const cartBtn = document.getElementById('cart-btn');

  if (role === 'customer') {
    customerNav.style.display = 'block';
    adminNav.style.display = 'none';
    cartBtn.style.display = 'flex';
    state.currentTab = 'home';
  } else if (role === 'admin') {
    customerNav.style.display = 'none';
    adminNav.style.display = 'block';
    cartBtn.style.display = 'none';
    state.currentTab = 'overview';
  } else if (role === 'pos') {
    customerNav.style.display = 'none';
    adminNav.style.display = 'none';
    cartBtn.style.display = 'none';
    state.currentTab = 'pos';
  }

  renderApp();
}

function switchTab(tab) {
  state.currentTab = tab;
  document.querySelectorAll('#customer-nav .nav-link').forEach(l => l.classList.remove('active'));
  const activeLink = document.getElementById(`nav-${tab}`);
  if (activeLink) activeLink.classList.add('active');
  renderApp();
}

function switchAdminTab(tab) {
  state.currentTab = tab;
  document.querySelectorAll('#admin-nav .nav-link').forEach(l => l.classList.remove('active'));
  const activeLink = document.getElementById(`admin-nav-${tab}`);
  if (activeLink) activeLink.classList.add('active');
  renderApp();
}

// Render Core Router View
function renderApp() {
  const container = document.getElementById('main-content');
  updateUserUI();

  if (state.currentRole === 'customer') {
    if (state.currentTab === 'home') container.innerHTML = renderCustomerHome();
    else if (state.currentTab === 'catalog') container.innerHTML = renderCatalogView();
    else if (state.currentTab === 'cake') container.innerHTML = renderCustomCakeForm();
    else if (state.currentTab === 'orders') renderOrdersView(container);
    else if (state.currentTab === 'reviews') container.innerHTML = renderReviewsView();
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

// Customer Home View
function renderCustomerHome() {
  return `
    <div class="hero-section">
      <div>
        <h1 class="hero-title">Freshness Baked Daily in 3D Perspective</h1>
        <p class="hero-subtitle">Order hand-crafted artisan sourdoughs, gourmet cakes, and pastries warm to your doorstep.</p>
        <button class="btn-primary" onclick="switchTab('catalog')" style="padding:14px 28px; font-size:16px;">
          <i class="fa-solid fa-basket-shopping"></i> Explore Full Catalog
        </button>
      </div>
      <div style="text-align:center;">
        <div class="tilt-card" style="padding:24px; background:rgba(255,255,255,0.1); border-color:rgba(255,255,255,0.2); backdrop-filter:blur(10px);">
          <i class="fa-solid fa-cake-candles" style="font-size:72px; color:var(--accent); margin-bottom:16px;"></i>
          <h3 style="color:#fff; font-size:22px;">Custom Celebration Cakes</h3>
          <p style="color:rgba(255,255,255,0.7); margin:8px 0 16px;">Design your dream cake with real-time quote generation</p>
          <button class="btn-secondary" onclick="switchTab('cake')">Order Custom Cake</button>
        </div>
      </div>
    </div>

    <div style="margin-bottom:24px; display:flex; justify-content:space-between; align-items:center;">
      <h2>Featured Today</h2>
      <a href="#" onclick="switchTab('catalog')" style="color:var(--primary); font-weight:700; text-decoration:none;">View All (${state.products.length}) →</a>
    </div>

    <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:24px;">
      ${state.products.map(p => `
        <div class="tilt-card" data-tilt>
          <div class="product-badge">${p.category || 'Fresh'}</div>
          <div style="height:160px; background:linear-gradient(135deg, #FDFBF7, #E8DCCF); display:flex; align-items:center; justify-content:center;">
            <i class="fa-solid fa-wheat-awn" style="font-size:48px; color:var(--primary);"></i>
          </div>
          <div class="product-info">
            <h3 class="product-title">${p.name}</h3>
            <p class="product-desc">${p.description || 'Delicious freshly baked artisan item.'}</p>
            <div class="product-bottom">
              <div class="product-price">₨ ${p.sale_price || p.price} ${p.sale_price ? `<span style="text-decoration:line-through; color:#999; font-size:13px;">₨ ${p.price}</span>` : ''}</div>
              <button class="btn-primary" onclick="addToCart(${p.id})"><i class="fa-solid fa-cart-plus"></i> Add</button>
            </div>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

// Catalog View
function renderCatalogView() {
  return `
    <div style="margin-bottom:24px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:16px;">
      <div>
        <h2>Fresh Bakery Menu</h2>
        <p style="color:var(--text-muted);">Browse our complete selection of fresh breads, cakes & pastries</p>
      </div>
      <input type="text" id="catalog-search" class="form-control" placeholder="🔍 Search cakes, sourdough, croissants..." onkeyup="filterCatalog()" style="width:280px;">
    </div>
    <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:24px;" id="catalog-grid">
      ${state.products.map(p => `
        <div class="tilt-card" data-tilt>
          <div style="height:160px; background:linear-gradient(135deg, #FFFDF9, #F5E6D3); display:flex; align-items:center; justify-content:center;">
            <i class="fa-solid fa-cookie-bite" style="font-size:48px; color:var(--accent);"></i>
          </div>
          <div class="product-info">
            <h3 class="product-title">${p.name}</h3>
            <p class="product-desc">${p.description || 'Artisan preparation with 100% natural ingredients.'}</p>
            <div class="product-bottom">
              <div class="product-price">₨ ${p.sale_price || p.price}</div>
              <button class="btn-primary" onclick="addToCart(${p.id})"><i class="fa-solid fa-cart-plus"></i> Add</button>
            </div>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

// Custom Cake Form
function renderCustomCakeForm() {
  return `
    <div style="max-width:640px; margin:0 auto; background:var(--surface); padding:32px; border-radius:var(--radius-lg); border:1px solid var(--border); box-shadow:var(--shadow-md);">
      <h2 style="margin-bottom:8px;">Custom Cake Request</h2>
      <p style="color:var(--text-muted); margin-bottom:24px;">Submit your custom design and receive a price quotation from our head chef.</p>

      <form onsubmit="handleCustomCakeSubmit(event)">
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
          <div class="form-group">
            <label class="form-label">Flavor</label>
            <select id="cake-flavour" class="form-control">
              <option>Belgian Chocolate Fudge</option>
              <option>Red Velvet Vanilla</option>
              <option>Lotus Biscoff Crisp</option>
              <option>Mango Salted Caramel</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Size (Pounds)</label>
            <select id="cake-size" class="form-control">
              <option>2 Lbs (Serves 6-8)</option>
              <option>4 Lbs (Serves 12-15)</option>
              <option>6 Lbs Tiered (Serves 20+)</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Theme / Event</label>
          <input type="text" id="cake-theme" class="form-control" placeholder="e.g. 21st Birthday, Graduation, Wedding" required>
        </div>
        <div class="form-group">
          <label class="form-label">Custom Message on Cake</label>
          <input type="text" id="cake-message" class="form-control" placeholder="e.g. Happy Birthday Sarah!">
        </div>
        <button type="submit" class="btn-primary" style="width:100%; justify-content:center; padding:14px;">
          <i class="fa-solid fa-paper-plane"></i> Submit Cake Request for Quotation
        </button>
      </form>
    </div>
  `;
}

// Track Orders View
async function renderOrdersView(container) {
  container.innerHTML = `
    <div style="margin-bottom:24px;">
      <h2>Track Your Bakery Orders</h2>
      <p style="color:var(--text-muted);">Real-time status updates from kitchen to delivery</p>
    </div>
    <div id="orders-list">
      <div style="background:var(--surface); padding:24px; border-radius:var(--radius-md); border:1px solid var(--border); margin-bottom:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
          <div><strong>Order #FB-2026-8812</strong> <span style="color:var(--text-muted); font-size:13px;">(Web Checkout)</span></div>
          <span style="background:rgba(39, 174, 96, 0.15); color:var(--success); font-weight:700; padding:4px 12px; border-radius:12px; font-size:12px;">OUT FOR DELIVERY</span>
        </div>
        <div style="font-size:14px; color:var(--text-muted); margin-bottom:16px;">1x Belgian Chocolate Cake, 2x Sourdough Loaf · Total: Rs 2,450</div>
        <div style="display:flex; gap:8px; align-items:center;">
          <div style="flex:1; height:6px; background:var(--success); border-radius:3px;"></div>
          <div style="flex:1; height:6px; background:var(--success); border-radius:3px;"></div>
          <div style="flex:1; height:6px; background:var(--success); border-radius:3px;"></div>
          <div style="flex:1; height:6px; background:var(--success); border-radius:3px;"></div>
          <div style="flex:1; height:6px; background:var(--border); border-radius:3px;"></div>
        </div>
      </div>
    </div>
  `;
}

// Reviews View
function renderReviewsView() {
  return `
    <div style="margin-bottom:24px;">
      <h2>Customer Reviews & Feedback</h2>
      <p style="color:var(--text-muted);">Read what our community says about Freshco Bakers</p>
    </div>
    <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:20px;">
      <div style="background:var(--surface); padding:20px; border-radius:var(--radius-md); border:1px solid var(--border);">
        <div style="color:var(--accent); margin-bottom:8px;"><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i></div>
        <p style="font-style:italic; margin-bottom:12px;">"The Belgian Fudge cake was unbelievable! Freshly baked and delivered right on time."</p>
        <div style="font-weight:700; font-size:14px;">— Ayesha K.</div>
      </div>
      <div style="background:var(--surface); padding:20px; border-radius:var(--radius-md); border:1px solid var(--border);">
        <div style="color:var(--accent); margin-bottom:8px;"><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i></div>
        <p style="font-style:italic; margin-bottom:12px;">"Best sourdough in town! Amazing 3D ordering experience too."</p>
        <div style="font-weight:700; font-size:14px;">— Bilal R.</div>
      </div>
    </div>
  `;
}

// Admin Products Table
function renderAdminProducts(container) {
  container.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;">
      <h2>Products Catalog Management</h2>
      <button class="btn-primary" onclick="alert('Product Add Modal')"><i class="fa-solid fa-plus"></i> Add New Product</button>
    </div>
    <table style="width:100%; background:var(--surface); border-radius:var(--radius-md); border-collapse:collapse; border:1px solid var(--border);">
      <thead>
        <tr style="background:var(--bg-light); text-align:left; font-size:13px; color:var(--text-muted);">
          <th style="padding:14px;">SKU</th>
          <th style="padding:14px;">Product Name</th>
          <th style="padding:14px;">Category</th>
          <th style="padding:14px;">Price</th>
          <th style="padding:14px;">Stock</th>
          <th style="padding:14px;">Actions</th>
        </tr>
      </thead>
      <tbody>
        ${state.products.map(p => `
          <tr style="border-top:1px solid var(--border);">
            <td style="padding:14px; font-weight:700;">${p.sku || 'SKU-01'}</td>
            <td style="padding:14px;">${p.name}</td>
            <td style="padding:14px;">${p.category || 'General'}</td>
            <td style="padding:14px; font-weight:700;">Rs ${p.sale_price || p.price}</td>
            <td style="padding:14px;"><span style="background:rgba(39, 174, 96, 0.15); color:var(--success); padding:4px 8px; border-radius:6px; font-weight:700;">${p.stock || 12} in stock</span></td>
            <td style="padding:14px;"><button class="btn-secondary" style="padding:4px 10px;">Edit</button></td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

// Admin Kanban
function renderAdminKanban(container) {
  container.innerHTML = `
    <div style="margin-bottom:24px;">
      <h2>Kitchen Orders Kanban Board</h2>
      <p style="color:var(--text-muted);">Live order status workflow & fulfillment tracking</p>
    </div>
    <div class="kanban-board">
      <div class="kanban-col">
        <div class="kanban-header">PENDING (2)</div>
        <div class="order-card">
          <div style="font-weight:700; font-size:14px;">#FB-2026-9912</div>
          <div style="font-size:12px; color:var(--text-muted);">2x Red Velvet Cake</div>
          <div style="margin-top:8px; font-weight:800; color:var(--primary);">Rs 3,900</div>
        </div>
      </div>
      <div class="kanban-col">
        <div class="kanban-header">PREPARING (1)</div>
        <div class="order-card">
          <div style="font-weight:700; font-size:14px;">#FB-2026-9890</div>
          <div style="font-size:12px; color:var(--text-muted);">6x Butter Croissant</div>
          <div style="margin-top:8px; font-weight:800; color:var(--primary);">Rs 900</div>
        </div>
      </div>
      <div class="kanban-col">
        <div class="kanban-header">READY (1)</div>
        <div class="order-card">
          <div style="font-weight:700; font-size:14px;">#FB-2026-9877</div>
          <div style="font-size:12px; color:var(--text-muted);">1x Sourdough Loaf</div>
          <div style="margin-top:8px; font-weight:800; color:var(--primary);">Rs 400</div>
        </div>
      </div>
      <div class="kanban-col">
        <div class="kanban-header">DELIVERED / COMPLETED</div>
        <div class="order-card" style="opacity:0.75;">
          <div style="font-weight:700; font-size:14px;">#FB-2026-9801</div>
          <div style="font-size:12px; color:var(--text-muted);">POS Counter Sale</div>
          <div style="margin-top:8px; font-weight:800; color:var(--success);">Paid Rs 1,650</div>
        </div>
      </div>
    </div>
  `;
}

function renderAdminInventory(c) {
  c.innerHTML = `<h2>Inventory Management</h2><p style="color:var(--text-muted);">Branch-level stock logs & transfer rules per SRS Section 10</p>`;
}

function renderAdminCakeQuotes(c) {
  c.innerHTML = `<h2>Custom Cake Quotes</h2><p style="color:var(--text-muted);">Review customer designs, calculate costs & issue binding price quotes</p>`;
}

function renderAdminStaff(c) {
  c.innerHTML = `<h2>Staff & Employee Permissions</h2><p style="color:var(--text-muted);">Manage Cashier, Manager, Admin, and Owner accounts & audit logs</p>`;
}

function renderAdminSettings(c) {
  c.innerHTML = `<h2>Bakery Store Settings</h2><p style="color:var(--text-muted);">Configure bakery information, flat delivery fee, tax rate, and notification toggles</p>`;
}

// Add to Cart
function addToCart(productId) {
  const prod = state.products.find(p => p.id === productId);
  if (!prod) return;

  const existing = state.cart.find(i => i.product_id === productId);
  if (existing) {
    existing.quantity += 1;
  } else {
    state.cart.push({ product_id: productId, name: prod.name, price: prod.sale_price || prod.price, quantity: 1 });
  }

  updateCartBadge();
}

function updateCartBadge() {
  const count = state.cart.reduce((sum, item) => sum + item.quantity, 0);
  document.getElementById('cart-count').innerText = count;
}

// Admin Dashboard View
async function renderAdminDashboard(container) {
  container.innerHTML = `
    <div style="margin-bottom:24px;">
      <h2>Executive Analytics Dashboard</h2>
      <p style="color:var(--text-muted);">Real-time financial, sales channels, & operational performance metrics</p>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(39, 174, 96, 0.15); color:var(--success);"><i class="fa-solid fa-coins"></i></div>
        <div><div class="stat-val" id="stat-revenue">Rs 142,500</div><div class="stat-lbl">Total Gross Revenue</div></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(230, 126, 34, 0.15); color:var(--accent);"><i class="fa-solid fa-receipt"></i></div>
        <div><div class="stat-val" id="stat-orders">84</div><div class="stat-lbl">Orders Fulfilled</div></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(241, 196, 15, 0.15); color:#D4AC0D;"><i class="fa-solid fa-clock"></i></div>
        <div><div class="stat-val" id="stat-pending">3</div><div class="stat-lbl">Pending Kitchen Orders</div></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(231, 76, 60, 0.15); color:var(--danger);"><i class="fa-solid fa-triangle-exclamation"></i></div>
        <div><div class="stat-val" id="stat-lowstock">2</div><div class="stat-lbl">Low Stock Alerts</div></div>
      </div>
    </div>
  `;

  try {
    const res = await fetch(`${API_BASE}/analytics/dashboard`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (res.ok) {
      const data = await res.json();
      document.getElementById('stat-revenue').innerText = `Rs ${data.revenue.toLocaleString()}`;
      document.getElementById('stat-orders').innerText = data.total_orders;
      document.getElementById('stat-pending').innerText = data.pending_orders;
      document.getElementById('stat-lowstock').innerText = data.low_stock_count;
    }
  } catch (e) {
    console.log('Analytics load error:', e);
  }
}

// POS View
function renderPOSView(container) {
  container.innerHTML = `
    <div style="display:grid; grid-template-columns: 2fr 1fr; gap:24px;">
      <div>
        <div style="display:flex; gap:12px; margin-bottom:20px;">
          <input type="text" id="pos-barcode" class="form-control" placeholder="Scan Barcode (e.g. 890123456 or SKU)..." autofocus onkeypress="if(event.key==='Enter') handlePOSBarcodeScan()">
          <button class="btn-primary" onclick="handlePOSBarcodeScan()"><i class="fa-solid fa-barcode"></i> Scan</button>
        </div>

        <h3 style="margin-bottom:16px;">Quick Items</h3>
        <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(180px, 1fr)); gap:16px;">
          ${state.products.map(p => `
            <div class="tilt-card" onclick="addToPOSCart(${p.id})" style="cursor:pointer; padding:16px; text-align:center;">
              <i class="fa-solid fa-cookie" style="font-size:32px; color:var(--primary); margin-bottom:8px;"></i>
              <div style="font-weight:700; font-size:15px;">${p.name}</div>
              <div style="color:var(--accent); font-weight:800; margin-top:4px;">Rs ${p.sale_price || p.price}</div>
            </div>
          `).join('')}
        </div>
      </div>

      <div style="background:var(--surface); padding:24px; border-radius:var(--radius-lg); border:1px solid var(--border); box-shadow:var(--shadow-md);">
        <h3 style="margin-bottom:16px;"><i class="fa-solid fa-cash-register"></i> Counter Order Cart</h3>
        <div id="pos-cart-list" style="min-height:200px; max-height:320px; overflow-y:auto; margin-bottom:20px;">
          <p style="color:var(--text-muted); text-align:center; margin-top:40px;">No items scanned</p>
        </div>

        <div class="form-group">
          <label class="form-label">Payment Method</label>
          <select id="pos-pay-method" class="form-control">
            <option value="CASH">Cash Counter</option>
            <option value="CARD">Card POS Reader</option>
            <option value="WALLET">JazzCash / EasyPaisa</option>
          </select>
        </div>

        <button class="btn-primary" onclick="completePOSSale()" style="width:100%; justify-content:center; padding:16px; font-size:16px;">
          <i class="fa-solid fa-check-double"></i> Complete Sale & Print Receipt
        </button>
      </div>
    </div>
  `;
}

let posCart = [];

function addToPOSCart(productId) {
  const prod = state.products.find(p => p.id === productId);
  if (!prod) return;

  const existing = posCart.find(i => i.product_id === productId);
  if (existing) {
    existing.quantity += 1;
  } else {
    posCart.push({ product_id: productId, name: prod.name, price: prod.sale_price || prod.price, quantity: 1 });
  }
  renderPOSCartList();
}

function renderPOSCartList() {
  const list = document.getElementById('pos-cart-list');
  if (!list) return;
  if (posCart.length === 0) {
    list.innerHTML = '<p style="color:var(--text-muted); text-align:center; margin-top:40px;">No items scanned</p>';
    return;
  }

  let total = 0;
  list.innerHTML = posCart.map(item => {
    const itemTotal = item.price * item.quantity;
    total += itemTotal;
    return `
      <div style="display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid var(--border);">
        <div>
          <div style="font-weight:700;">${item.name}</div>
          <div style="font-size:12px; color:var(--text-muted);">${item.quantity} x Rs ${item.price}</div>
        </div>
        <div style="font-weight:800;">Rs ${itemTotal}</div>
      </div>
    `;
  }).join('') + `
    <div style="display:flex; justify-content:space-between; margin-top:16px; font-size:18px; font-weight:800;">
      <span>Total:</span>
      <span style="color:var(--primary);">Rs ${total}</span>
    </div>
  `;
}

async function completePOSSale() {
  if (posCart.length === 0) {
    alert('Cart is empty!');
    return;
  }

  const payload = {
    items: posCart.map(i => ({ product_id: i.product_id, quantity: i.quantity })),
    payment_method: document.getElementById('pos-pay-method').value,
    amount_paid: posCart.reduce((sum, i) => sum + (i.price * i.quantity), 0)
  };

  try {
    const res = await fetch(`${API_BASE}/pos/sales`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
      },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      const order = await res.json();
      openThermalReceiptModal(order);
      posCart = [];
      renderPOSCartList();
    } else {
      openThermalReceiptModal({ order_number: 'POS-2026-9921', total: payload.amount_paid, items: posCart });
      posCart = [];
      renderPOSCartList();
    }
  } catch (e) {
    openThermalReceiptModal({ order_number: 'POS-2026-9921', total: payload.amount_paid, items: posCart });
    posCart = [];
    renderPOSCartList();
  }
}

function openThermalReceiptModal(order) {
  const modal = document.getElementById('receipt-modal');
  const content = document.getElementById('thermal-receipt-content');

  content.innerHTML = `
    <div style="text-align:center;">
      <h2 style="font-size:20px; font-weight:800;">FRESHCO BAKERS</h2>
      <p style="font-size:12px;">Freshness Baked Daily</p>
      <p style="font-size:11px; margin-top:4px;">Receipt #${order.order_number || 'POS-8821'}</p>
    </div>
    <div class="thermal-line"></div>
    ${(order.items || posCart).map(i => `
      <div style="display:flex; justify-content:space-between; font-size:12px;">
        <span>${i.product_name || i.name} x${i.quantity}</span>
        <span>Rs ${i.total || (i.price * i.quantity)}</span>
      </div>
    `).join('')}
    <div class="thermal-line"></div>
    <div style="display:flex; justify-content:space-between; font-weight:800; font-size:14px;">
      <span>TOTAL PAID:</span>
      <span>Rs ${order.total || 0}</span>
    </div>
    <div style="text-align:center; font-size:11px; margin-top:12px;">
      Thank you for visiting Freshco Bakers!
    </div>
  `;

  modal.classList.add('active');
}

function closeReceiptModal() {
  document.getElementById('receipt-modal').classList.remove('active');
}

// 3D Tilt Cards Movement Engine
function attach3DTiltListeners() {
  const cards = document.querySelectorAll('.tilt-card');
  cards.forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      const rotateX = -y / 10;
      const rotateY = x / 10;
      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.02)`;
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) scale(1)`;
    });
  });
}

// User Auth Modal Functions
function openAuthModal() {
  document.getElementById('auth-modal').classList.add('active');
}

function closeAuthModal() {
  document.getElementById('auth-modal').classList.remove('active');
}

function toggleAuthMode() {
  state.authMode = state.authMode === 'login' ? 'register' : 'login';
  document.getElementById('auth-modal-title').innerText = state.authMode === 'login' ? 'Sign In to Freshco' : 'Create Customer Account';
  document.getElementById('group-name').style.display = state.authMode === 'register' ? 'block' : 'none';
  document.getElementById('auth-submit-btn').innerText = state.authMode === 'login' ? 'Sign In' : 'Register Account';
}

function updateUserUI() {
  const btnText = document.getElementById('user-btn-text');
  if (btnText) {
    if (state.currentUser) {
      btnText.innerText = state.currentUser.name;
    } else {
      btnText.innerText = 'Sign In';
    }
  }
}
