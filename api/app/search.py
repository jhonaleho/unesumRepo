# app/search.py
import os, json, threading
import faiss, numpy as np

# Lee rutas desde variables de entorno (Dockerfile/fly.toml)
MAPPING_PATH = os.getenv("MAPPING_PATH", "/app/data/mapping.jsonl")
INDEX_PATH   = os.getenv("INDEX_PATH",   "/app/data/index.faiss")

# Caches en memoria (se llenan 1 sola vez)
_mapping_cache = None
_index_cache = None
_lock = threading.Lock()

def _load_mapping(path: str):
    out, bad = [], 0
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception as e:
                bad += 1
                # no tumbes el server por 1 línea mala
                print(f"[mapping] línea {i} inválida: {e}")
    print(f"[mapping] cargadas={len(out)}; inválidas={bad}; path={path}")
    return out

def get_mapping():
    global _mapping_cache
    if _mapping_cache is None:
        with _lock:
            if _mapping_cache is None:
                _mapping_cache = _load_mapping(MAPPING_PATH)
    return _mapping_cache

def get_index():
    global _index_cache
    if _index_cache is None:
        with _lock:
            if _index_cache is None:
                print(f"[faiss] leyendo índice: {INDEX_PATH}")
                idx = faiss.read_index(INDEX_PATH)
                _index_cache = idx
    return _index_cache

def search_vectors(query_vec: np.ndarray, top_k: int = 5):
    idx = get_index()
    mapping = get_mapping()
    sims, ids = idx.search(query_vec, top_k)
    results = []
    for rank, (vid, score) in enumerate(zip(ids[0], sims[0]), start=1):
        if int(vid) < 0 or int(vid) >= len(mapping):
            continue
        rec = mapping[int(vid)]
        results.append({
            "rank": rank,
            "score": float(score),
            "vector_id": int(vid),
            "titulo": rec.get("titulo"),
            "autores": rec.get("autores"),
            "anio_publicacion": rec.get("anio_publicacion"),
            "pagina_inicio": rec.get("pagina_inicio"),
            "pagina_fin": rec.get("pagina_fin"),
            "pdf_url": rec.get("pdf_url"),
            "nombre_archivo": rec.get("nombre_archivo"),
            "snippet": (rec.get("texto") or "")[:300]
        })
    return results
