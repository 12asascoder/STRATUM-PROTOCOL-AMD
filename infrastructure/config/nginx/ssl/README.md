# SSL Certificates Directory

This directory should contain SSL certificates for HTTPS support.

## For Development (Self-Signed Certificates)

Generate self-signed certificates for local development:

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout key.pem \
  -out cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

## For Production

Place your production SSL certificates in this directory:
- `cert.pem` - SSL certificate
- `key.pem` - Private key
- `chain.pem` - Certificate chain (optional)

Or use Let's Encrypt with cert-manager in Kubernetes.
