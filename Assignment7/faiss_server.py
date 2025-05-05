from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import faiss
import sys
import numpy as np
from pathlib import Path
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# In-memory storage
EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
CHUNK_SIZE = 256
CHUNK_OVERLAP = 40
chunk_metadata = []  # List of dicts: {'url': ..., 'chunk': ...}
dimension = 768      # Embedding size for 'all-MiniLM-L6-v2'
index = faiss.IndexFlatL2(dimension)  # FAISS index

def mcp_log(level: str, message: str) -> None:
    """Log a message to stderr to avoid interfering with JSON communication"""
    sys.stderr.write(f"{level}: {message}\n")
    sys.stderr.flush()

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunks.append(text[start:end])
        if end == text_length:
            break
        start += chunk_size - overlap
    return chunks

def get_embedding(text: str) -> np.ndarray:
    response = requests.post(
        "http://localhost:11434/api/embeddings",
        json={
            "model": "nomic-embed-text",
            "prompt": text
        }
    )
    response.raise_for_status()
    return np.array(response.json()["embedding"], dtype=np.float32)

@app.route('/extract', methods=['POST'])
def extract():
    ROOT = Path(__file__).parent.resolve()
    INDEX_CACHE = ROOT / "faiss_index"
    INDEX_FILE = INDEX_CACHE / "index.bin"


    data = request.json
    url = data['url']
    # text = data.get('text') or data.get('html')  # Accept either field
    html_content = data['html']
    soup = BeautifulSoup(html_content, features='html.parser')

    # Chunk the text
    chunks = chunk_text(soup.get_text(separator="\n"))
    # Compute embeddings for all chunks
    # embeddings = model.encode(chunks)
    embeddings = [get_embedding(chunk) for chunk in chunks]
    # embeddings = np.array(embeddings).astype('float32')

    # Store each chunk and its embedding
    for chunk, embedding in zip(chunks, embeddings):
        chunk_metadata.append({'url': url, 'chunk': chunk})
        index.add(np.expand_dims(embedding, axis=0))
    
    if index and index.ntotal > 0:
        faiss.write_index(index, str(INDEX_FILE))
        mcp_log("SUCCESS", "Saved FAISS index and metadata")
    else:
        mcp_log("WARN", "No new documents or updates to process.")

    return jsonify({'status': 'ok', 'chunks_indexed': len(chunks)})

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    query = data['query']

    # Compute embedding for query
    query_embedding = get_embedding(query).reshape(1, -1)
    # query_embedding = np.array(query_embedding).astype('float32')

    # Search in FAISS
    k = 5  # Number of results to return
    if index.ntotal == 0:
        return jsonify({'urls': []})

    D, I = index.search(query_embedding, k)
    results = []
    seen_urls = set()
    for idx in I[0]:
        if idx < len(chunk_metadata):
            url = chunk_metadata[idx]['url']
            if url not in seen_urls:
                results.append(url)
                seen_urls.add(url)

    return jsonify({'urls': results})

if __name__ == '__main__':
    app.run(port=5000)