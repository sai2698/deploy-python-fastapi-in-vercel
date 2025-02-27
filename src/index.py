from fastapi import FastAPI, HTTPException, Depends
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

# MongoDB connection configuration
MONGODB_URI = "mongodb+srv://naveendevarapalli99:Naveen123@cluster0.jmg62pd.mongodb.net/"
DB_NAME = "ott"
COLLECTION_NAME = "catalogue"

# Database connection handling
async def get_database():
    """
    Create a connection to the MongoDB database and yield the database object
    """
    if not MONGODB_URI:
        raise HTTPException(status_code=500, detail="MongoDB URI not configured")
    
    client = AsyncIOMotorClient(MONGODB_URI)
    try:
        # Connect to the database
        db = client[DB_NAME]
        yield db
    finally:
        # Close the connection when done
        client.close()

@app.get("/")
async def root():
    return {"message": "Welcome to the MongoDB API"}

@app.get("/getall", response_model=List[Dict[str, Any]])
async def get_all_items(db = Depends(get_database)):
    """
    Retrieve all documents from the MongoDB collection
    """
    try:
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
