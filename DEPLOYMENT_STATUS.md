# MeetMaster Deployment Status

Date: 2026-05-14

## Server Access

SSH access works with the temporary local key:

```powershell
ssh -i .deploy_keys\meetmaster_beget_ed25519 root@155.212.135.186
```

Server facts checked after login:

- Host: `ai-test-proba`
- OS: Ubuntu 24.04.4 LTS
- Root filesystem after deployment: about `22G` used of `24G`, about `2.1G` free, `92%`
- Existing Docker workloads were already present: Supabase and n8n under `/opt/stack`
- Existing workloads were not removed or modified

## MeetMaster Deployment

MeetMaster was deployed to:

```text
/opt/meetmaster/app
```

Deployment source:

```text
https://github.com/swet757-cpu/meetmaster.git
server commit: 3c2a807
```

Secret/runtime files copied to the server:

```text
/opt/meetmaster/app/.env
/opt/meetmaster/app/credentials/google_client_secret.json
/opt/meetmaster/app/credentials/google_token.json
```

Server-only PostgreSQL variables were appended to `/opt/meetmaster/app/.env`:

```text
POSTGRES_USER=<set>
POSTGRES_DB=<set>
POSTGRES_PASSWORD=<set>
```

Docker Compose start succeeded:

```bash
cd /opt/meetmaster/app
docker compose up -d --build
```

Running MeetMaster containers:

```text
app-db-1   postgres:16-alpine   healthy
app-bot-1  app-bot              running
```

Bot log confirms startup:

```text
Running upgrade  -> 20260511_0001, initial schema
Start polling
Run polling for bot @MeetMaste_bot id=8770189132 - 'MeetMaster'
```

Database migration verification:

```text
alembic_version = 20260511_0001
```

## Fix 2026-05-14: Large Telegram IDs

Problem found in production logs after the first booking confirmation attempt:

```text
invalid input for query argument ... value out of int32 range
WHERE users.telegram_id = $1::INTEGER
```

The user's Telegram ID was larger than a PostgreSQL `integer`. Fixed by changing `users.telegram_id` to `BigInteger` and adding migration:

```text
20260514_0002_users_telegram_id_bigint.py
```

Server verification after redeploy:

```text
alembic_version = 20260514_0002
users.telegram_id = bigint
app-bot-1 = running
app-db-1 = healthy
```

## Important Risk

Disk space is tight. Do not reinstall the server or delete existing Docker/Supabase/n8n data blindly.

Before future large builds or updates, check:

```bash
df -h /
docker system df
du -h --max-depth=1 /var/lib/docker 2>/dev/null | sort -h
```
