from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
import os
from typing import List, Dict, Any
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

# MongoDB connection
# Get MongoDB URI from environment variables
MONGODB_URI = "mongodb+srv://naveendevarapalli99:Naveen123@cluster0.jmg62pd.mongodb.net/"
DB_NAME = "ott"
COLLECTION_NAME = "catalogue"

# Create a MongoDB client
client = None

@app.on_event("startup")
async def startup_db_client():
    global client
    if not MONGODB_URI:
        raise HTTPException(status_code=500, detail="MongoDB URI not configured")
    client = AsyncIOMotorClient(MONGODB_URI)
    
@app.on_event("shutdown")
async def shutdown_db_client():
    global client
    if client:
        client.close()

@app.get("/")
async def root():
    return {"message": "Welcome to the MongoDB API"}

@app.get("/getall", response_model=List[Dict[str, Any]])
async def get_all_items():
    """
    Retrieve all documents from the MongoDB collection
    """
    if not client:
        raise HTTPException(status_code=500, detail="Database client not initialized")
    
    try:
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # Get all documents from collection
        cursor = collection.find({})
        documents = await cursor.to_list(length=None)
        
        # MongoDB returns documents with ObjectId which is not JSON serializable
        # Convert ObjectId to string for each document
        processed_documents = []
        for doc in documents:
            if "_id" in doc and hasattr(doc["_id"], "__str__"):
                doc["_id"] = str(doc["_id"])
            processed_documents.append(doc)
            
        return processed_documents
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
