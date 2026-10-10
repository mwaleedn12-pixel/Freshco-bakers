"""
Custom API Documentation UI Generators (Modern Swagger UI & Scalar Reference).
"""

SWAGGER_CUSTOM_CSS = """
/* Freshco Bakers Custom Dark Bakery Theme for Swagger UI */
body {
  background-color: #090d16 !important;
  color: #f1f5f9 !important;
  font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.swagger-ui {
  color: #f1f5f9 !important;
}

.swagger-ui .topbar {
  background: #0f172a !important;
  border-bottom: 1px solid rgba(245, 158, 11, 0.3) !important;
  padding: 14px 24px !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
}

.swagger-ui .topbar .topbar-wrapper {
  display: flex !important;
  align-items: center !important;
}

.swagger-ui .topbar .topbar-wrapper a {
  display: flex !important;
  align-items: center !important;
  gap: 12px !important;
  color: #f59e0b !important;
  font-weight: 800 !important;
  font-size: 18px !important;
  text-decoration: none !important;
}

.swagger-ui .topbar .topbar-wrapper a::before {
  content: "🥐" !important;
  font-size: 26px !important;
}

.swagger-ui .info {
  margin: 30px 0 !important;
  padding: 24px !important;
  background: rgba(17, 26, 46, 0.8) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 14px !important;
  backdrop-filter: blur(10px) !important;
}

.swagger-ui .info .title {
  color: #f8fafc !important;
  font-weight: 800 !important;
  letter-spacing: -0.02em !important;
}

.swagger-ui .info p, .swagger-ui .info li {
  color: #94a3b8 !important;
  font-size: 14px !important;
}

.swagger-ui .scheme-container {
  background: rgba(15, 23, 42, 0.9) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 12px !important;
  padding: 16px !important;
  margin-bottom: 24px !important;
  box-shadow: none !important;
}

.swagger-ui .opblock-tag {
  color: #f8fafc !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
  font-size: 17px !important;
  font-weight: 700 !important;
  padding: 14px 0 !important;
}

.swagger-ui .opblock {
  border-radius: 12px !important;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2) !important;
  border: 1px solid rgba(255, 255, 255, 0.06) !important;
  background: rgba(17, 26, 46, 0.6) !important;
  margin: 0 0 14px !important;
}

.swagger-ui .opblock .opblock-summary {
  padding: 10px 16px !important;
}

.swagger-ui .opblock .opblock-summary-method {
  border-radius: 8px !important;
  font-weight: 800 !important;
  font-size: 12px !important;
  min-width: 75px !important;
  text-align: center !important;
}

.swagger-ui .opblock-get {
  background: rgba(16, 185, 129, 0.08) !important;
  border-color: rgba(16, 185, 129, 0.3) !important;
}
.swagger-ui .opblock-get .opblock-summary-method {
  background: #10b981 !important;
}

.swagger-ui .opblock-post {
  background: rgba(59, 130, 246, 0.08) !important;
  border-color: rgba(59, 130, 246, 0.3) !important;
}
.swagger-ui .opblock-post .opblock-summary-method {
  background: #3b82f6 !important;
}

.swagger-ui .opblock-patch {
  background: rgba(245, 158, 11, 0.08) !important;
  border-color: rgba(245, 158, 11, 0.3) !important;
}
.swagger-ui .opblock-patch .opblock-summary-method {
  background: #f59e0b !important;
}

.swagger-ui .opblock-delete {
  background: rgba(244, 63, 94, 0.08) !important;
  border-color: rgba(244, 63, 94, 0.3) !important;
}
.swagger-ui .opblock-delete .opblock-summary-method {
  background: #f43f5e !important;
}

.swagger-ui .opblock .opblock-summary-path {
  color: #f1f5f9 !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-weight: 600 !important;
}

.swagger-ui .opblock-body {
  background: #090d16 !important;
  color: #cbd5e1 !important;
}

.swagger-ui table thead tr th, .swagger-ui table thead tr td {
  color: #94a3b8 !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
}

.swagger-ui .parameters-col_name {
  color: #f8fafc !important;
}

.swagger-ui input[type=text], .swagger-ui textarea {
  background: #0f172a !important;
  color: #f8fafc !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  border-radius: 8px !important;
}

.swagger-ui .btn {
  border-radius: 8px !important;
  font-weight: 600 !important;
}

.swagger-ui .btn.execute {
  background: linear-gradient(135deg, #f59e0b, #d97706) !important;
  color: #0b0f19 !important;
  border: none !important;
  font-weight: 700 !important;
}

.swagger-ui .btn.authorize {
  border-color: #f59e0b !important;
  color: #f59e0b !important;
}

.swagger-ui .btn.authorize svg {
  fill: #f59e0b !important;
}

.swagger-ui section.models {
  background: rgba(17, 26, 46, 0.6) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 12px !important;
}

.swagger-ui section.models h4 {
  color: #f8fafc !important;
}

.swagger-ui .model-box {
  background: #090d16 !important;
}
"""


def get_custom_swagger_html(openapi_url: str, title: str = "Freshco Bakers API — Swagger UI") -> str:
    """Returns custom-styled Swagger UI with Freshco Bakers dark gold bakery branding."""
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🥐</text></svg>">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
  <style>
    {SWAGGER_CUSTOM_CSS}
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.onload = function() {{
      window.ui = SwaggerUIBundle({{
        url: '{openapi_url}',
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIBundle.SwaggerUIStandalonePreset
        ],
        layout: "BaseLayout",
        docExpansion: "list",
        filter: true,
        showExtensions: true,
        showCommonExtensions: true,
        defaultModelsExpandDepth: 1
      }});
    }};
  </script>
</body>
</html>
"""


def get_scalar_html(openapi_url: str, title: str = "Freshco Bakers API Reference — Scalar") -> str:
    """Returns ultra-modern Scalar API Reference UI."""
    return f"""<!doctype html>
<html>
  <head>
    <title>{title}</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🥐</text></svg>">
    <style>
      body {{
        margin: 0;
        background: #090d16;
      }}
    </style>
  </head>
  <body>
    <script
      id="api-reference"
      data-url="{openapi_url}"
      data-configuration='{{"theme":"saturn","darkMode":true,"layout":"modern","searchHotKey":"k"}}'
      src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
  </body>
</html>
"""
