# Nivesh Firewall — Manual Render Deployment Guide

This guide provides the exact, step-by-step instructions for deploying the Nivesh Firewall production architecture manually through the [Render Dashboard](https://dashboard.render.com).

---

## 1. Architecture Overview on Render

```text
┌─────────────────────────────────────────────────────────────┐
│ Browser Client                                              │
└────────────────┬────────────────────────────────────────────┘
                 │ HTTPS
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Render Static Site (Frontend SPA)                           │
│ - URL: https://nivesh-app.onrender.com                      │
│ - Build: npm install && npm run build                       │
│ - Publish Directory: frontend/dist                          │
│ - SPA Rewrite: /* -> /index.html                            │
└────────────────┬────────────────────────────────────────────┘
                 │ REST API (HTTPS / CORS restricted)
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Render Web Service (FastAPI Backend)                        │
│ - URL: https://nivesh-api.onrender.com                      │
│ - Runtime: Docker (Dockerfile) or Python 3.11               │
│ - Bind: 0.0.0.0:$PORT                                       │
│ - Health Check Path: /health/live                           │
│ - Preflight: Alembic migrations to head + Engine checks     │
└────────────────┬────────────────────────────────────────────┘
                 │ TCP (SSL / internal private network)
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Render Managed PostgreSQL                                   │
│ - Version: PostgreSQL 15 / 16                               │
│ - Internal connection string: postgresql://...              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Recommended Deployment Order

To correctly resolve the circular CORS & API URL dependencies:

1. **Step 1**: Create the **Render PostgreSQL** database.
2. **Step 2**: Create the **Backend Web Service** (deploys initial container, generates backend URL).
3. **Step 3**: Create the **Frontend Static Site** (bakes backend URL into static bundle at build time).
4. **Step 4**: Update the **Backend CORS configuration** (`NIVESH_ALLOWED_ORIGINS`) with the actual frontend URL.

---

## 3. Step 1: Render PostgreSQL Database

In the Render Dashboard:
1. Click **New +** → **PostgreSQL**.
2. Configure settings:
   - **Name**: `nivesh-db`
   - **Database**: `nivesh_db`
   - **User**: `nivesh_user`
   - **Region**: Choose the region closest to your users (e.g. `Oregon (US West)` or `Frankfurt (EU Central)`).
     > **CRITICAL**: The Backend Web Service and Database **must be created in the same Render region** for low latency and free internal network bandwidth.
   - **PostgreSQL Version**: `16` (or `15`)
   - **Instance Type**: `Free` (or `Starter` / higher for persistent storage)
3. Click **Create Database**.
4. Once provisioned, locate the **Connections** panel on the database dashboard:
   - Copy the **Internal Database URL** (e.g. `postgres://nivesh_user:password@dpg-xxxxx-a:5432/nivesh_db`).
   - *Note*: Nivesh Firewall automatically normalizes legacy `postgres://` schemes to modern `postgresql://`.

---

## 4. Step 2: Backend Web Service

In the Render Dashboard:
1. Click **New +** → **Web Service**.
2. Connect your Git repository (`Nivesh_FireWall`).
3. Configure settings:
   - **Name**: `nivesh-api` (or your chosen backend name)
   - **Region**: **Same region** as your PostgreSQL database.
   - **Branch**: `master` (or deployment branch)
   - **Root Directory**: Leave blank (uses repo root)
   - **Environment / Runtime**: `Docker` (recommended, uses the production multi-stage `Dockerfile`)
     *(Alternatively, if choosing `Python 3`: Build Command: `pip install -r requirements.txt`, Start Command: `python scripts/entrypoint.py`)*
   - **Instance Type**: `Free` or `Starter`
4. Expand **Advanced**:
   - **Health Check Path**: `/health/live`
   - **Auto-Deploy**: `Yes` (or manual if preferred)
5. Under **Environment Variables**, add:

| Variable Name | Example / Value | Description |
|---|---|---|
| `NIVESH_ENV` | `production` | Strict production mode |
| `NIVESH_DEBUG` | `False` | Disables debug stacktraces and endpoints |
| `NIVESH_SECRET_KEY` | *(Generate 64 hex chars)* | `openssl rand -hex 32` |
| `NIVESH_DATABASE_URL` | *(Render Internal Database URL)* | Copied from Step 1 |
| `NIVESH_DB_SSL_MODE` | `require` (or `prefer`) | Enforces SSL connection to database |
| `NIVESH_WORKERS` | `2` (or `1` on Free tier) | ASGI worker process count |
| `NIVESH_SOURCE_MODE` | `OFFICIAL_SNAPSHOT` | Production regulatory gateway mode |
| `NIVESH_ALLOWED_ORIGINS` | `https://placeholder.onrender.com` | Temporary; update in Step 4 |
| `NIVESH_FORWARDED_ALLOW_IPS` | `*` | Trusts Render load balancer reverse proxy |

*(Optional exchange credentials if using LIVE source mode)*:
- `NSE_API_KEY`, `NSE_API_SECRET`, `BSE_API_KEY`, `BSE_API_SECRET`

6. Click **Create Web Service**.
7. Note down your backend URL (e.g., `https://nivesh-api.onrender.com`).

---

## 5. Step 3: Frontend Static Site

In the Render Dashboard:
1. Click **New +** → **Static Site**.
2. Connect your Git repository (`Nivesh_FireWall`).
3. Configure settings:
   - **Name**: `nivesh-app` (or your chosen frontend name)
   - **Branch**: `master` (or deployment branch)
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`
     *(Note: If Root Directory is left blank, use Build Command: `cd frontend && npm install && npm run build` and Publish Directory: `frontend/dist`)*
4. Under **Environment Variables**, add:

| Variable Name | Value | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `https://nivesh-api.onrender.com` | Your actual backend URL from Step 2 |
| `NODE_VERSION` | `20` | Ensures Node.js 20+ runtime |

> **IMPORTANT**: Vite bakes `VITE_API_BASE_URL` into client JavaScript bundles **at build time**. Whenever you change this variable, you must trigger a manual deploy or clear build cache.

5. Click **Create Static Site**.
6. Note down your frontend URL (e.g., `https://nivesh-app.onrender.com`).

---

## 6. Step 4: SPA Routing & Backend CORS Update

### A. SPA Direct Routing Rule (Prevents 404 on Refresh)
In the Render Static Site dashboard (`nivesh-app`):
1. Navigate to **Redirects / Rewrites** in the left menu.
2. Click **Add Rule**:
   - **Type**: `Rewrite`
   - **Source**: `/*`
   - **Destination**: `/index.html`
   - **Status Code**: `200`
3. Click **Save**.

### B. Update Backend CORS Origin
In the Render Web Service dashboard (`nivesh-api`):
1. Navigate to **Environment** in the left menu.
2. Edit `NIVESH_ALLOWED_ORIGINS`:
   - Set to: `https://<your-actual-frontend>.onrender.com`
   - *Example*: `https://nivesh-app.onrender.com`
   - *(If using custom domains later, separate with comma: `https://nivesh-app.onrender.com,https://app.nivesh.ai`)*
   - **DO NOT** use `*` (production validation strictly forbids wildcard origins).
3. Click **Save Changes**. Render will automatically redeploy the backend with the new allowed origin.

---

## 7. Verification Checklist

After deployment completes:

1. **Backend Liveness**:
   - Open: `https://<backend-url>.onrender.com/health/live`
   - Expected response: `{"status":"alive",...}` with HTTP 200.

2. **Backend Readiness**:
   - Open: `https://<backend-url>.onrender.com/health/ready`
   - Expected response: `{"status":"ready","database":{"status":"healthy","connected":true},...}` with HTTP 200.

3. **Frontend Application**:
   - Open: `https://<frontend-url>.onrender.com`
   - Verify: The Nivesh Firewall UI renders with green "Protected" shield indicator.

4. **End-to-End Analysis**:
   - Submit a test financial message in the input box.
   - Verify: Backend processes the request, returns evidence and policy decision, and frontend displays the verification badges.
