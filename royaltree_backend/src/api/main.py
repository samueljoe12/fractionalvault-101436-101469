from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Query, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Union
from datetime import datetime, timedelta
import sqlite3
import hashlib
import secrets
import os
from fastapi.responses import JSONResponse

# --- App Configuration ---
app = FastAPI(
    title="Royaltree Backend API",
    description="API backend for Royaltree: a digital content fractional ownership and royalty platform. Features: Auth, assets, transactions, creator/investor dashboards, admin ops. SQLite database.",
    version="1.0.0",
    openapi_tags=[
        {"name": "public", "description": "Landing and health endpoints"},
        {"name": "auth", "description": "User registration and authentication"},
        {"name": "creator", "description": "Endpoints for creators"},
        {"name": "investor", "description": "Endpoints for investors"},
        {"name": "admin", "description": "Admin panel and moderation"},
        {"name": "assets", "description": "Asset and IP management"},
        {"name": "transactions", "description": "Buy/sell and royalty/earning endpoints"},
        {"name": "dashboard", "description": "User and role-based dashboards"},
    ]
)

# --- CORS Configuration (Aligned to Frontend on HTTPS port 3000) ---

# The ONLY allowed frontend is the HTTPS version, port 3000:
# https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3000
# You may set FRONTEND_ORIGINS as a comma-separated list in your environment for overrides.

_frontend_origins = os.environ.get(
    "FRONTEND_ORIGINS",
    "https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3000"
).split(",")

# DO NOT allow '*' if allow_credentials is True! Protocol (https) and port (3000) must match UI!
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in _frontend_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

DB_PATH = os.environ.get("ROYALTREE_DB_PATH", "royaltree.sqlite3")
ASSETS_UPLOAD_FOLDER = os.environ.get("ROYALTREE_ASSET_UPLOAD_DIR", "uploaded_assets")
os.makedirs(ASSETS_UPLOAD_FOLDER, exist_ok=True)


# --- Utility Functions ---

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hash_: str) -> bool:
    return hash_password(password) == hash_

def create_access_token(user_id: int) -> str:
    # For demonstration: use a simple token generation (not secure for production as is)
    token = secrets.token_urlsafe(32)
    exp = datetime.utcnow() + timedelta(hours=8)
    conn = get_db_connection()
    conn.execute("INSERT INTO tokens (token, user_id, expires_at) VALUES (?, ?, ?)", (token, user_id, exp.isoformat()))
    conn.commit()
    conn.close()
    return token

def get_user_by_token(token: str) -> Optional[sqlite3.Row]:
    conn = get_db_connection()
    cursor = conn.execute("SELECT users.* FROM users JOIN tokens ON users.id = tokens.user_id WHERE tokens.token=? AND tokens.expires_at > ?",
                          (token, datetime.utcnow().isoformat()))
    user = cursor.fetchone()
    conn.close()
    return user

def require_role(role: str):
    def dependency(token: str = Query(..., description="Access token for authentication (query param: token)")):
        user = get_user_by_token(token)
        if not user or user["role"] != role:
            raise HTTPException(status_code=401, detail="Unauthorized or insufficient permissions")
        return user
    return dependency

def require_any_role(roles: List[str]):
    def dependency(token: str = Query(..., description="Access token for authentication (query param: token)")):
        user = get_user_by_token(token)
        if not user or user["role"] not in roles:
            raise HTTPException(status_code=401, detail="Unauthorized or insufficient permissions")
        return user
    return dependency

def require_admin(token: str = Query(..., description="Access token for authentication")):
    user = get_user_by_token(token)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=401, detail="Admin access required")
    return user

# --- Data Models ---

# PUBLIC_INTERFACE
class UserBase(BaseModel):
    username: str = Field(..., description="Unique username")
    email: EmailStr
    role: str = Field(..., description="Role: creator, investor, or admin")

# PUBLIC_INTERFACE
class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

