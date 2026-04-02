from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import sqlite3
import os

app = FastAPI(title="GameShop API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SQLite Database
DB_PATH = os.getenv("DATABASE_PATH", "/var/www/gameshop/data/gameshop.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            game TEXT NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            original_price REAL,
            description TEXT,
            featured INTEGER DEFAULT 0,
            in_stock INTEGER DEFAULT 1,
            image TEXT
        )
    ''')
    
    # Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            product_id TEXT NOT NULL,
            game TEXT NOT NULL,
            player_id TEXT NOT NULL,
            server TEXT,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            payment_method TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            username TEXT,
            balance REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize DB on startup
@app.on_event("startup")
async def startup():
    init_db()
    init_sample_products()

def init_sample_products():
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if products exist
    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    
    if count == 0:
        sample_products = [
            # MLBB Products
            (str(uuid.uuid4()), "mlbb", "50 + 5 Diamonds", 1.29, 1.49, "50 Diamonds + 5 Bonus", 1, 1, None),
            (str(uuid.uuid4()), "mlbb", "100 + 10 Diamonds", 2.49, 2.99, "100 Diamonds + 10 Bonus", 0, 1, None),
            (str(uuid.uuid4()), "mlbb", "500 + 50 Diamonds", 9.99, 12.99, "500 Diamonds + 50 Bonus", 1, 1, None),
            (str(uuid.uuid4()), "mlbb", "Starlight Member", 4.99, None, "1 Month Starlight Pass", 1, 1, None),
            (str(uuid.uuid4()), "mlbb", "Weekly Diamond Pass", 1.99, None, "Weekly Diamond Pass", 0, 1, None),
            # PUBG Products
            (str(uuid.uuid4()), "pubg", "60 UC", 0.99, None, "60 Unknown Cash", 0, 1, None),
            (str(uuid.uuid4()), "pubg", "325 UC", 4.99, None, "325 Unknown Cash", 1, 1, None),
            (str(uuid.uuid4()), "pubg", "660 UC", 9.99, None, "660 Unknown Cash", 0, 1, None),
            (str(uuid.uuid4()), "pubg", "Royal Pass", 9.99, None, "Premium Royal Pass", 1, 1, None),
            # Free Fire Products
            (str(uuid.uuid4()), "freefire", "100 Diamonds", 0.99, None, "100 Diamonds", 0, 1, None),
            (str(uuid.uuid4()), "freefire", "500 Diamonds", 4.99, None, "500 Diamonds", 1, 1, None),
            (str(uuid.uuid4()), "freefire", "1000 Diamonds", 9.99, None, "1000 Diamonds", 0, 1, None),
            # Valorant Products
            (str(uuid.uuid4()), "valorant", "475 VP", 4.99, None, "475 Valorant Points", 0, 1, None),
            (str(uuid.uuid4()), "valorant", "1000 VP", 9.99, None, "1000 Valorant Points", 1, 1, None),
            (str(uuid.uuid4()), "valorant", "2050 VP", 19.99, None, "2050 Valorant Points", 1, 1, None),
        ]
        
        cursor.executemany(
            "INSERT INTO products (id, game, name, price, original_price, description, featured, in_stock, image) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            sample_products
        )
        conn.commit()
        print(f"Initialized {len(sample_products)} sample products")
    
    conn.close()

# Models
class Product(BaseModel):
    id: str
    game: str
    name: str
    price: float
    original_price: Optional[float] = None
    description: str
    featured: bool = False
    in_stock: bool = True

class Order(BaseModel):
    id: str
    user_id: Optional[str]
    product_id: str
    game: str
    player_id: str
    server: Optional[str] = None
    amount: float
    status: str = "pending"
    payment_method: Optional[str] = None
    created_at: datetime = datetime.utcnow()

# Endpoints
@app.get("/api/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/games")
async def get_games():
    return [
        {"id": "mlbb", "name": "Mobile Legends", "icon": "🎮", "color": "#00F0FF"},
        {"id": "pubg", "name": "PUBG Mobile", "icon": "🔫", "color": "#FF6B3D"},
        {"id": "freefire", "name": "Free Fire", "icon": "🔥", "color": "#A855F7"},
        {"id": "valorant", "name": "Valorant", "icon": "🎯", "color": "#FF4655"},
    ]

@app.get("/api/products")
async def get_products(game: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor()
    
    if game:
        cursor.execute("SELECT * FROM products WHERE game = ?", (game,))
    else:
        cursor.execute("SELECT * FROM products")
    
    rows = cursor.fetchall()
    conn.close()
    
    products = []
    for row in rows:
        products.append({
            "id": row["id"],
            "game": row["game"],
            "name": row["name"],
            "price": row["price"],
            "original_price": row["original_price"],
            "description": row["description"],
            "featured": bool(row["featured"]),
            "in_stock": bool(row["in_stock"])
        })
    
    return products

@app.get("/api/products/featured")
async def get_featured():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE featured = 1")
    rows = cursor.fetchall()
    conn.close()
    
    products = []
    for row in rows:
        products.append({
            "id": row["id"],
            "game": row["game"],
            "name": row["name"],
            "price": row["price"],
            "original_price": row["original_price"],
            "description": row["description"],
            "featured": True,
            "in_stock": bool(row["in_stock"])
        })
    
    return products

@app.get("/api/products/{product_id}")
async def get_product(product_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "id": row["id"],
        "game": row["game"],
        "name": row["name"],
        "price": row["price"],
        "original_price": row["original_price"],
        "description": row["description"],
        "featured": bool(row["featured"]),
        "in_stock": bool(row["in_stock"])
    }

@app.post("/api/orders")
async def create_order(order: dict):
    conn = get_db()
    cursor = conn.cursor()
    
    order_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    
    cursor.execute('''
        INSERT INTO orders (id, user_id, product_id, game, player_id, server, amount, status, payment_method, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        order_id,
        order.get("user_id"),
        order.get("product_id"),
        order.get("game"),
        order.get("player_id"),
        order.get("server"),
        order.get("amount"),
        "pending",
        order.get("payment_method"),
        created_at
    ))
    
    conn.commit()
    conn.close()
    
    return {"order_id": order_id, "status": "pending", "created_at": created_at}

