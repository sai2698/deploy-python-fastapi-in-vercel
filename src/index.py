# from fastapi import FastAPI, HTTPException, Depends, Request
# from fastapi.responses import HTMLResponse
# from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates
# from motor.motor_asyncio import AsyncIOMotorClient
# from pydantic import BaseModel,HttpUrl
# from typing import List, Dict, Any, Optional
# from fastapi.middleware.cors import CORSMiddleware

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Or better: [ "https://*.github.dev" ]
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Serve static files (if needed)
# app.mount("/static", StaticFiles(directory="static"), name="static")

# # Configure templates
# templates = Jinja2Templates(directory="templates")

# # MongoDB Configuration
# MONGODB_URI = "mongodb+srv://naveendevarapalli99:Naveen123@cluster0.jmg62pd.mongodb.net/"
# DB_NAME = "ott"
# COLLECTION_NAME = "catalogue"

# async def get_database():
#     if not MONGODB_URI:
#         raise HTTPException(status_code=500, detail="MongoDB URI not configured")
#     client = AsyncIOMotorClient(MONGODB_URI)
#     try:
#         db = client[DB_NAME]
#         yield db
#     finally:
#         client.close()

# # Catalogue Item Model
# class CatalogueItem(BaseModel):
#     id: str
#     title: str
#     genre: List[str]
#     year: str
#     thumbnail: str
#     description: str
#     url: Optional[str] = ""

# # Serve the HTML templates
# @app.get("/", response_class=HTMLResponse)
# async def home(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})

# @app.get("/add", response_class=HTMLResponse)
# async def add_page(request: Request):
#     return templates.TemplateResponse("add.html", {"request": request})

# @app.get("/home", response_class=HTMLResponse)
# async def home(request: Request,db=Depends(get_database)):
#     collection = db[COLLECTION_NAME]
#     cursor = collection.find({})
#     documents = await cursor.to_list(length=None)
#     for doc in documents:
#         if "_id" in doc:
#             doc["_id"] = str(doc["_id"])
#     return templates.TemplateResponse("home.html", {"request": request, "movies": documents[::-1]})

# @app.get("/watch/{movie_id}", response_class=HTMLResponse)
# async def watch_movie(movie_id: str,request: Request,db=Depends(get_database)):
#     collection = db[COLLECTION_NAME]
#     cursor = collection.find({})
#     movies = await cursor.to_list(length=None)
#     for doc in movies:
#         if "_id" in doc:
#             doc["_id"] = str(doc["_id"])
#     movie = next((m for m in movies if m["id"] == movie_id), None)
#     if not movie:
#         raise HTTPException(status_code=404, detail="Movie not found")
#     return templates.TemplateResponse("watch.html", {"request": request, "movie": movie})


# # API Endpoints
# @app.get("/getall", response_model=List[Dict[str, Any]])
# async def get_all_items(db=Depends(get_database)):
#     collection = db[COLLECTION_NAME]
#     cursor = collection.find({})
#     documents = await cursor.to_list(length=None)
#     for doc in documents:
#         if "_id" in doc:
#             doc["_id"] = str(doc["_id"])
#     return documents[::-1]  # Reverse the array before returning


# @app.post("/add_item", response_model=Dict[str, str])
# async def add_item(item: CatalogueItem, db=Depends(get_database)):
#     try:
#         collection = db[COLLECTION_NAME]
#         result = await collection.insert_one(item.dict())  # Change model_dump() to dict()
#         return {"message": "Item added successfully", "id": str(result.inserted_id)}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @app.delete("/delete/{item_id}", response_model=Dict[str, str])
# async def delete_item(item_id: str, db=Depends(get_database)):
#     collection = db[COLLECTION_NAME]
#     result = await collection.delete_one({"id": item_id})
#     if result.deleted_count == 0:
#         raise HTTPException(status_code=404, detail="Item not found")
#     return {"message": "Item deleted successfully"}

# @app.get("/get/{item_id}", response_model=Dict[str, Any])
# async def get_item(item_id: str, db=Depends(get_database)):
#     collection = db[COLLECTION_NAME]
#     item = await collection.find_one({"id": item_id})
#     if not item:
#         raise HTTPException(status_code=404, detail="Item not found")
#     item["_id"] = str(item["_id"])
#     return item