# PUBLIC_INTERFACE
class UserPublic(UserBase):
    id: int

    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class AssetBase(BaseModel):
    title: str = Field(..., description="Title/name of the digital asset")
    description: Optional[str] = Field("", description="Description of the asset")
    category: Optional[str] = Field("", description="Asset category (music, book, art, etc.)")
    total_shares: int = Field(..., gt=0, description="Total shares for fractional ownership")
    price_per_share: float = Field(..., description="Price per share (in USD)")
    royalty_percent: float = Field(..., ge=0, le=100, description="Royalty percent for investors (0-100)")

# PUBLIC_INTERFACE
class AssetCreate(AssetBase):
    file: Optional[UploadFile] = None

# PUBLIC_INTERFACE
class AssetUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    category: Optional[str]
    total_shares: Optional[int]
    price_per_share: Optional[float]
    royalty_percent: Optional[float]

# PUBLIC_INTERFACE
class AssetPublic(AssetBase):
    id: int
    creator_id: int
    status: str
    file_url: Optional[str]
    shares_available: int
    shares_sold: int
    earnings_total: float
    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class TransactionBase(BaseModel):
    asset_id: int
    shares: int = Field(..., gt=0)
    type: str = Field(..., description="buy or sell")
    price: float

# PUBLIC_INTERFACE
class TransactionCreate(BaseModel):
    asset_id: int
    shares: int = Field(..., gt=0)
    type: str
    price: float

# PUBLIC_INTERFACE
class TransactionPublic(TransactionBase):
    id: int
    user_id: int
    timestamp: str

# PUBLIC_INTERFACE
class RoyaltyReceipt(BaseModel):
    asset_id: int
    amount: float
    timestamp: str

# PUBLIC_INTERFACE
class DashboardSummary(BaseModel):
    owned_assets: List[AssetPublic]
    earnings_total: float
    royalties_received: float
    invested_assets: List[dict] = []  # for investors: asset, shares_owned, earnings

# --- Startup: DB Setup ---
def initialize_db():
    conn = get_db_connection()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password_hash TEXT,
        role TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS tokens (
        id INTEGER PRIMARY KEY,
        token TEXT UNIQUE,
        user_id INTEGER,
        expires_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )""")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY,
        title TEXT,
        description TEXT,
        category TEXT,
        file_path TEXT,
        creator_id INTEGER,
        status TEXT, -- pending/approved/rejected
        total_shares INTEGER,
        price_per_share REAL,
        royalty_percent REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (creator_id) REFERENCES users(id)
    )""")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS shares (
        id INTEGER PRIMARY KEY,
        asset_id INTEGER,
        owner_id INTEGER,
        shares INTEGER,
        buy_price REAL,
        FOREIGN KEY (asset_id) REFERENCES assets(id),
        FOREIGN KEY (owner_id) REFERENCES users(id)
    )""")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY,
        asset_id INTEGER,
        user_id INTEGER,
        shares INTEGER,
        type TEXT, -- buy/sell/royalty
        price REAL,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (asset_id) REFERENCES assets(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )""")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS disputes (
        id INTEGER PRIMARY KEY,
        asset_id INTEGER,
        user_id INTEGER,
        reason TEXT,
        status TEXT, -- open, resolved
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    conn.close()

@app.on_event("startup")
def on_startup():
    initialize_db()

# --- Public Endpoints ---

@app.options("/{full_path:path}", tags=["public"])
async def options_handler(full_path: str):
    """
    PUBLIC_INTERFACE
    CORS preflight handler for diagnostic. Ensures all OPTIONS requests receive a valid 200 OK response.
    """
    return JSONResponse({"ok": True})

@app.get("/", tags=["public"])
def landing_info():
    """
    PUBLIC_INTERFACE
    Landing page (API level): Returns platform information, main routes, and summary.
    """
    return {
        "platform": "Royaltree",
        "description": "Digital content platform for fractional ownership, investment, and royalties.",
        "main_routes": [
            "/auth/register", "/auth/login",
            "/creator/assets", "/investor/marketplace", "/assets/{id}",
            "/transactions", "/dashboard", "/admin/panel",
            "/health/db"
        ]
    }

@app.get("/health/db", tags=["public"], summary="Database health check", description="Health check endpoint for the SQLite DB connection. Returns {'status': 'healthy'} if DB reachable, {'status': 'unhealthy'} with error otherwise.", response_model=dict)
def db_health_check():
    """
    PUBLIC_INTERFACE
    Health check endpoint for the SQLite database. Attempts a simple query to verify connection.
    Returns {"status": "healthy"} if DB is reachable and working, otherwise returns {"status": "unhealthy", "detail": "...error..."}
    """
    try:
        conn = get_db_connection()
        # Attempt a trivial query to ensure DB is accessible
        conn.execute("SELECT 1")
        conn.close()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "detail": str(e)}