@app.get("/api/orders/{user_id}")
async def get_user_orders(user_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    orders = []
    for row in rows:
        orders.append({
            "id": row["id"],
            "user_id": row["user_id"],
            "product_id": row["product_id"],
            "game": row["game"],
            "player_id": row["player_id"],
            "server": row["server"],
            "amount": row["amount"],
            "status": row["status"],
            "payment_method": row["payment_method"],
            "created_at": row["created_at"]
        })
    
    return orders

@app.post("/api/users")
async def create_user(user: dict):
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE email = ?", (user.get("email"),))
    existing = cursor.fetchone()
    
    if existing:
        conn.close()
        return {
            "id": existing["id"],
            "email": existing["email"],
            "username": existing["username"],
            "balance": existing["balance"],
            "created_at": existing["created_at"]
        }
    
    # Create new user
    user_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    
    cursor.execute('''
        INSERT INTO users (id, email, username, balance, created_at)
        VALUES (?, ?, ?, 0.0, ?)
    ''', (user_id, user.get("email"), user.get("username"), created_at))
    
    conn.commit()
    conn.close()
    
    return {
        "id": user_id,
        "email": user.get("email"),
        "username": user.get("username"),
        "balance": 0.0,
        "created_at": created_at
    }

@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": row["id"],
        "email": row["email"],
        "username": row["username"],
        "balance": row["balance"],
        "created_at": row["created_at"]
    }

# Player profile check models
class PlayerCheck(BaseModel):
    game: str
    player_id: str
    server: Optional[str] = None

# Check player profile (for account verification)
@app.post("/api/check-player")
async def check_player(data: PlayerCheck):
    """
    Check player profile for various games.
    Returns player name, level, and other info for verification.
    """
    import httpx
    import hashlib
    
    game = data.game.lower()
    player_id = data.player_id.strip()
    server = data.server.strip() if data.server else None
    
    # Mobile Legends API
    if game == "mlbb":
        try:
            # MLBB requires server ID (zone)
            if not server:
                return {"success": False, "error": "Server ID required for Mobile Legends"}
            
            # CodaShop API proxy (commonly used for game top-ups)
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try MLBB official API or third-party validation
                response = await client.get(
                    f"https://api.dovidingue21.workers.dev/mlbb",
                    params={"id": player_id, "zone": server}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        return {
                            "success": True,
                            "player": {
                                "name": data.get("username", f"Player_{player_id[-4:]}"),
                                "level": data.get("level", "?"),
                                "rank": data.get("rank", "?"),
                                "avatar": "🎮"
                            }
                        }
        except Exception as e:
            print(f"MLBB API error: {e}")
    
    # PUBG Mobile
    elif game == "pubg":
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://api.dovidingue21.workers.dev/pubg",
                    params={"id": player_id}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        return {
                            "success": True,
                            "player": {
                                "name": data.get("username", f"Player_{player_id[-4:]}"),
                                "level": data.get("level", "?"),
                                "rank": data.get("rank", "?"),
                                "avatar": "🔫"
                            }
                        }
        except Exception as e:
            print(f"PUBG API error: {e}")
    
    # Free Fire
    elif game == "freefire":
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://api.dovidingue21.workers.dev/freefire",
                    params={"id": player_id, "region": server or "global"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        return {
                            "success": True,
                            "player": {
                                "name": data.get("username", f"Player_{player_id[-4:]}"),
                                "level": data.get("level", "?"),
                                "rank": data.get("rank", "?"),
                                "avatar": "🔥"
                            }
                        }
        except Exception as e:
            print(f"Free Fire API error: {e}")
    
    # Valorant
    elif game == "valorant":
        # Valorant uses Riot ID (Name#Tag)
        try:
            if "#" in player_id:
                name, tag = player_id.split("#")
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        f"https://api.henrikdev.xyz/valorant/v1/account/{name}/{tag}"
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("status") == 200:
                            acc = data.get("data", {})
                            return {
                                "success": True,
                                "player": {
                                    "name": acc.get("name", player_id),
                                    "level": acc.get("account_level", "?"),
                                    "rank": acc.get("rank", "?"),
                                    "avatar": "🎯"
                                }
                            }
        except Exception as e:
            print(f"Valorant API error: {e}")
    
    # Fallback: Return mock data for demo
    # In production, replace with actual API calls
    game_avatars = {
        "mlbb": "🎮",
        "pubg": "🔫",
        "freefire": "🔥",
        "valorant": "🎯"
    }
    
    game_ranks = {
        "mlbb": ["Warrior", "Elite", "Master", "Grandmaster", "Epic", "Legend", "Mythic"],
        "pubg": ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Crown", "Ace", "Conqueror"],
        "freefire": ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Heroic"],
        "valorant": ["Iron", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Ascendant", "Immortal", "Radiant"]
    }
    
    import random
    
    return {
        "success": True,
        "player": {
            "name": f"Player_{player_id[-4:]}",
            "level": random.randint(10, 65),
            "rank": random.choice(game_ranks.get(game, ["Player"])),
            "avatar": game_avatars.get(game, "🎮")
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3002)