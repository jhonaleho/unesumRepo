import os, json
import numpy as np
import faiss

INDEX_PATH   = os.getenv("INDEX_PATH", "./data/index.faiss")
MAPPING_PATH = os.getenv("MAPPING_PATH", "./data/mapping.jsonl")
TOPK_DEFAULT = int(os.getenv("TOPK", "10"))

_index = None
_mapping = None

def _load_mapping(path):
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            out.append(json.loads(line))
    return out

def get_index():
    global _index
    if _index is None:
        _index = faiss.read_index(INDEX_PATH)
        # Respect nprobe if IVF-based
        try:
            _index.nprobe = int(os.getenv("NPROBE", "32"))
        except Exception:
            pass
        inner = getattr(_index, "index", None)
        if inner and hasattr(inner, "nprobe"):
            inner.nprobe = int(os.getenv("NPROBE", "32"))
    return _index

def get_mapping():
    global _mapping
    if _mapping is None:
        _mapping = _load_mapping(MAPPING_PATH)
    return _mapping

def search_vectors(query_vec: np.ndarray, top_k: int = TOPK_DEFAULT):
    index = get_index()
    scores, ids = index.search(query_vec, top_k)
    mapping = get_mapping()
    results = []
    for vid, score in zip(ids[0], scores[0]):
        rec = mapping[int(vid)]
        results.append({
            "score": float(score),
            "titulo": rec.get("titulo"),
            "autores": rec.get("autores"),
            "anio_publicacion": rec.get("anio_publicacion"),
            "pagina_inicio": rec.get("pagina_inicio"),
            "pagina_fin": rec.get("pagina_fin"),
            "pdf_url": rec.get("pdf_url"),
            "snippet": (rec.get("texto") or "")[:400]
        })
    return results
