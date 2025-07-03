# Royaltree Backend API Documentation

## Overview

This document provides the API documentation for the Royaltree backend, which is built using FastAPI. The backend powers a digital content fractional ownership and royalty platform. Features include authentication, digital asset management, user dashboards (creator/investor), transaction management, royalty simulation, and admin operations.

**Base URL:** All endpoints are relative to the deployment's root, e.g., `https://your-deployment.com/`

---

## Authentication

- Many routes require an **access token** as the `token` query parameter for authenticated calls.
- User roles supported: `creator`, `investor`, `admin`.
- Obtain an access token by logging in via `/auth/login`.

---

## API Endpoints

### Public

#### `GET /`
**Description:** Landing endpoint. Returns platform info, main routes.
**Authentication:** None

**Response:**
```json
{
  "platform": "Royaltree",
  "description": "Digital content platform for fractional ownership, investment, and royalties.",
  "main_routes": [
    "/auth/register", "/auth/login", "/creator/assets", "/investor/marketplace",
    "/assets/{id}", "/transactions", "/dashboard", "/admin/panel", "/health/db"
  ]
}
```

#### `GET /health/db`
**Description:** Checks health/connection to the SQLite DB.
**Authentication:** None

**Responses:**
- `200 OK` Healthy: `{"status": "healthy"}`
- `200 OK` Unhealthy: `{"status": "unhealthy", "detail": "..."}`

---

### Authentication

#### `POST /auth/register`
**Description:** Register a new user (creator/investor/admin).
**Body:** JSON, UserCreate

| Field     | Type    | Description           | Required |
|-----------|---------|-----------------------|----------|
| username  | string  | Unique username       | Yes      |
| email     | string  | User's email (valid)  | Yes      |
| role      | string  | One of: creator, investor, admin | Yes |
| password  | string  | Password (min 6 chars)| Yes      |

**Response:** 201 or 200, UserPublic model.

#### `POST /auth/login`
**Description:** Authenticate user and get an access token.
**Body:** Form (not JSON), fields: `username`, `password` (OAuth2 standard)

**Response:**
```json
{
  "access_token": "<token>",
  "token_type": "bearer"
}
```

---

### Creator Endpoints
All endpoints require `token` for a user with `role=creator` (as a query param).

#### `POST /creator/assets`
**Description:** Upload a new digital asset (file required, for approval).
**Body:** `multipart/form-data` (fields & file)

| Field          | Type       | Notes                                    |
|----------------|------------|------------------------------------------|
| title          | string     | Required                                 |
| description    | string     | Optional                                 |
| category       | string     | Optional (music, book, art, etc.)        |
| total_shares   | int        | Required, must be >0                     |
| price_per_share| float      | Required, must be >0                     |
| royalty_percent| float      | Required, 0-100                          |
| file           | file       | Required (binary asset content)          |

**Response:** AssetPublic (JSON)

#### `GET /creator/assets`
**Description:** List all assets created by the creator.
**Response:** List of AssetPublic

#### `GET /creator/earnings`
**Description:** Returns earnings summary for creator (sales & royalties).
**Response:**
```json
{
  "total_sales": <float>,
  "total_royalties": <float>
}
```

---

### Investor Endpoints
All endpoints require `token` for a user with `role=investor` (as a query param).

#### `GET /investor/marketplace`
**Description:** Get all approved assets available for fractional purchase.
**Response:** List of AssetPublic

#### `POST /investor/assets/buy`
**Description:** Purchase shares of an asset.
**Body:** Form data.

| Field    | Type   | Description            |
|----------|--------|------------------------|
| asset_id | int    | ID of the asset        |
| shares   | int    | Number of shares to buy|

**Response:**
```json
{
  "status": "success",
  "shares_bought": <int>,
  "total_price": <float>
}
```

#### `GET /investor/assets`
**Description:** List assets (and shares/earnings) owned by the investor.
**Response:** List of asset metadata with investor share/earnings fields.

#### `GET /investor/earnings`
**Description:** Return all earned royalties and realized gains for investor.
**Response:**
```json
{
  "total_royalties": <float>,
  "total_gains": <float>
}
```

---

### Asset Endpoints

#### `GET /assets/{asset_id}`
**Description:** Get metadata and details about an asset (public + authenticated).
**Parameters:**
- `asset_id` (int, path)
- `token` (optional, for extra access if needed)

**Response:** AssetPublic

#### `GET /assets/{asset_id}/download`
**Description:** Download asset file (only creator, admin or shareholder!).
**Parameters:**
- `asset_id` (int, path)
- `token` (required, query param)

**Response:** File (content-disposition attachment if permitted)

#### `POST /assets/{asset_id}/dispute`
**Description:** Submit a dispute for an asset.
**Parameters:**
- `asset_id` (int, path)
- `token` (required, query param)
**Body:** Form data

| Field   | Type   | Description      |
|---------|--------|------------------|
| reason  | string | Reason for dispute |

