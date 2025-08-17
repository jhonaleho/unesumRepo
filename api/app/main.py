# app/main.py
import os
import time
import logging
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from openai import OpenAI

# Tu lógica de búsqueda
from app.search import search_vectors, get_mapping  # get_mapping ya existe en tu search.py

# ---------- Config básica ----------
ROOT = Path(__file__).resolve().parent.parent  # .../api
# En local puedes tener .env, en Fly usas secrets/vars
load_dotenv(ROOT / ".env")

APP_TITLE = "Thesis Search API"
APP_VERSION = "1.0.0"

# CORS: permite localhost y tu dominio prod; se puede extender con env ALLOW_ORIGINS
_default_origins = ["http://localhost:5173", "https://www.unesumrepo.com"]
_env_origins = os.getenv("ALLOW_ORIGINS")
ALLOW_ORIGINS = (
    [o.strip() for o in _env_origins.split(",")] if _env_origins else _default_origins
)

# Logging (nivel configurable por env: DEBUG/INFO/WARN/ERROR)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("thesis-api")

# OpenAI
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
EMBED_DIMENSIONS = int(os.getenv("EMBED_DIMENSIONS", "512"))
API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "Falta OPENAI_API_KEY. En local, crea api/.env con OPENAI_API_KEY=sk-... "
        "o expórtala. En Fly, usa `fly secrets set OPENAI_API_KEY=...`."
    )

OPENAI_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "20"))
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "2"))

# Cliente OpenAI con timeout y pocos retries (evita cuelgues)
client = OpenAI(api_key=API_KEY, timeout=OPENAI_TIMEOUT, max_retries=OPENAI_MAX_RETRIES)

# ---------- FastAPI ----------
app = FastAPI(title=APP_TITLE, version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Utilidades ----------
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

# ---------- Modelos ----------
class SearchRequest(BaseModel):
    q: str
    top_k: int = 10

# ---------- Endpoints ----------
@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.on_event("startup")
def warmup():
    """Precarga el mapping en memoria para que el 1er /search sea rápido."""
    t0 = time.time()
    try:
        m = get_mapping()
        logger.info("[startup] mapping cargado: %s registros en %.2fs", len(m), time.time() - t0)
    except Exception as e:
        # No tumbes el arranque si falla: log y sigue (healthz seguirá vivo)
        logger.exception("[startup] error precargando mapping: %s", e)

@app.post("/search")
def search(req: SearchRequest):
    if not req.q or not req.q.strip():
        raise HTTPException(status_code=400, detail="Empty query")

    # top_k razonable
    top_k = max(1, min(int(req.top_k), 50))

    t0 = time.time()
    logger.info("[/search] q=%r top_k=%s", req.q, top_k)
    try:
        qv = embed_query(req.q)
        logger.info("[/search] embed listo en %.2fs", time.time() - t0)
        t1 = time.time()
        results = search_vectors(qv, top_k)
        logger.info(
            "[/search] faiss+mapping en %.2fs (total %.2fs)",
            time.time() - t1, time.time() - t0
        )
        return {"results": results}
    except HTTPException:
        raise
    except Exception as e:
        # Siempre devuelve JSON en caso de error
        logger.exception("[/search] error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
