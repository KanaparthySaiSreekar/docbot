# DocBot Deployment Guide

Quick reference for deploying DocBot on kanapa.space homelab.

---

## Quick Deploy

```bash
cd /home/kanapasai/homelab
docker-compose up -d --build docbot
```

---

## Initial Setup (One-time)

### 1. Create Required Directories
```bash
mkdir -p /home/kanapasai/homelab/projects/docbot/data
```

### 2. Create Production Config
```bash
cd /home/kanapasai/homelab/projects/docbot
cp config.example.json config.prod.json
```

### 3. Edit Configuration
Edit `config.prod.json` and update:

#### Required Settings
```json
{
  "database": {
    "path": "data/docbot.db"
  },
  "app": {
    "env": "prod",
    "base_url": "https://docbot.kanapa.space",
    "timezone": "Asia/Kolkata",
    "debug": false,
    "log_level": "INFO"
  }
}
```

#### API Credentials (Get from respective dashboards)

**Google OAuth** (from Google Cloud Console):
```json
"auth": {
  "google_client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
  "google_client_secret": "YOUR_SECRET",
  "session_secret_key": "generate_with: openssl rand -hex 32"
}
```

**WhatsApp Cloud API** (from Meta Business Suite):
```json
"whatsapp": {
  "phone_number_id": "YOUR_PHONE_NUMBER_ID",
  "access_token": "YOUR_ACCESS_TOKEN",
  "verify_token": "YOUR_CUSTOM_VERIFY_TOKEN",
  "api_version": "v21.0"
}
```

**Razorpay** (from Razorpay Dashboard):
```json
"razorpay": {
  "key_id": "rzp_live_YOUR_KEY_ID",
  "key_secret": "YOUR_KEY_SECRET",
  "webhook_secret": "YOUR_WEBHOOK_SECRET"
}
```

**Google Calendar** (from Google Cloud Console):
```json
"google_calendar": {
  "credentials_path": "google_calendar_credentials.json",
  "calendar_id": "YOUR_CALENDAR_ID@gmail.com"
}
```

---

## Build Issues & Fixes

### Issue 1: Source Code Not Found in Builder
**Error**: `Expected a Python module at: src/docbot/__init__.py`

**Fix**: Dockerfile now copies source code before `uv sync`:
```dockerfile
COPY pyproject.toml uv.lock README.md ./
COPY src/ /app/src/
RUN uv sync --frozen --no-dev
```

### Issue 2: README.md Blocked
**Error**: `failed to open file /app/README.md`

**Fix**: Added exception in `.dockerignore`:
```
*.md
!README.md
```

### Issue 3: Missing C Compiler for pycairo
**Error**: `Unknown compiler(s): [['cc'], ['gcc']...`

**Fix**: Added build dependencies to Dockerfile:
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*
```

---

## Docker Compose Configuration

Located in: `/home/kanapasai/homelab/docker-compose.yml`

```yaml
  docbot:
    build:
      context: ./projects/docbot
      dockerfile: Dockerfile
    container_name: docbot
    restart: unless-stopped
    volumes:
      - ./projects/docbot/data:/app/data
      - ./projects/docbot/config.${DOCBOT_ENV:-prod}.json:/app/config.${DOCBOT_ENV:-prod}.json:ro
    environment:
      - DOCBOT_ENV=${DOCBOT_ENV:-prod}
    networks:
      - web
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.docbot.rule=Host(`docbot.kanapa.space`)"
      - "traefik.http.routers.docbot.entrypoints=web"
      - "traefik.http.services.docbot.loadbalancer.server.port=8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
```

---

## Cloudflare Tunnel Configuration

### 1. Edit Tunnel Config
```bash
sudo nano /home/sreeni/docker/cloudflared/config/config.yml
```

### 2. Add DocBot Entry
```yaml
ingress:
  - hostname: docbot.kanapa.space
    service: http://localhost:80
  # ... other services
  - service: http_status:404
```

### 3. Restart Cloudflared
```bash
docker restart cloudflared
```

---

## Cloudflare DNS Configuration

1. Go to Cloudflare Dashboard → kanapa.space → DNS
2. Add CNAME record:
   - **Type**: CNAME
   - **Name**: `docbot`
   - **Target**: `<your-tunnel-id>.cfargotunnel.com`
   - **Proxy status**: ✅ Proxied (orange cloud)
   - **TTL**: Auto

---

## Deployment Commands

### Build and Start
```bash
cd /home/kanapasai/homelab
docker-compose up -d --build docbot
```

### View Logs
```bash
# Live logs
docker-compose logs -f docbot

# Last 100 lines
docker-compose logs --tail=100 docbot
```

### Restart
```bash
docker-compose restart docbot
```

### Stop
```bash
docker-compose stop docbot
```

### Remove
```bash
docker-compose down docbot
```

---

## Verification

### 1. Check Container Status
```bash
docker ps | grep docbot
```

Expected output:
```
CONTAINER ID   IMAGE            STATUS                    PORTS      NAMES
xxx            homelab-docbot   Up X minutes (healthy)    8000/tcp   docbot
```

### 2. Check Logs
```bash
docker-compose logs docbot | tail -20
```

Expected to see:
```json
{"timestamp": "...", "level": "INFO", "logger_name": "docbot.main", "message": "DocBot API starting up", "env": "prod"}
{"timestamp": "...", "level": "INFO", "logger_name": "docbot.database", "message": "Database initialized successfully"}
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3. Test Health Endpoint Locally
```bash
# Direct container test
docker exec docbot curl -s http://localhost:8000/health

# Through Traefik
curl -s -H "Host: docbot.kanapa.space" http://localhost:80/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-07T...",
  "env": "prod"
}
```