# --- Auth Endpoints ---

@app.post(
    "/auth/register",
    tags=["auth"],
    response_model=UserPublic,
    status_code=201,
    summary="Register a new user (creator/investor/admin)",
    description=(
        "Register a new user (creator, investor, or admin).\n"
        "**Accepts:** application/json ONLY.<br/>\n"
        "**Request body:** Must be a flat object matching UserCreate fields: `{ \"username\": ..., \"email\": ..., \"role\": ..., \"password\": ... }`<br/>"
        "- No 'user_json' key, stringified JSON, or nested object—just flat JSON.<br/>"
        "**Content-Type application/json is required.**"
        "<br/><br/>Returns the registered user (public view) on success.<br/>\n"
        "HTTP 409 if username/email exists. HTTP 400 if fields are missing/invalid. HTTP 415 for wrong Content-Type.\n"
        "\n**Example:**\n"
        "```json\n"
        "{\n  \"username\": \"johnny\",\n  \"email\": \"johnny@example.com\",\n  \"role\": \"creator\",\n  \"password\": \"supersecret\"\n}\n"
        "```"
    ),
    responses={
        201: {"description": "User registered successfully", "model": UserPublic},
        409: {"description": "Username or email already exists"},
        400: {"description": "Invalid role or data"},
        415: {"description": "Unsupported Media Type - Only application/json accepted"},
    }
)
# PUBLIC_INTERFACE
async def register(user: UserCreate, request: Request):
    """
    PUBLIC_INTERFACE
    Register a new user.

    Request:
        - Content-Type: application/json
        - Body: { "username": str, "email": str, "role": "creator|investor|admin", "password": str }

    Returns:
        UserPublic (id, username, email, role) — HTTP 201

    Errors:
      - 409: username or email exists
      - 400: invalid role or schema
      - 415: content-type not application/json

    NOTE:
      - Only flat JSON is accepted. No 'user_json', no multipart, no form fields.
    """
    print("DEBUG: Incoming /auth/register request", flush=True)
    if request.headers.get("content-type", "").split(";")[0].lower() != "application/json":
        print("DEBUG: Content-Type failure on /auth/register", flush=True)
        raise HTTPException(
            status_code=415, detail="Content-Type must be application/json"
        )
    if user.role not in ("creator", "investor", "admin"):
        print("DEBUG: Invalid role on /auth/register", flush=True)
        raise HTTPException(status_code=400, detail="Invalid role")
    conn = get_db_connection()
    if conn.execute(
        "SELECT id FROM users WHERE username=? or email=?", (user.username, user.email)
    ).fetchone():
        conn.close()
        print("DEBUG: Duplicate user/email on /auth/register", flush=True)
        raise HTTPException(status_code=409, detail="Username or email already exists")
    hash_ = hash_password(user.password)
    cur = conn.execute(
        "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
        (user.username, user.email, hash_, user.role)
    )
    uid = cur.lastrowid
    conn.commit()
    conn.close()
    print(f"DEBUG: Registered user {user.username} (id={uid})", flush=True)
    return UserPublic(id=uid, username=user.username, email=user.email, role=user.role)

@app.post("/auth/login", tags=["auth"])
def login(form: OAuth2PasswordRequestForm = Depends()):
    """
    PUBLIC_INTERFACE
    Login endpoint: returns a token for authenticated access.
    """
    print("DEBUG: Incoming /auth/login request", flush=True)
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM users WHERE username=?", (form.username,))
    user = cursor.fetchone()
    conn.close()
    if not user or not verify_password(form.password, user["password_hash"]):
        print("DEBUG: Invalid credentials on /auth/login", flush=True)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user["id"])
    print(f"DEBUG: Successful login for user {form.username} (id={user['id']})", flush=True)
    return {"access_token": token, "token_type": "bearer"}