# @app.put("/update/{item_id}", response_model=Dict[str, str])
# async def update_item(item_id: str, updated_item: CatalogueItem, db=Depends(get_database)):
#     collection = db[COLLECTION_NAME]
#     result = await collection.update_one({"id": item_id}, {"$set": updated_item.dict()})
#     if result.matched_count == 0:
#         raise HTTPException(status_code=404, detail="Item not found")
#     return {"message": "Item updated successfully"}


from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta

# ===================== CONFIG =====================
ENABLE_AUTH = False  # 🔴 Set False to disable auth globally

SECRET_KEY = "CHANGE_THIS_SECRET_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 90  # 3 months

# MONGODB_URI = "mongodb+srv://naveendevarapalli99:Naveen123@cluster0.jmg62pd.mongodb.net/"
# DB_NAME = "ott"
# COLLECTION_NAME = "catalogue"

MONGODB_URI = "mongodb+srv://naveendevarapalli99:Naveen123@cluster0.jmg62pd.mongodb.net/"
DB_NAME = "ott"
COLLECTION_NAME = "catalogue"

USERS_COLLECTION = "users"

# =================================================

app = FastAPI()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ===================== DATABASE =====================
async def get_database():
    client = AsyncIOMotorClient(MONGODB_URI)
    try:
        yield client[DB_NAME]
    finally:
        client.close()


# ===================== MODELS =====================
class CatalogueItem(BaseModel):
    id: str
    title: str
    genre: List[str]
    year: str
    thumbnail: str
    description: str
    url: Optional[str] = ""


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    name: str
    token: str


# ===================== AUTH UTILS =====================
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(data: dict):
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


async def authenticate(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_database),
):
    if not ENABLE_AUTH:
        return None

    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db[USERS_COLLECTION].find_one({"username": username})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")


# ===================== LOGIN =====================
@app.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db=Depends(get_database)):
    users = db[USERS_COLLECTION]

    # Auto-create default admin
    admin = await users.find_one({"username": "admin"})
    if not admin:
        await users.insert_one({
            "username": "admin",
            "password": hash_password("admin@123"),
            "name": "Administrator",
            "created_at": datetime.utcnow()
        })

    user = await users.find_one({"username": data.username})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user["username"]})

    return {
        "name": user.get("name", user["username"]),
        "token": token
    }


# ===================== UI ROUTES =====================
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/home", response_class=HTMLResponse)
async def home(request: Request, db=Depends(get_database)):
    collection = db[COLLECTION_NAME]
    docs = await collection.find({}).to_list(None)
    for d in docs:
        d["_id"] = str(d["_id"])
    return templates.TemplateResponse("home.html", {"request": request, "movies": docs[::-1]})


@app.get("/watch/{movie_id}", response_class=HTMLResponse)
async def watch(movie_id: str, request: Request, db=Depends(get_database)):
    collection = db[COLLECTION_NAME]
    movies = await collection.find({}).to_list(None)
    for m in movies:
        m["_id"] = str(m["_id"])
    movie = next((m for m in movies if m["id"] == movie_id), None)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return templates.TemplateResponse("watch.html", {"request": request, "movie": movie})


# ===================== API ROUTES =====================
@app.get("/getall", response_model=List[Dict[str, Any]])
async def get_all_items(
    db=Depends(get_database),
    user=Depends(authenticate)
):
    docs = await db[COLLECTION_NAME].find({}).to_list(None)
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs[::-1]


@app.post("/add_item")
async def add_item(
    item: CatalogueItem,
    db=Depends(get_database),
    user=Depends(authenticate)
):
    await db[COLLECTION_NAME].insert_one(item.dict())
    return {"message": "Item added successfully"}


@app.delete("/delete/{item_id}")
async def delete_item(
    item_id: str,
    db=Depends(get_database),
    user=Depends(authenticate)
):
    result = await db[COLLECTION_NAME].delete_one({"id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted"}


@app.get("/get/{item_id}")
async def get_item(
    item_id: str,
    db=Depends(get_database),
    user=Depends(authenticate)
):
    item = await db[COLLECTION_NAME].find_one({"id": item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item["_id"] = str(item["_id"])
    return item


@app.put("/update/{item_id}")
async def update_item(
    item_id: str,
    updated_item: CatalogueItem,
    db=Depends(get_database),
    user=Depends(authenticate)
):
    result = await db[COLLECTION_NAME].update_one(
        {"id": item_id},
        {"$set": updated_item.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item updated"}

