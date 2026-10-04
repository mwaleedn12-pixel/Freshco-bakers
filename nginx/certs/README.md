# Placeholder directory for TLS certificates.
# In production, mount your Let's Encrypt / purchased certs here:
#   fullchain.pem   — server certificate + intermediates
#   privkey.pem     — private key
#
# For local development with self-signed certs:
#   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
#       -keyout privkey.pem -out fullchain.pem \
#       -subj "/CN=localhost"