# --- Creator Endpoints ---

@app.post("/creator/assets", tags=["creator"], response_model=AssetPublic)
def upload_asset(
    title: str = Form(...),
    description: str = Form(""),
    category: str = Form(""),
    total_shares: int = Form(..., gt=0),
    price_per_share: float = Form(..., gt=0),
    royalty_percent: float = Form(..., ge=0, le=100),
    file: UploadFile = File(...),
    user=Depends(require_role("creator"))
):
    """
    PUBLIC_INTERFACE
    Creator uploads a digital asset for approval/fractional sale.
    """
    file_location = os.path.join(ASSETS_UPLOAD_FOLDER, f"{secrets.token_hex(8)}_{file.filename}")
    with open(file_location, "wb") as f:
        content = file.file.read()
        f.write(content)
    file_url = file_location  # In production, return a URL endpoint for serving

    conn = get_db_connection()
    cur = conn.execute(
        "INSERT INTO assets (title, description, category, file_path, creator_id, status, total_shares, price_per_share, royalty_percent) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?)",
        (title, description, category, file_url, user["id"], total_shares, price_per_share, royalty_percent)
    )
    asset_id = cur.lastrowid
    conn.commit()
    asset = conn.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()
    conn.close()
    return _asset_row_to_pub(asset)

@app.get("/creator/assets", tags=["creator"], response_model=List[AssetPublic])
def creator_assets(user=Depends(require_role("creator"))):
    """
    PUBLIC_INTERFACE
    List all assets uploaded by the creator.
    """
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM assets WHERE creator_id=?", (user["id"],)).fetchall()
    conn.close()
    return [_asset_row_to_pub(row) for row in rows]

@app.get("/creator/earnings", tags=["creator"])
def creator_earnings(user=Depends(require_role("creator"))):
    """
    PUBLIC_INTERFACE
    Track creator's earnings from their approved assets (summed royalties and sales).
    """
    conn = get_db_connection()
    result = conn.execute(
        "SELECT SUM(price_per_share * total_shares) as gross, "
        "SUM((SELECT COALESCE(SUM(price),0) FROM transactions WHERE asset_id=assets.id AND type='royalty')) as royalties "
        "FROM assets WHERE creator_id=? AND status='approved'",
        (user["id"],)
    ).fetchone()
    conn.close()
    return {"total_sales": result["gross"] or 0, "total_royalties": result["royalties"] or 0}

# --- Investor Endpoints ---

@app.get("/investor/marketplace", tags=["investor"], response_model=List[AssetPublic])
def list_marketplace_assets(user=Depends(require_role("investor"))):
    """
    PUBLIC_INTERFACE
    Get all approved assets available for fractional purchase.
    """
    conn = get_db_connection()
    assets = conn.execute("SELECT * FROM assets WHERE status = 'approved'").fetchall()
    result = []
    for row in assets:
        asset = _asset_row_to_pub(row)
        asset["shares_available"] = _get_asset_available_shares(row["id"])
        asset["shares_sold"] = row["total_shares"] - asset["shares_available"]
        # Optionally omit file_url here for preview
        result.append(asset)
    conn.close()
    return result

@app.post("/investor/assets/buy", tags=["investor"])
def purchase_shares(asset_id: int = Form(...), shares: int = Form(..., gt=0), user=Depends(require_role("investor"))):
    """
    PUBLIC_INTERFACE
    Investor buys shares of an asset.
    """
    conn = get_db_connection()
    asset = conn.execute("SELECT * FROM assets WHERE id=? AND status='approved'", (asset_id,)).fetchone()
    if not asset:
        conn.close()
        raise HTTPException(status_code=404, detail="Asset not found or not approved")
    available = _get_asset_available_shares(asset_id)
    if shares > available:
        conn.close()
        raise HTTPException(status_code=400, detail="Not enough shares available")
    price = shares * asset["price_per_share"]
    # Insert share record
    conn.execute("INSERT INTO shares (asset_id, owner_id, shares, buy_price) VALUES (?, ?, ?, ?)", (asset_id, user["id"], shares, price))
    # Insert transaction
    conn.execute("INSERT INTO transactions (asset_id, user_id, shares, type, price) VALUES (?, ?, ?, 'buy', ?)",
                 (asset_id, user["id"], shares, price))
    conn.commit()
    conn.close()
    return {"status": "success", "shares_bought": shares, "total_price": price}

