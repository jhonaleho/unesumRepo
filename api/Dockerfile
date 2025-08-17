FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app
# Copiamos SOLO el índice (ya está en el repo)
COPY data/index.faiss /app/data/index.faiss

# Índice desde la imagen; mapping desde volumen /data
ENV PORT=8080 \
    HOST=0.0.0.0 \
    INDEX_PATH=/app/data/index.faiss \
    MAPPING_PATH=/data/mapping.jsonl \
    EMBED_MODEL=text-embedding-3-small \
    EMBED_DIMENSIONS=512 \
    NPROBE=32

EXPOSE 8080
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8080","--workers","1"]
