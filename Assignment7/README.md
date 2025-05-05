# Assignment7: FAISS Document Embedding & Search Server

This project provides a simple Flask-based API for document chunking, embedding, and semantic search using FAISS and an external embedding model using Ollama. It is designed to index text data (from HTML) and enable fast similarity search over the indexed content.

## Features

- **Chunking**: Splits input text into overlapping chunks for better embedding and retrieval.
- **Embedding**: Uses an external embedding server (Ollama) to generate vector representations of text.
- **FAISS Indexing**: Stores and searches embeddings using Facebook's FAISS library for efficient similarity search.
- **REST API**: Exposes endpoints for document extraction (indexing) and search.

## Requirements

- Python 3.8+
- [FAISS](https://github.com/facebookresearch/faiss)
- Flask
- Flask-CORS
- requests
- numpy
- beautifulsoup4

You also need an embedding server running at `http://127.0.0.1:11434` that supports the `/api/embeddings` endpoint and the `nomic-embed-text` model.

## Usage

### 1. Start the FAISS Server

```bash
python faiss_server.py
```

The server will start on port 5000.

### 2. API Endpoints

#### `/extract` (POST)

- **Purpose**: Indexes a document by extracting text from HTML, chunking it, embedding each chunk, and adding to the FAISS index.
- **Request JSON**:
  ```json
  {
    "url": "http://example.com/page",
    "html": "<html>...</html>"
  }
  ```
- **Response**:
  ```json
  {
    "status": "ok",
    "chunks_indexed": 5
  }
  ```

#### `/search` (POST)

- **Purpose**: Searches the indexed documents for the most semantically similar chunks to the query.
- **Request JSON**:
  ```json
  {
    "query": "your search text"
  }
  ```
- **Response**:
  ```json
  {
    "results": [
      {
        "url": "http://example.com/page",
        "chunk": "Relevant chunk of text..."
      },
      ...
    ]
  }
  ```

## Notes

- The FAISS index and chunk metadata are stored in the `faiss_index` directory.
- The embedding server must be running and accessible at `http://127.0.0.1:11434/api/embeddings`.
- The embedding model used is `nomic-embed-text` 
- The server currently uses an in-memory list for chunk metadata, so restarting the server will lose metadata unless you implement persistent storage.

## Troubleshooting

- **403 Forbidden from embedding server**: Ensure your embedding server is running, accessible, and does not require authentication or CORS headers for local requests.
- **FAISS index errors**: Make sure the `faiss_index` directory exists and is writable.
