# Aarozi Healthcare — Production Deployment & Cloud Hosting

---

## 1. Cloud Architecture Overview

The central cloud infrastructure serves purely as the commercial SaaS hub:
- **Domain:** `https://aarozi.health`
- **Reverse Proxy:** Caddy 2 (Automatic TLS 1.3, Let's Encrypt certificates, HTTP/3)
- **Application Server:** FastAPI (4 Uvicorn workers)
- **Frontend:** Nuxt 3 SSR
- **Database:** PostgreSQL 16 (Customer accounts, orders, license claims)
- **Object Storage:** Cloudflare R2 (Windows executable distribution, zero egress fees)

---

## 2. 5-Minute Production Spin-Up

On your Ubuntu 24.04 VPS (Hetzner, DigitalOcean, or AWS):

```bash
# 1. Clone repository
git clone https://github.com/your-org/Aarozi_Healthcare.git
cd Aarozi_Healthcare

# 2. Configure production environment
cp deploy/production.env.example .env
nano .env  # Enter DOMAIN, POSTGRES_PASSWORD, SECRET_KEY

# 3. Launch Docker containers
docker compose -f docker-compose.prod.yml up -d --build

# 4. Verify health status
curl -k https://localhost/health
```

Caddy immediately provisions trusted SSL certificates and starts serving the commercial marketing landing page, customer dashboard, and payment webhooks.

