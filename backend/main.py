from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException, RequestValidationError
import os
import chromadb
from sentence_transformers import SentenceTransformer
from services.hot_topic import get_hot_topics

from database import engine
import models
from routes import auth, mentor, roadmap, exercises
from auth import get_current_user

# Create DB tables
models.Base.metadata.create_all(bind=engine)

# Initialize ChromaDB for hot topics
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="hot_topics")

# Initialize sentence transformer model
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Function to populate ChromaDB with hot topics
def populate_hot_topics():
    print("🔄 Populating ChromaDB with hot topics...")
    topics = get_hot_topics()
    if topics:
        documents = [f"{topic['title']} - {topic['source']}" for topic in topics]
        metadatas = [{"url": topic["url"], "source": topic["source"]} for topic in topics]
        ids = [f"topic_{i}" for i in range(len(topics))]
        
        embeddings = embedder.encode(documents).tolist()
        
        collection.add(
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
            ids=ids
        )
        print(f"✅ Added {len(topics)} hot topics to ChromaDB")
    else:
        print("⚠️ No hot topics found to populate")

# Populate on startup
populate_hot_topics()

app = FastAPI(title="MyCoach API", version="1.0.0")

# Allow all localhost ports (Vite may use 5173, 5174, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Ensure CORS headers are present even on error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={"Access-Control-Allow-Origin": request.headers.get("origin", "*")},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
        headers={"Access-Control-Allow-Origin": request.headers.get("origin", "*")},
    )

# Serve uploaded CVs (optional, for admin use)
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth.router)
app.include_router(mentor.router)
app.include_router(roadmap.router)
app.include_router(exercises.router)

@app.get("/api/hot-topics/search")
def search_hot_topics(query: str, n_results: int = 5):
    """Search hot topics using vector similarity"""
    query_embedding = embedder.encode([query]).tolist()[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    return {
        "query": query,
        "results": [
            {
                "document": doc,
                "metadata": meta,
                "distance": dist
            } for doc, meta, dist in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )
        ]
    }

@app.get("/api/hot-topics/relevant")
def get_relevant_hot_topics(current_user: models.User = Depends(get_current_user)):
    """Get hot topics relevant to the user's career path"""
    if not current_user.career_path:
        return {"results": []}
    
    query = current_user.career_path
    query_embedding = embedder.encode([query]).tolist()[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=10  # More results for user
    )
    return {
        "career_path": query,
        "results": [
            {
                "title": doc.split(" - ")[0] if " - " in doc else doc,
                "source": meta["source"],
                "url": meta["url"],
                "relevance": 1 - dist  # Convert distance to relevance score
            } for doc, meta, dist in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )
        ]
    }

@app.get("/")
def root():
    return {"status": "MyCoach API running"}