**Response:**
```json
{
  "status": "submitted",
  "asset_id": <int>
}
```

---

### Transactions

#### `GET /transactions`
**Description:** List all transactions for the authenticated user.
**Parameters:** 
- `token` (query param)

**Response:** Array of transaction objects.

#### `POST /transactions/royalty`
**Admin only** (token for admin)
**Description:** Simulate royalty payout to all asset shareholders.
**Body:** Form data

| Field    | Type   | Description        |
|----------|--------|--------------------|
| asset_id | int    | ID of asset        |
| amount   | float  | Royalty payout total|

**Response:**
```json
{
  "status": "royalty distributed",
  "shareholders": <int>
}
```
or
```json
{
  "distributed": 0,
  "note": "No shareholders for this asset"
}
```

---

### Admin Panel / Approvals / Disputes

**All endpoints require ADMIN token**

#### `GET /admin/assets/pending`
**Description:** List all pending assets for approval.
**Response:** List of AssetPublic

#### `POST /admin/assets/{asset_id}/status`
**Description:** Approve or reject an asset.
**Parameters:**
- `asset_id` (int, path)
**Body:** Form data

| Field        | Type   | Description                 |
|--------------|--------|-----------------------------|
| asset_status | string | Must be "approved" or "rejected" |

**Response:**
```json
{
  "asset_id": <int>,
  "new_status": "approved" | "rejected"
}
```

#### `GET /admin/panel/disputes`
**Description:** List all open disputes.
**Response:** Array of dispute details

#### `POST /admin/panel/disputes/resolve`
**Description:** Resolve/close a dispute.
**Body:** Form data

| Field       | Type   | Description           |
|-------------|--------|-----------------------|
| dispute_id  | int    | ID of dispute         |
| resolution  | string | Resolution summary    |

**Response:**
```json
{
  "status": "resolved",
  "dispute_id": <int>,
  "resolution": "<string>"
}
```

---

### Dashboard

#### `GET /dashboard`
**Description:** Aggregated dashboard for an authenticated user
**Parameters:** 
- `token` (query param)

**Response:** 
- For creators:
```json
{
  "role": "creator",
  "owned_assets": [AssetPublic, ...],
  "earnings_total": <float>,
  "royalties_received": <float>
}
```
- For investors:
```json
{
  "role": "investor",
  "invested_assets": [
    { ...AssetPublic fields..., "shares_owned": int, "earnings": float }
  ],
  "earnings_total": <float>,
  "royalties_received": <float>
}
```

---

## Data Models

### UserCreate
```json
{
  "username": "string",
  "email": "user@email.com",
  "role": "creator"|"investor"|"admin",
  "password": "string"
}
```
### UserPublic
```json
{
  "id": 1,
  "username": "string",
  "email": "user@email.com",
  "role": "creator"|"investor"|"admin"
}
```
### AssetPublic
```json
{
  "id": 1,
  "title": "string",
  "description": "string",
  "category": "string",
  "total_shares": 1000,
  "price_per_share": 10.0,
  "royalty_percent": 15.5,
  "creator_id": 4,
  "status": "pending"|"approved"|"rejected",
  "file_url": "/uploaded_assets/file.mp3",
  "shares_available": 256,
  "shares_sold": 744,
  "earnings_total": 2000.0
}
```
### TransactionPublic
```json
{
  "id": 123,
  "asset_id": 1,
  "user_id": 4,
  "shares": 50,
  "type": "buy"|"sell"|"royalty",
  "price": 500.0,
  "timestamp": "YYYY-MM-DDTHH:mm:ss"
}
```

---

## Authentication & Authorization Table

| Endpoint                              | Auth Role Required      | Method & Route                   |
|----------------------------------------|------------------------|----------------------------------|
| `/auth/register`                      | None                   | POST `/auth/register`            |
| `/auth/login`                         | None                   | POST `/auth/login`               |
| `/`                                   | None                   | GET `/`                          |
| `/health/db`                          | None                   | GET `/health/db`                 |
| `/creator/*`                          | creator                | various                          |
| `/investor/*`                         | investor               | various                          |
| `/admin/*`                            | admin                  | various                          |
| `/assets/{id}`                        | Optional token         | GET `/assets/{id}`               |
| `/assets/{id}/download`                | Asset shareholder/admin/creator | GET `/assets/{id}/download`      |
| `/dashboard`                          | Any authenticated      | GET `/dashboard`                 |
| `/transactions`                       | Any authenticated      | GET `/transactions`              |

---

## Real-Time Usage

- WebSocket endpoints are not implemented. Use standard HTTP endpoints and polling.

---

## Notes

- All POST endpoints expect form data unless otherwise noted.
- All endpoints that require authentication expect a `token` in the query string, unless they are run as FastAPI dependency injection (i.e., using Depends).

---

## Further References

- See the FastAPI OpenAPI docs at `/docs` or `/openapi.json` for an interactive reference.

