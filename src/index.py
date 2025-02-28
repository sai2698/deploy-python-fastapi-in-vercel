from fastapi import FastAPI, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
import os
from typing import List, Dict, Any, Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# MongoDB connection configuration
MONGODB_URI = "your_mongodb_connection_string"
DB_NAME = "ott"
COLLECTION_NAME = "catalogue"

# Database connection handling
async def get_database():
    if not MONGODB_URI:
        raise HTTPException(status_code=500, detail="MongoDB URI not configured")
    client = AsyncIOMotorClient(MONGODB_URI)
    try:
        db = client[DB_NAME]
        yield db
    finally:
        client.close()

# Pydantic model for Catalogue
class CatalogueItem(BaseModel):
    id: str
    title: str
    genre: List[str]
    year: str
    thumbnail: str
    description: str
    url: Optional[str] = ""

@app.get("/")
async def root():
    return {"message": "Welcome to the MongoDB API"}

@app.get("/getall", response_model=List[Dict[str, Any]] )
async def get_all_items(db=Depends(get_database)):
    try:
        collection = db[COLLECTION_NAME]
        cursor = collection.find({})
        documents = await cursor.to_list(length=None)
        for doc in documents:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/add", response_model=Dict[str, str])
async def add_item(item: CatalogueItem, db=Depends(get_database)):
    try:
        collection = db[COLLECTION_NAME]
        result = await collection.insert_one(item.dict())
        return {"message": "Item added successfully", "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/get/{item_id}", response_model=Dict[str, Any])
async def get_item(item_id: str, db=Depends(get_database)):
    try:
        collection = db[COLLECTION_NAME]
        item = await collection.find_one({"id": item_id})
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        item["_id"] = str(item["_id"])
        return item
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.put("/update/{item_id}", response_model=Dict[str, str])
async def update_item(item_id: str, item: CatalogueItem, db=Depends(get_database)):
    try:
        collection = db[COLLECTION_NAME]
        result = await collection.update_one({"id": item_id}, {"$set": item.dict()})
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"message": "Item updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.delete("/delete/{item_id}", response_model=Dict[str, str])
async def delete_item(item_id: str, db=Depends(get_database)):
    try:
        collection = db[COLLECTION_NAME]
        result = await collection.delete_one({"id": item_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"message": "Item deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
