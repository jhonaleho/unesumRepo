import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from openai import OpenAI
from app.search import search_vectors

ROOT = Path(__file__).resolve().parent.parent  # .../api
load_dotenv(ROOT / ".env")
app = FastAPI(title="Thesis Search API", version="1.0.0")

# Local dev CORS: allow Vite (http://localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],

)

EMBED_MODEL      = os.getenv("EMBED_MODEL", "text-embedding-3-small")
EMBED_DIMENSIONS = int(os.getenv("EMBED_DIMENSIONS", "512"))
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "Falta OPENAI_API_KEY. Crea api/.env con OPENAI_API_KEY=sk-... "
        "o exporta la variable antes de iniciar."
    )

client = OpenAI(api_key=API_KEY)
def l2_normalize(mat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-12
    return mat / norms

def embed_query(q: str) -> np.ndarray:
    kwargs = dict(model=EMBED_MODEL, input=[q])
    if EMBED_DIMENSIONS:
        kwargs["dimensions"] = EMBED_DIMENSIONS
    resp = client.embeddings.create(**kwargs)
    v = np.array(resp.data[0].embedding, dtype=np.float32).reshape(1, -1)
    return l2_normalize(v)

class SearchRequest(BaseModel):
    q: str
    top_k: int = 10

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/search")
def search(req: SearchRequest):
    if not req.q.strip():
        raise HTTPException(status_code=400, detail="Empty query")
    qv = embed_query(req.q)
    return {"results": search_vectors(qv, req.top_k)}