### 4. Check Network
```bash
docker network inspect web --format '{{range .Containers}}{{.Name}} {{end}}'
```

Should include: `docbot traefik portfolio`

### 5. Test Public Access
```bash
curl -s https://docbot.kanapa.space/health
```

**Note**: DNS may take 5-10 minutes to propagate

---

## Accessing the Application

- **Main App**: https://docbot.kanapa.space
- **Health Check**: https://docbot.kanapa.space/health
- **Ready Check**: https://docbot.kanapa.space/ready
- **Dashboard**: https://docbot.kanapa.space/dashboard (requires Google OAuth)

---

## Troubleshooting

### Container Won't Start

**Check logs**:
```bash
docker-compose logs docbot
```

**Common issues**:
- Missing config file: Ensure `config.prod.json` exists
- Database path issue: Check `data/` directory exists and is writable
- Port conflict: Ensure port 8000 isn't used by another service

### Site Not Accessible

1. **Check container is running**:
   ```bash
   docker ps | grep docbot
   ```

2. **Test local access**:
   ```bash
   curl -H "Host: docbot.kanapa.space" http://localhost:80
   ```

3. **Check Traefik logs**:
   ```bash
   docker-compose logs traefik | grep docbot
   ```

4. **Check cloudflared**:
   ```bash
   docker logs cloudflared | grep docbot
   ```

5. **Verify DNS**:
   ```bash
   dig docbot.kanapa.space
   ```

### Health Check Failing

```bash
# Check health status
docker inspect docbot | jq '.[0].State.Health'

# Test health endpoint
docker exec docbot curl -f http://localhost:8000/health
```

### Database Issues

```bash
# Check database file exists
ls -lh /home/kanapasai/homelab/projects/docbot/data/

# Check database permissions
docker exec docbot ls -lh /app/data/

# View database logs
docker-compose logs docbot | grep database
```

---

## Updating the Application

### 1. Pull Latest Code
```bash
cd /home/kanapasai/homelab/projects/docbot
git pull
```

### 2. Backup Database (Important!)
```bash
cp data/docbot.db data/docbot.db.backup-$(date +%Y%m%d-%H%M%S)
```

### 3. Rebuild and Deploy
```bash
cd /home/kanapasai/homelab
docker-compose up -d --build docbot
```

### 4. Verify
```bash
docker-compose logs -f docbot
curl https://docbot.kanapa.space/health
```

---

## Database Management

### Backup Database
```bash
# Manual backup
cp /home/kanapasai/homelab/projects/docbot/data/docbot.db \
   /home/kanapasai/homelab/projects/docbot/data/backups/docbot-$(date +%Y%m%d).db

# From inside container
docker exec docbot cp /app/data/docbot.db /app/data/docbot.db.backup
```

### Restore Database
```bash
# Stop container
docker-compose stop docbot

# Restore backup
cp data/backups/docbot-20260207.db data/docbot.db

# Start container
docker-compose start docbot
```

### Access Database (SQLite)
```bash
# Install sqlite3 in container
docker exec -it docbot sh
apk add --no-cache sqlite  # if alpine
apt-get install sqlite3    # if debian

# Access database
sqlite3 /app/data/docbot.db
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCBOT_ENV` | `prod` | Environment (test/prod) |

To use test config:
```bash
DOCBOT_ENV=test docker-compose up -d docbot
```

---

## File Locations

### On Host
```
/home/kanapasai/homelab/projects/docbot/
├── config.prod.json          # Production config (not in git)
├── config.test.json          # Test config (not in git)
├── config.example.json       # Template
├── data/
│   ├── docbot.db            # SQLite database
│   └── backups/             # Database backups
├── src/                      # Source code
├── Dockerfile               # Container build
└── docker-compose.yml       # Local compose (not used)
```

### In Container
```
/app/
├── config.prod.json         # Mounted from host (read-only)
├── data/
│   └── docbot.db           # Mounted from host
├── src/docbot/             # Copied during build
├── db/                     # SQL schemas
└── .venv/                  # Python virtual environment
```

---

## Security Notes

1. **Never commit secrets**: `config.prod.json` is in `.gitignore`
2. **Config is read-only**: Mounted with `:ro` flag
3. **Use strong secrets**: Generate with `openssl rand -hex 32`
4. **Keep credentials updated**: Rotate API keys regularly
5. **Monitor logs**: Check for authentication failures

---

## Performance Monitoring

### Container Resource Usage
```bash
docker stats docbot
```

### Application Logs
```bash
# JSON formatted logs
docker-compose logs docbot | jq '.'

# Filter by level
docker-compose logs docbot | jq 'select(.level == "ERROR")'
```

### Database Size
```bash
du -h /home/kanapasai/homelab/projects/docbot/data/docbot.db
```

---

## Quick Reference

### Essential Commands
```bash
# Deploy
docker-compose up -d --build docbot

# Restart
docker-compose restart docbot

# Logs
docker-compose logs -f docbot

# Health
curl https://docbot.kanapa.space/health

# Shell access
docker exec -it docbot sh

# Stop
docker-compose stop docbot
```

### URLs
- App: https://docbot.kanapa.space
- Health: https://docbot.kanapa.space/health
- Dashboard: https://docbot.kanapa.space/dashboard

### Ports
- External: 443 (HTTPS via Cloudflare)
- Traefik: 80 (HTTP)
- Container: 8000 (internal)

---

## Support

For issues specific to DocBot application:
1. Check application logs for errors
2. Verify all API credentials are correct
3. Check database integrity
4. Review configuration settings

For infrastructure issues, see: `/home/kanapasai/homelab/DEPLOYMENT-GUIDE.md`

---

**Last Updated**: 2026-02-07