@app.get("/investor/assets", tags=["investor"])
def investor_assets(user=Depends(require_role("investor"))):
    """
    PUBLIC_INTERFACE
    Investor's assets and shares/earnings dashboard.
    """
    conn = get_db_connection()
    rows = conn.execute("SELECT assets.*, SUM(shares.shares) as owned FROM shares "
                        "JOIN assets ON assets.id = shares.asset_id "
                        "WHERE shares.owner_id=? GROUP BY assets.id", (user["id"],)).fetchall()
    result = []
    for row in rows:
        asset_pub = _asset_row_to_pub(row)
        # get earning for their share
        earnings = _get_investor_asset_earnings(row["id"], user["id"])
        asset_pub["investor_earnings"] = earnings
        asset_pub["shares_owned"] = row["owned"]
        result.append(asset_pub)
    conn.close()
    return result

@app.get("/investor/earnings", tags=["investor"])
def investor_earnings(user=Depends(require_role("investor"))):
    """
    PUBLIC_INTERFACE
    Sum all royalties and realized gains for investor.
    """
    conn = get_db_connection()
    total_royalties = conn.execute("SELECT SUM(price) FROM transactions WHERE user_id=? AND type='royalty'", (user["id"],)).fetchone()[0] or 0
    total_gains = conn.execute("SELECT SUM(price) FROM transactions WHERE user_id=? AND type='sell'", (user["id"],)).fetchone()[0] or 0
    conn.close()
    return {"total_royalties": total_royalties, "total_gains": total_gains}

# --- Asset Endpoints ---

@app.get("/assets/{asset_id}", tags=["assets"], response_model=AssetPublic)
def get_asset_detail(asset_id: int, token: Optional[str] = Query(None)):
    """
    PUBLIC_INTERFACE
    Get asset metadata, availability, and earnings summary. File access may require authentication.
    """
    conn = get_db_connection()
    asset = conn.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()
    if not asset:
        conn.close()
        raise HTTPException(status_code=404, detail="Asset not found")
    asset_pub = _asset_row_to_pub(asset)
    conn.close()
    return asset_pub

@app.get("/assets/{asset_id}/download", tags=["assets"])
def download_asset(asset_id: int, token: str = Query(...)):
    """
    PUBLIC_INTERFACE
    Download asset file (if authorized as owner or admin).
    """
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    conn = get_db_connection()
    asset = conn.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()
    if not asset:
        conn.close()
        raise HTTPException(status_code=404, detail="Asset not found")
    if user["id"] != asset["creator_id"] and user["role"] != "admin":
        # Must own shares to access (or be creator/admin)
        shares = conn.execute("SELECT SUM(shares) FROM shares WHERE asset_id=? AND owner_id=?", (asset_id, user["id"])).fetchone()[0] or 0
        if not shares:
            conn.close()
            raise HTTPException(status_code=403, detail="Access denied: not a shareholder or admin/creator.")
    conn.close()
    return FileResponse(asset["file_path"], filename=os.path.basename(asset["file_path"]))

# --- Asset Management - Admin Approvals ---

@app.get("/admin/assets/pending", tags=["admin"])
def admin_pending_assets(user=Depends(require_admin)):
    """
    PUBLIC_INTERFACE
    Admin lists all pending assets for approval.
    """
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM assets WHERE status='pending'").fetchall()
    conn.close()
    return [_asset_row_to_pub(row) for row in rows]

