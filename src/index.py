from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel,HttpUrl
from typing import List, Dict, Any, Optional

app = FastAPI()

# Serve static files (if needed)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure templates
templates = Jinja2Templates(directory="templates")

# MongoDB Configuration
MONGODB_URI = "mongodb+srv://naveendevarapalli99:Naveen123@cluster0.jmg62pd.mongodb.net/"
DB_NAME = "ott"
COLLECTION_NAME = "catalogue"

async def get_database():
    if not MONGODB_URI:
        raise HTTPException(status_code=500, detail="MongoDB URI not configured")
    client = AsyncIOMotorClient(MONGODB_URI)
    try:
        db = client[DB_NAME]
        yield db
    finally:
        client.close()

# Catalogue Item Model
class CatalogueItem(BaseModel):
    id: str
    title: str
    genre: List[str]
    year: str
    thumbnail: str
    description: str
    url: Optional[str] = ""

# Serve the HTML templates
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/add", response_class=HTMLResponse)
async def add_page(request: Request):
    return templates.TemplateResponse("add.html", {"request": request})

# API Endpoints
@app.get("/getall", response_model=List[Dict[str, Any]])
async def get_all_items(db=Depends(get_database)):
    collection = db[COLLECTION_NAME]
    cursor = collection.find({})
    documents = await cursor.to_list(length=None)
    for doc in documents:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
    return documents[::-1]  # Reverse the array before returning


@app.post("/add_item", response_model=Dict[str, str])
async def add_item(item: CatalogueItem, db=Depends(get_database)):
    try:
        collection = db[COLLECTION_NAME]
        result = await collection.insert_one(item.dict())  # Change model_dump() to dict()
        return {"message": "Item added successfully", "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/delete/{item_id}", response_model=Dict[str, str])
async def delete_item(item_id: str, db=Depends(get_database)):
    collection = db[COLLECTION_NAME]
    result = await collection.delete_one({"id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}

@app.get("/get/{item_id}", response_model=Dict[str, Any])
async def get_item(item_id: str, db=Depends(get_database)):
    collection = db[COLLECTION_NAME]
    item = await collection.find_one({"id": item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item["_id"] = str(item["_id"])
    return item

@app.put("/update/{item_id}", response_model=Dict[str, str])
async def update_item(item_id: str, updated_item: CatalogueItem, db=Depends(get_database)):
    collection = db[COLLECTION_NAME]
    result = await collection.update_one({"id": item_id}, {"$set": updated_item.dict()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item updated successfully"}
