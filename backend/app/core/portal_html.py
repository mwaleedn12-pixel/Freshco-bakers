"""
Developer & Operations Dashboard for Freshco Bakers API.
Provides an interactive management interface, live API tester, module catalog,
telemetry stats, and seed controls.
"""

def get_developer_portal_html(app_name: str = "Freshco Bakers", version: str = "1.0.0", env: str = "development") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{app_name} — Backend Control Hub</title>
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🥐</text></svg>">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-base: #090d16;
      --bg-surface: #0f172a;
      --bg-card: rgba(17, 26, 46, 0.75);
      --bg-card-hover: rgba(24, 37, 66, 0.9);
      --border: rgba(255, 255, 255, 0.08);
      --border-accent: rgba(245, 158, 11, 0.3);
      --amber: #f59e0b;
      --amber-glow: rgba(245, 158, 11, 0.2);
      --amber-dark: #d97706;
      --emerald: #10b981;
      --emerald-glow: rgba(16, 185, 129, 0.2);
      --sky: #38bdf8;
      --indigo: #6366f1;
      --rose: #f43f5e;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
      --radius: 14px;
      --font: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      --mono: 'JetBrains Mono', monospace;
    }}

    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    body {{
      background: radial-gradient(circle at 10% 20%, rgba(245, 158, 11, 0.07) 0%, transparent 40%),
                  radial-gradient(circle at 90% 80%, rgba(99, 102, 241, 0.06) 0%, transparent 40%),
                  var(--bg-base);
      color: var(--text-main);
      font-family: var(--font);
      min-height: 100vh;
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
    }}

    /* Container */
    .container {{
      max-width: 1400px;
      margin: 0 auto;
      padding: 24px 28px;
    }}

    /* Top Bar */
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 24px;
      background: var(--bg-card);
      backdrop-filter: blur(16px);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      margin-bottom: 28px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }}

    .brand {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}

    .brand-icon {{
      width: 44px;
      height: 44px;
      background: linear-gradient(135deg, #f59e0b, #b45309);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      box-shadow: 0 0 20px var(--amber-glow);
    }}

    .brand-info h1 {{
      font-size: 20px;
      font-weight: 700;
      letter-spacing: -0.02em;
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .brand-info p {{
      font-size: 13px;
      color: var(--text-muted);
    }}

    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 600;
      letter-spacing: 0.02em;
    }}

    .badge-live {{
      background: rgba(16, 185, 129, 0.12);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }}

    .badge-env {{
      background: rgba(245, 158, 11, 0.12);
      color: #fbbf24;
      border: 1px solid rgba(245, 158, 11, 0.3);
      text-transform: uppercase;
    }}

    .pulse-dot {{
      width: 8px;
      height: 8px;
      background: #10b981;
      border-radius: 50%;
      box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
      animation: pulse 2s infinite;
    }}

    @keyframes pulse {{
      0% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }}
      70% {{ box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }}
      100% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }}
    }}

    .header-actions {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 9px 16px;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 600;
      text-decoration: none;
      cursor: pointer;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      border: 1px solid transparent;
      font-family: inherit;
    }}

    .btn-primary {{
      background: linear-gradient(135deg, #f59e0b, #d97706);
      color: #0b0f19;
      box-shadow: 0 4px 14px var(--amber-glow);
    }}

    .btn-primary:hover {{
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(245, 158, 11, 0.4);
    }}

    .btn-secondary {{
      background: rgba(255, 255, 255, 0.05);
      color: var(--text-main);
      border: 1px solid var(--border);
    }}

    .btn-secondary:hover {{
      background: rgba(255, 255, 255, 0.1);
      border-color: rgba(255, 255, 255, 0.2);
      transform: translateY(-1px);
    }}

    .btn-scalar {{
      background: linear-gradient(135deg, #4f46e5, #4338ca);
      color: #fff;
    }}

    .btn-scalar:hover {{
      transform: translateY(-2px);
      box-shadow: 0 6px 18px rgba(79, 70, 229, 0.4);
    }}

    /* Metrics Grid */
    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 18px;
      margin-bottom: 28px;
    }}

    .metric-card {{
      background: var(--bg-card);
      backdrop-filter: blur(12px);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 20px;
      position: relative;
      overflow: hidden;
      transition: all 0.25s ease;
    }}

    .metric-card:hover {{
      border-color: var(--border-accent);
      transform: translateY(-3px);
      box-shadow: 0 12px 28px rgba(0, 0, 0, 0.3);
    }}

    .metric-icon {{
      font-size: 24px;
      margin-bottom: 12px;
      display: inline-block;
    }}

    .metric-title {{
      font-size: 13px;
      color: var(--text-muted);
      font-weight: 500;
      margin-bottom: 4px;
    }}

    .metric-value {{
      font-size: 26px;
      font-weight: 800;
      color: var(--text-main);
      letter-spacing: -0.02em;
    }}

    .metric-sub {{
      font-size: 12px;
      color: var(--emerald);
      margin-top: 6px;
      display: flex;
      align-items: center;
      gap: 4px;
    }}

    /* Layout Columns */
    .main-grid {{
      display: grid;
      grid-template-columns: 1fr 420px;
      gap: 28px;
    }}

    @media (max-width: 1024px) {{
      .main-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    /* Section Cards */
    .section-card {{
      background: var(--bg-card);
      backdrop-filter: blur(12px);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 24px;
      margin-bottom: 24px;
    }}

    .section-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }}

    .section-header h2 {{
      font-size: 17px;
      font-weight: 700;
      letter-spacing: -0.01em;
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    /* Playground / Console */
    .console-form {{
      display: flex;
      flex-direction: column;
      gap: 14px;
    }}

    .input-row {{
      display: flex;
      gap: 10px;
    }}

    select, input, textarea {{
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid var(--border);
      color: var(--text-main);
      border-radius: 10px;
      padding: 10px 14px;
      font-family: inherit;
      font-size: 13px;
      outline: none;
      transition: all 0.2s ease;
    }}

    select:focus, input:focus, textarea:focus {{
      border-color: var(--amber);
      box-shadow: 0 0 0 2px var(--amber-glow);
    }}

    .method-select {{
      font-weight: 700;
      min-width: 110px;
    }}

    .endpoint-input {{
      flex: 1;
      font-family: var(--mono);
      font-size: 13px;
    }}

    .quick-chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 8px;
    }}

    .chip {{
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 5px 10px;
      border-radius: 8px;
      font-size: 11px;
      font-family: var(--mono);
      cursor: pointer;
      transition: all 0.2s;
    }}

    .chip:hover {{
      background: rgba(245, 158, 11, 0.15);
      color: var(--amber);
      border-color: var(--border-accent);
    }}

    .token-row {{
      display: flex;
      gap: 10px;
      align-items: center;
    }}

    .token-input {{
      flex: 1;
      font-family: var(--mono);
      font-size: 12px;
    }}

    .body-textarea {{
      width: 100%;
      height: 90px;
      font-family: var(--mono);
      font-size: 12px;
      resize: vertical;
      display: none;
    }}

    /* Response Box */
    .response-box {{
      margin-top: 16px;
      background: #060910;
      border: 1px solid var(--border);
      border-radius: 10px;
      overflow: hidden;
    }}

    .response-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 14px;
      background: rgba(255, 255, 255, 0.03);
      border-bottom: 1px solid var(--border);
      font-size: 12px;
      color: var(--text-muted);
      font-family: var(--mono);
    }}

    .res-status {{
      font-weight: 700;
    }}

    .res-status.status-200 {{ color: var(--emerald); }}
    .res-status.status-400 {{ color: var(--rose); }}
    .res-status.status-401 {{ color: #fb923c; }}

    pre.res-body {{
      padding: 14px;
      font-family: var(--mono);
      font-size: 12px;
      color: #e2e8f0;
      overflow-x: auto;
      max-height: 340px;
      line-height: 1.6;
    }}

    /* Modules Directory Grid */
    .modules-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 12px;
    }}

    .module-item {{
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 14px;
      transition: all 0.2s ease;
      cursor: pointer;
    }}

    .module-item:hover {{
      background: rgba(255, 255, 255, 0.05);
      border-color: rgba(245, 158, 11, 0.4);
      transform: translateY(-2px);
    }}

    .module-item-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 6px;
    }}

    .module-name {{
      font-size: 14px;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .module-path {{
      font-family: var(--mono);
      font-size: 11px;
      color: var(--text-dim);
      margin-bottom: 4px;
    }}

    .module-desc {{
      font-size: 12px;
      color: var(--text-muted);
      line-height: 1.4;
    }}

    .method-pill {{
      display: inline-block;
      font-size: 9px;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
      margin-right: 4px;
      font-family: var(--mono);
    }}

    .method-get {{ background: rgba(16, 185, 129, 0.2); color: #34d399; }}
    .method-post {{ background: rgba(59, 130, 246, 0.2); color: #60a5fa; }}
    .method-patch {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; }}
    .method-delete {{ background: rgba(244, 63, 94, 0.2); color: #fb7185; }}

    /* Credentials Card */
    .cred-item {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 12px;
      border-radius: 8px;
      background: rgba(15, 23, 42, 0.6);
      margin-bottom: 8px;
      border: 1px solid var(--border);
    }}

    .cred-role {{
      font-size: 12px;
      font-weight: 700;
      color: var(--amber);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    .cred-email {{
      font-family: var(--mono);
      font-size: 12px;
      color: var(--text-main);
    }}

    .copy-btn {{
      background: none;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      font-size: 13px;
      padding: 4px;
      border-radius: 4px;
      transition: color 0.15s;
    }}

    .copy-btn:hover {{
      color: var(--text-main);
    }}

    /* Toast */
    #toast {{
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: var(--bg-surface);
      border: 1px solid var(--emerald);
      color: #34d399;
      padding: 12px 20px;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 600;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
      display: none;
      z-index: 999;
      animation: fadeIn 0.3s ease;
    }}

    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(10px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <!-- Top Header -->
    <header>
      <div class="brand">
        <div class="brand-icon">🥐</div>
        <div class="brand-info">
          <h1>
            {app_name}
            <span class="badge badge-live"><span class="pulse-dot"></span> LIVE ENGINE</span>
            <span class="badge badge-env">{env}</span>
          </h1>
          <p>Artisan Bakery Enterprise Engine • FastAPI • PostgreSQL Central Architecture</p>
        </div>
      </div>
      <div class="header-actions">
        <button id="seedBtn" class="btn btn-secondary" onclick="seedDemoData()">🌱 Seed Demo Data</button>
        <a href="/api/v1/docs" class="btn btn-primary" target="_blank">📖 Swagger UI</a>
        <a href="/scalar" class="btn btn-scalar" target="_blank">⚡ Scalar API Docs</a>
        <a href="/api/v1/redoc" class="btn btn-secondary" target="_blank">📄 ReDoc</a>
      </div>
    </header>

    <!-- Metrics Row -->
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-icon">⚡</div>
        <div class="metric-title">Backend Architecture</div>
        <div class="metric-value">FastAPI 0.115</div>
        <div class="metric-sub">✓ Asynchronous ASGI • Python 3.12</div>
      </div>
      <div class="metric-card">
        <div class="metric-icon">🥐</div>
        <div class="metric-title">Bakery Catalog & Inventory</div>
        <div id="statProducts" class="metric-value">5 Categories</div>
        <div class="metric-sub">✓ Multi-branch Stock Control</div>
      </div>
      <div class="metric-card">
        <div class="metric-icon">📦</div>
        <div class="metric-title">Orders & POS Engine</div>
        <div id="statOrders" class="metric-value">Omnichannel</div>
        <div class="metric-sub">✓ Web, Mobile & Cashier POS</div>
      </div>
      <div class="metric-card">
        <div class="metric-icon">🛡️</div>
        <div class="metric-title">Security & Rate Limiting</div>
        <div class="metric-value">120 req / min</div>
        <div class="metric-sub">✓ Argon2id • HS256 JWT • OWASP</div>
      </div>
    </div>

    <!-- Main Grid -->
    <div class="main-grid">
      <!-- Left Column: Interactive Console & Modules -->
      <div>
        <!-- Interactive Live API Console -->
        <div class="section-card">
          <div class="section-header">
            <h2>💻 Interactive API Test Console</h2>
            <span style="font-size: 12px; color: var(--text-muted);">Execute live requests directly</span>
          </div>

          <!-- Quick Chips -->
          <div class="quick-chips">
            <span class="chip" onclick="setPreset('GET', '/api/v1/health')">Health Check</span>
            <span class="chip" onclick="setPreset('GET', '/api/v1/system/stats')">System Stats</span>
            <span class="chip" onclick="setPreset('GET', '/api/v1/categories')">All Categories</span>
            <span class="chip" onclick="setPreset('GET', '/api/v1/products')">Products List</span>
            <span class="chip" onclick="setPreset('GET', '/api/v1/branches')">Bakery Branches</span>
            <span class="chip" onclick="setPreset('GET', '/api/v1/coupons')">Active Coupons</span>
            <span class="chip" onclick="setPreset('POST', '/api/v1/auth/login', '{{\\n  \\"email\\": \\"admin@freshco.com\\",\\n  \\"password\\": \\"password123\\"\\n}}')">Login (Admin)</span>
          </div>

          <div class="console-form">
            <div class="input-row">
              <select id="httpMethod" class="method-select" onchange="toggleBodyInput()">
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PATCH">PATCH</option>
                <option value="DELETE">DELETE</option>
              </select>
              <input type="text" id="apiEndpoint" class="endpoint-input" value="/api/v1/health" placeholder="/api/v1/...">
              <button class="btn btn-primary" id="sendBtn" onclick="runConsoleRequest()">Send Request</button>
            </div>

            <div class="token-row">
              <input type="text" id="authToken" class="token-input" placeholder="Bearer JWT Token (Optional for protected routes)...">
              <button class="btn btn-secondary" style="white-space: nowrap;" onclick="autoLoginAdmin()">🔑 Get Admin Token</button>
            </div>

            <textarea id="reqBody" class="body-textarea" placeholder="JSON Request Payload..."></textarea>
          </div>

          <!-- Response Box -->
          <div class="response-box" id="resBox" style="display: none;">
            <div class="response-header">
              <span>Status: <span id="resStatus" class="res-status">200 OK</span></span>
              <span id="resTime">12ms</span>
              <button class="copy-btn" onclick="copyResponse()">📋 Copy JSON</button>
            </div>
            <pre class="res-body" id="resBody">Loading...</pre>
          </div>
        </div>

        <!-- Modules Directory -->
        <div class="section-card">
          <div class="section-header">
            <h2>📦 API Modules Architecture (22 Connected Services)</h2>
            <input type="text" id="modSearch" placeholder="Filter module..." oninput="filterModules()" style="padding: 6px 12px; font-size: 12px; width: 180px;">
          </div>

          <div class="modules-grid" id="modulesGrid">
            <!-- Auth -->
            <div class="module-item" onclick="setPreset('POST', '/api/v1/auth/login', '{{\\n  \\"email\\": \\"admin@freshco.com\\",\\n  \\"password\\": \\"password123\\"\\n}}')">
              <div class="module-item-header">
                <div class="module-name">🔐 Auth & JWT</div>
                <div><span class="method-pill method-post">POST</span></div>
              </div>
              <div class="module-path">/api/v1/auth</div>
              <div class="module-desc">Argon2id passwords, access tokens, role validation, /me profile.</div>
            </div>

            <!-- Categories -->
            <div class="module-item" onclick="setPreset('GET', '/api/v1/categories')">
              <div class="module-item-header">
                <div class="module-name">🍰 Categories</div>
                <div><span class="method-pill method-get">GET</span><span class="method-pill method-post">POST</span></div>
              </div>
              <div class="module-path">/api/v1/categories</div>
              <div class="module-desc">Breads, Celebration Cakes, French Pastries, Cookies, Savory.</div>
            </div>

            <!-- Products -->
            <div class="module-item" onclick="setPreset('GET', '/api/v1/products')">
              <div class="module-item-header">
                <div class="module-name">🥐 Products Catalog</div>
                <div><span class="method-pill method-get">GET</span><span class="method-pill method-post">POST</span></div>
              </div>
              <div class="module-path">/api/v1/products</div>
              <div class="module-desc">Artisan bakes, SKUs, barcodes, nutritional tags, pricing.</div>
            </div>

            <!-- Orders -->
            <div class="module-item" onclick="setPreset('GET', '/api/v1/orders/admin/list')">
              <div class="module-item-header">
                <div class="module-name">📦 Orders Pipeline</div>
                <div><span class="method-pill method-get">GET</span><span class="method-pill method-post">POST</span><span class="method-pill method-patch">PATCH</span></div>
              </div>
              <div class="module-path">/api/v1/orders</div>
              <div class="module-desc">Dine-in, takeaway, delivery, status progression & order tracking.</div>
            </div>

            <!-- Custom Cakes -->
            <div class="module-item" onclick="setPreset('GET', '/api/v1/custom-cakes/admin/list')">
              <div class="module-item-header">
                <div class="module-name">🎂 Custom Cake Studio</div>
                <div><span class="method-pill method-get">GET</span><span class="method-pill method-post">POST</span></div>
              </div>
              <div class="module-path">/api/v1/custom-cakes</div>
              <div class="module-desc">Tiered cakes, flavors, reference images, quotes & deposits.</div>
            </div>

            <!-- Multi Branch -->
            <div class="module-item" onclick="setPreset('GET', '/api/v1/branches')">
              <div class="module-item-header">
                <div class="module-name">🏬 Multi-Branch</div>
                <div><span class="method-pill method-get">GET</span></div>
              </div>
              <div class="module-path">/api/v1/branches</div>
              <div class="module-desc">Central Gulberg Bakery, DHA Phase 5 outlet, location routing.</div>
            </div>

            <!-- Inventory -->
            <div class="module-item" onclick="setPreset('GET', '/api/v1/inventory/branch/1')">
              <div class="module-item-header">
                <div class="module-name">📊 Stock & Inventory</div>
                <div><span class="method-pill method-get">GET</span><span class="method-pill method-post">POST</span></div>
              </div>
              <div class="module-path">/api/v1/inventory</div>
              <div class="module-desc">Real-time branch inventory levels, restock alerts, audit trail.</div>
            </div>

            <!-- POS -->
            <div class="module-item" onclick="setPreset('GET', '/api/v1/pos/branches')">
              <div class="module-item-header">
                <div class="module-name">🖥️ Point of Sale (POS)</div>
                <div><span class="method-pill method-get">GET</span><span class="method-pill method-post">POST</span></div>
              </div>
              <div class="module-path">/api/v1/pos</div>
              <div class="module-desc">High-speed register sales, cash/card splits, instant receipts.</div>
            </div>

            <!-- Payments -->
            <div class="module-item" onclick="setPreset('GET', '/api/v1/payments/receipt/1')">
              <div class="module-item-header">
                <div class="module-name">💳 Payments & Receipts</div>
                <div><span class="method-pill method-get">GET</span><span class="method-pill method-post">POST</span></div>
              </div>
              <div class="module-path">/api/v1/payments</div>
              <div class="module-desc">Cash on delivery, Card terminal, Bank transfer verification.</div>
            </div>

            <!-- Coupons -->
            <div class="module-item" onclick="setPreset('GET', '/api/v1/coupons')">
              <div class="module-item-header">
                <div class="module-name">🎟️ Coupons & Discounts</div>
                <div><span class="method-pill method-get">GET</span><span class="method-pill method-post">POST</span></div>
              </div>
              <div class="module-path">/api/v1/coupons</div>
              <div class="module-desc">Percentage & flat discounts, minimum cart values, validity limits.</div>
            </div>

            <!-- Reviews -->
            <div class="module-item" onclick="setPreset('GET', '/api/v1/reviews/product/1')">
              <div class="module-item-header">
                <div class="module-name">⭐ Reviews & Ratings</div>
                <div><span class="method-pill method-get">GET</span><span class="method-pill method-post">POST</span></div>
              </div>
              <div class="module-path">/api/v1/reviews</div>
              <div class="module-desc">Verified buyer reviews, 1-5 star ratings, admin moderation.</div>
            </div>

            <!-- Analytics -->
            <div class="module-item" onclick="setPreset('GET', '/api/v1/analytics/summary')">
              <div class="module-item-header">
                <div class="module-name">📈 Real-time Analytics</div>
                <div><span class="method-pill method-get">GET</span></div>
              </div>
              <div class="module-path">/api/v1/analytics</div>
              <div class="module-desc">Daily revenue, top-selling bakes, average order value.</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Telemetry & Credentials -->
      <div>
        <!-- System Diagnostics Card -->
        <div class="section-card">
          <div class="section-header">
            <h2>🩺 System Diagnostics</h2>
            <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 11px;" onclick="refreshStats()">Refresh</button>
          </div>
          <div style="font-size: 13px; display: flex; flex-direction: column; gap: 10px;">
            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border); padding-bottom: 6px;">
              <span style="color: var(--text-muted);">Database:</span>
              <span id="diagDb" style="color: var(--emerald); font-weight: 600;">PostgreSQL (Ready)</span>
            </div>
            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border); padding-bottom: 6px;">
              <span style="color: var(--text-muted);">Environment:</span>
              <span style="color: var(--amber); font-weight: 600;">{env}</span>
            </div>
            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border); padding-bottom: 6px;">
              <span style="color: var(--text-muted);">API Base URL:</span>
              <span style="font-family: var(--mono); color: var(--sky);">/api/v1</span>
            </div>
            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border); padding-bottom: 6px;">
              <span style="color: var(--text-muted);">Rate Limiter:</span>
              <span style="color: var(--emerald);">Active (Sliding Window)</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding-bottom: 6px;">
              <span style="color: var(--text-muted);">n8n Automations:</span>
              <span style="color: var(--indigo); font-weight: 600;">WhatsApp Webhook Ready</span>
            </div>
          </div>
        </div>

        <!-- Quick Demo Accounts -->
        <div class="section-card">
          <div class="section-header">
            <h2>🔑 Demo Credentials</h2>
            <span style="font-size: 11px; color: var(--text-muted);">Password: password123</span>
          </div>

          <div class="cred-item">
            <div>
              <div class="cred-role">Owner / Executive</div>
              <div class="cred-email">owner@freshco.com</div>
            </div>
            <button class="copy-btn" onclick="copyText('owner@freshco.com')">Copy</button>
          </div>

          <div class="cred-item">
            <div>
              <div class="cred-role">System Admin</div>
              <div class="cred-email">admin@freshco.com</div>
            </div>
            <button class="copy-btn" onclick="copyText('admin@freshco.com')">Copy</button>
          </div>

          <div class="cred-item">
            <div>
              <div class="cred-role">Branch Manager</div>
              <div class="cred-email">manager@freshco.com</div>
            </div>
            <button class="copy-btn" onclick="copyText('manager@freshco.com')">Copy</button>
          </div>

          <div class="cred-item">
            <div>
              <div class="cred-role">Front Cashier</div>
              <div class="cred-email">cashier@freshco.com</div>
            </div>
            <button class="copy-btn" onclick="copyText('cashier@freshco.com')">Copy</button>
          </div>

          <div class="cred-item">
            <div>
              <div class="cred-role">Customer Account</div>
              <div class="cred-email">sara@gmail.com</div>
            </div>
            <button class="copy-btn" onclick="copyText('sara@gmail.com')">Copy</button>
          </div>
        </div>

        <!-- cURL Snippet Helper -->
        <div class="section-card">
          <div class="section-header">
            <h2>💻 Quick cURL</h2>
            <button class="copy-btn" onclick="copyCurl()">Copy</button>
          </div>
          <pre id="curlBox" style="font-family: var(--mono); font-size: 11px; color: #cbd5e1; background: #060910; padding: 12px; border-radius: 8px; overflow-x: auto; white-space: pre-wrap;">curl -X GET "http://localhost:8000/api/v1/health" \\
  -H "Accept: application/json"</pre>
        </div>
      </div>
    </div>
  </div>

  <div id="toast">Message</div>

  <script>
    function showToast(msg) {{
      const t = document.getElementById('toast');
      t.innerText = msg;
      t.style.display = 'block';
      setTimeout(() => {{ t.style.display = 'none'; }}, 3000);
    }}

    function copyText(text) {{
      navigator.clipboard.writeText(text);
      showToast('Copied to clipboard: ' + text);
    }}

    function copyCurl() {{
      const text = document.getElementById('curlBox').innerText;
      navigator.clipboard.writeText(text);
      showToast('cURL copied!');
    }}

    function copyResponse() {{
      const text = document.getElementById('resBody').innerText;
      navigator.clipboard.writeText(text);
      showToast('Response copied to clipboard!');
    }}

    function toggleBodyInput() {{
      const m = document.getElementById('httpMethod').value;
      const b = document.getElementById('reqBody');
      b.style.display = (m === 'POST' || m === 'PATCH' || m === 'PUT') ? 'block' : 'none';
      updateCurl();
    }}

    function setPreset(method, endpoint, body) {{
      document.getElementById('httpMethod').value = method;
      document.getElementById('apiEndpoint').value = endpoint;
      if (body) {{
        document.getElementById('reqBody').value = body;
      }}
      toggleBodyInput();
      updateCurl();
      runConsoleRequest();
    }}

    function updateCurl() {{
      const method = document.getElementById('httpMethod').value;
      const ep = document.getElementById('apiEndpoint').value;
      const token = document.getElementById('authToken').value.trim();
      const body = document.getElementById('reqBody').value.trim();

      let cmd = `curl -X ${{method}} "http://localhost:8000${{ep}}" \\\\\\n  -H "Accept: application/json"`;
      if (token) {{
        cmd += ` \\\\\\n  -H "Authorization: Bearer ${{token}}"`;
      }}
      if ((method === 'POST' || method === 'PATCH') && body) {{
        cmd += ` \\\\\\n  -H "Content-Type: application/json" \\\\\\n  -d '${{body}}'`;
      }}
      document.getElementById('curlBox').innerText = cmd;
    }}

    async function autoLoginAdmin() {{
      showToast('Requesting admin token...');
      try {{
        const res = await fetch('/api/v1/auth/login', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ email: 'admin@freshco.com', password: 'password123' }})
        }});
        const data = await res.json();
        if (data.access_token) {{
          document.getElementById('authToken').value = data.access_token;
          showToast('✓ Admin token loaded!');
          updateCurl();
        }} else {{
          showToast('Login failed: ' + (data.detail || 'Check credentials'));
        }}
      }} catch (err) {{
        showToast('Login error: ' + err.message);
      }}
    }}

    async function runConsoleRequest() {{
      const method = document.getElementById('httpMethod').value;
      const endpoint = document.getElementById('apiEndpoint').value;
      const token = document.getElementById('authToken').value.trim();
      const bodyText = document.getElementById('reqBody').value.trim();

      const box = document.getElementById('resBox');
      const statusEl = document.getElementById('resStatus');
      const timeEl = document.getElementById('resTime');
      const bodyEl = document.getElementById('resBody');

      box.style.display = 'block';
      bodyEl.innerText = 'Sending request...';
      updateCurl();

      const startTime = performance.now();
      try {{
        const headers = {{ 'Accept': 'application/json' }};
        if (token) headers['Authorization'] = `Bearer ${{token}}`;
        if (method === 'POST' || method === 'PATCH') headers['Content-Type'] = 'application/json';

        const opt = {{ method, headers }};
        if ((method === 'POST' || method === 'PATCH') && bodyText) {{
          opt.body = bodyText;
        }}

        const resp = await fetch(endpoint, opt);
        const elapsed = Math.round(performance.now() - startTime);

        statusEl.innerText = `${{resp.status}} ${{resp.statusText || ''}}`;
        statusEl.className = 'res-status ' + (resp.status >= 200 && resp.status < 300 ? 'status-200' : 'status-400');
        timeEl.innerText = `${{elapsed}}ms`;

        const data = await resp.json().catch(() => ({{ detail: 'Non-JSON response' }}));
        bodyEl.innerText = JSON.stringify(data, null, 2);
      }} catch (err) {{
        statusEl.innerText = 'Error';
        statusEl.className = 'res-status status-400';
        bodyEl.innerText = err.message;
      }}
    }}

    async function seedDemoData() {{
      const btn = document.getElementById('seedBtn');
      btn.innerText = 'Seeding...';
      btn.disabled = true;
      try {{
        const res = await fetch('/api/v1/system/seed', {{ method: 'POST' }});
        const d = await res.json();
        showToast(d.message || 'Data seeded successfully!');
        refreshStats();
      }} catch (e) {{
        showToast('Seeding error: ' + e.message);
      }} finally {{
        btn.innerText = '🌱 Seed Demo Data';
        btn.disabled = false;
      }}
    }}

    async function refreshStats() {{
      try {{
        const res = await fetch('/api/v1/system/stats');
        if (res.ok) {{
          const d = await res.json();
          if (d.categories) document.getElementById('statProducts').innerText = `${{d.products || 0}} Products • ${{d.categories}} Categories`;
          if (d.orders) document.getElementById('statOrders').innerText = `${{d.orders}} Total Orders`;
          if (d.database) document.getElementById('diagDb').innerText = d.database;
        }}
      }} catch (e) {{}}
    }}

    function filterModules() {{
      const query = document.getElementById('modSearch').value.toLowerCase();
      const items = document.querySelectorAll('.module-item');
      items.forEach(el => {{
        const text = el.innerText.toLowerCase();
        el.style.display = text.includes(query) ? 'block' : 'none';
      }});
    }}

    // Initial refresh
    window.addEventListener('DOMContentLoaded', () => {{
      refreshStats();
      updateCurl();
    }});
  </script>
</body>
</html>
"""