@app.post("/admin/assets/{asset_id}/status", tags=["admin"])
def admin_update_asset(asset_id: int, asset_status: str = Form(...), user=Depends(require_admin)):
    """
    PUBLIC_INTERFACE
    Admin approves or rejects assets.
    """
    if asset_status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Invalid status")
    conn = get_db_connection()
    asset = conn.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()
    if not asset:
        conn.close()
        raise HTTPException(status_code=404, detail="Asset not found")
    conn.execute("UPDATE assets SET status=? WHERE id=?", (asset_status, asset_id))
    conn.commit()
    conn.close()
    return {"asset_id": asset_id, "new_status": asset_status}


# --- Transactions Endpoints ---

@app.get("/transactions", tags=["transactions"])
def list_transactions(token: str = Query(...)):
    """
    PUBLIC_INTERFACE
    List all transactions (buy, sell, royalty) for the authenticated user.
    """
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY timestamp DESC", (user["id"],)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/transactions/royalty", tags=["admin"])
def simulate_royalty(asset_id: int = Form(...), amount: float = Form(...), user=Depends(require_admin)):
    """
    PUBLIC_INTERFACE
    Admin simulates a royalty payout for an asset.
    """
    conn = get_db_connection()
    asset = conn.execute("SELECT * FROM assets WHERE id=? AND status='approved'", (asset_id,)).fetchone()
    if not asset:
        conn.close()
        raise HTTPException(status_code=404, detail="Asset not found or not approved")
    # Distribute royalty according to shares
    rows = conn.execute("SELECT owner_id, SUM(shares) as owned FROM shares WHERE asset_id=? GROUP BY owner_id", (asset_id,)).fetchall()
    if not rows:
        conn.close()
        return {"distributed": 0, "note": "No shareholders for this asset"}
    total_shares = asset["total_shares"]
    for row in rows:
        pay = round(amount * (row["owned"] / total_shares), 2)
        conn.execute("INSERT INTO transactions (asset_id, user_id, shares, type, price) VALUES (?, ?, ?, 'royalty', ?)",
                     (asset_id, row["owner_id"], row["owned"], pay))
    conn.commit()
    conn.close()
    return {"status": "royalty distributed", "shareholders": len(rows)}

# --- Admin Panel: Dispute/Moderation ---

@app.get("/admin/panel/disputes", tags=["admin"])
def list_disputes(user=Depends(require_admin)):
    """
    PUBLIC_INTERFACE
    List all open disputes.
    """
    conn = get_db_connection()
    disputes = conn.execute("SELECT * FROM disputes WHERE status='open'").fetchall()
    conn.close()
    return [dict(row) for row in disputes]

@app.post("/admin/panel/disputes/resolve", tags=["admin"])
def resolve_dispute(dispute_id: int = Form(...), resolution: str = Form(...), user=Depends(require_admin)):
    """
    PUBLIC_INTERFACE
    Resolve a dispute and close it.
    """
    conn = get_db_connection()
    dispute = conn.execute("SELECT * FROM disputes WHERE id=?", (dispute_id,)).fetchone()
    if not dispute:
        conn.close()
        raise HTTPException(status_code=404, detail="Dispute not found")
    conn.execute("UPDATE disputes SET status='resolved' WHERE id=?", (dispute_id,))
    conn.commit()
    conn.close()
    return {"status": "resolved", "dispute_id": dispute_id, "resolution": resolution}

@app.post("/assets/{asset_id}/dispute", tags=["assets"])
def submit_dispute(asset_id: int, reason: str = Form(...), token: str = Query(...)):
    """
    PUBLIC_INTERFACE
    Submit a dispute regarding an asset.
    """
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    conn = get_db_connection()
    conn.execute("INSERT INTO disputes (asset_id, user_id, reason, status) VALUES (?, ?, ?, 'open')",
                 (asset_id, user["id"], reason))
    conn.commit()
    conn.close()
    return {"status": "submitted", "asset_id": asset_id}

# --- Dashboard Endpoints ---

