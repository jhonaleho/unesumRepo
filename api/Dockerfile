# api/Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps (mínimos). No usamos swig porque NO vamos a compilar FAISS.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiamos solo requirements primero para cachear capas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el código backend
COPY app ./app

# (Si el índice es pequeño y lo quieres hornear, descomenta)
# COPY data ./data

# Rutas y defaults (en Fly montaremos /data con un volumen)
ENV PORT=8080 \
    HOST=0.0.0.0 \
    INDEX_PATH=/data/index.faiss \
    MAPPING_PATH=/data/mapping.jsonl \
    EMBED_MODEL=text-embedding-3-small \
    EMBED_DIMENSIONS=512 \
    NPROBE=32

EXPOSE 8080
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8080","--workers","1"]