@app.get("/dashboard", tags=["dashboard"])
def dashboard_summary(token: str = Query(...)):
    """
    PUBLIC_INTERFACE
    Aggregated dashboard: earnings, assets owned, investments, total royalties for creators/investors.
    """
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    if user["role"] == "creator":
        # Show creator asset/earning summary
        conn = get_db_connection()
        arows = conn.execute("SELECT * FROM assets WHERE creator_id=?", (user["id"],)).fetchall()
        owned_assets = [_asset_row_to_pub(row) for row in arows]
        earnings = sum([_get_asset_creator_earnings(row["id"]) for row in arows])
        royalties = conn.execute("SELECT SUM(price) FROM transactions WHERE type='royalty' AND asset_id IN (SELECT id FROM assets WHERE creator_id=?)",
                                 (user["id"],)).fetchone()[0] or 0
        conn.close()
        return {"role": "creator", "owned_assets": owned_assets, "earnings_total": earnings, "royalties_received": royalties}
    else:
        # investor
        conn = get_db_connection()
        irows = conn.execute("SELECT assets.*, SUM(shares.shares) as n_shares FROM shares "
                             "JOIN assets ON assets.id = shares.asset_id "
                             "WHERE shares.owner_id=? GROUP BY assets.id", (user["id"],)).fetchall()
        invested_assets = []
        for row in irows:
            earnings = _get_investor_asset_earnings(row["id"], user["id"])
            invested_assets.append({
                **_asset_row_to_pub(row),
                "shares_owned": row["n_shares"] or 0,
                "earnings": earnings
            })
        royalties = conn.execute("SELECT SUM(price) FROM transactions WHERE type='royalty' AND user_id=?", (user["id"],)).fetchone()[0] or 0
        earnings = conn.execute("SELECT SUM(price) FROM transactions WHERE type='sell' AND user_id=?", (user["id"],)).fetchone()[0] or 0
        conn.close()
        return {"role": "investor", "invested_assets": invested_assets, "earnings_total": earnings, "royalties_received": royalties}

# --- Helper Functions ---

def _asset_row_to_pub(row: Union[sqlite3.Row, dict]) -> dict:
    # Make API-friendly asset object
    base = {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "category": row["category"],
        "total_shares": row["total_shares"],
        "price_per_share": row["price_per_share"],
        "royalty_percent": row["royalty_percent"],
        "creator_id": row["creator_id"],
        "status": row["status"],
        "file_url": row.get("file_path") if "file_path" in row.keys() else None,
    }
    base["shares_available"] = _get_asset_available_shares(row["id"])
    base["shares_sold"] = base["total_shares"] - base["shares_available"]
    base["earnings_total"] = _get_asset_creator_earnings(row["id"])
    return base

def _get_asset_available_shares(asset_id: int) -> int:
    conn = get_db_connection()
    asset = conn.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()
    result = conn.execute("SELECT SUM(shares) FROM shares WHERE asset_id=?", (asset_id,)).fetchone()
    used = result[0] if result and result[0] else 0
    conn.close()
    available = asset["total_shares"] - used
    return available

def _get_asset_creator_earnings(asset_id: int) -> float:
    conn = get_db_connection()
    earnings = conn.execute("SELECT SUM(price) FROM transactions WHERE asset_id=? AND type='buy'", (asset_id,)).fetchone()[0]
    conn.close()
    return earnings or 0.0

def _get_investor_asset_earnings(asset_id: int, user_id: int) -> float:
    conn = get_db_connection()
    royalties = conn.execute("SELECT SUM(price) FROM transactions WHERE asset_id=? AND user_id=? AND type='royalty'", (asset_id, user_id)).fetchone()[0] or 0
    sell = conn.execute("SELECT SUM(price) FROM transactions WHERE asset_id=? AND user_id=? AND type='sell'", (asset_id, user_id)).fetchone()[0] or 0
    conn.close()
    return (royalties or 0) + (sell or 0)

# --- End of Implementation ---

# OpenAPI summary routes
@app.get("/docs/websocket-usage", tags=["public"])
def websocket_usage_help():
    """Docs/help endpoint for real-time/websocket (future use in platform)."""
    return {
        "note": "WebSocket endpoints not implemented; for real-time updates, polling API routes is recommended."
    }
