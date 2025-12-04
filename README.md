# VodafoneZiggo Customer Support AI Assistant

A production-ready prototype of an AI-powered customer support assistant that scrapes website content, embeds it in a vector store, and provides intelligent question-answering through a REST API.

## 🎯 Overview

This project implements an end-to-end RAG (Retrieval-Augmented Generation) system with the following flow:

```
Website → Scrape Content → Split & Embed → Vector Store → API
                                                    ↓
                                              Retrieve relevant docs
                                                    ↓
                                              Generate Response
```

## 🏗️ Architecture

### Components

1. **Web Scraper** (`src/scraper.py`)
   - Uses `BeautifulSoup` + `requests` for simple, lightweight HTML parsing
   - No JavaScript rendering needed (suitable for static content)
   - Extracts clean text content, removing scripts and styles

2. **Embedding & Vector Store** (`src/embedding_store.py`)
   - **Model**: HuggingFace `sentence-transformers/all-MiniLM-L6-v2`
   - **Why this model?**
     - Open-source, no API keys needed
     - 384-dimensional vectors (lightweight, fast)
     - ~80% quality of larger models but 10x faster
     - Excellent for semantic search tasks
   - **Storage**: Chroma DB (local, persistent, no external services)

3. **RAG Pipeline** (`src/rag_assistant.py`)
   - Combines retrieval with optional LLM-based response generation
   - **LLM Options**:
     - Local: Mistral-7B (runs offline, resource-intensive)
     - API: OpenAI GPT models (requires keys, cloud-based)
   - Includes fallback mode for retrieval-only answers

4. **FastAPI Application** (`src/main.py`)
   - Exposes REST endpoints for question-answering
   - Automatic startup logic for data initialization
   - Health checks and statistics endpoints

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose (recommended)
- OR: Python 3.11+, pip

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
cd /home/syedalihassan03/technical-test

# Build and run
docker-compose up --build

# Wait for startup (~2 minutes on first run for model downloads)
# API will be available at http://localhost:8000
```

### Option 2: Local Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
cd src
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📡 API Usage

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Ask a Question
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What internet packages do you offer?"}'
```

### Get Statistics
```bash
curl http://localhost:8000/api/stats
```

### Interactive API Docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📦 Key Libraries & Why They Were Chosen

| Library | Purpose | Why This Choice |
|---------|---------|-----------------|
| **requests** | HTTP client | Simple, reliable, no bloat |
| **BeautifulSoup4** | HTML parsing | Lightweight, no JS rendering needed |
| **LangChain** | LLM orchestration | Flexible chains, modular design |
| **sentence-transformers** | Text embeddings | Open-source, fast, high quality |
| **Chroma** | Vector database | Local, simple, persistent |
| **FastAPI** | Web framework | Modern, async, auto-documentation |
| **Pydantic** | Data validation | Type-safe, built into FastAPI |

## 🔧 Configuration

### Environment Variables (`.env`)

```env
SCRAPE_URL=https://ziggo.nl/internet          # Target URL
DATA_DIR=./data                                 # Persistent storage
LOG_LEVEL=INFO                                  # Logging level
API_PORT=8000                                   # FastAPI port
```

### Docker Compose Customization

Edit `docker-compose.yml`:
- Change `SCRAPE_URL` to scrape different pages
- Adjust volume mounts for data persistence
- Enable GPU support with NVIDIA runtime (see comments)

## 📊 Vector Store Details

### Indexing Strategy
- **Text Chunking**: 500 characters per chunk with 100 char overlap
- **Overlap Benefit**: Preserves context at chunk boundaries
- **Retrieval**: Top-3 most similar chunks (default, configurable)
- **Similarity Metric**: Cosine similarity (default in Chroma)

### Diagram: Data Flow

```
┌─────────────────┐
│ VodafoneZiggo   │
│ Website         │
└────────┬────────┘
         │ HTTP Request
         ▼
┌─────────────────────────────────────┐
│ Scraper (BeautifulSoup)             │
│ - Fetch HTML                        │
│ - Remove scripts/styles             │
│ - Extract clean text                │
└────────┬────────────────────────────┘
         │ Raw Text Content
         ▼
┌─────────────────────────────────────┐
│ Text Splitter                       │
│ - Split into 500-char chunks        │
│ - 100-char overlap                  │
└────────┬────────────────────────────┘
         │ Text Chunks
         ▼
┌─────────────────────────────────────┐
│ Embeddings (all-MiniLM-L6-v2)       │
│ - Embed each chunk                  │
│ - 384-dim vectors                   │
└────────┬────────────────────────────┘
         │ Embeddings
         ▼
┌─────────────────────────────────────┐
│ Chroma Vector Store                 │
│ - Store embeddings + text           │
│ - Persist to disk                   │
└────────┬────────────────────────────┘
         │ Retrieved docs
         ▼
┌─────────────────────────────────────┐
│ FastAPI Endpoint                    │
│ - Accept user question              │
│ - Retrieve similar chunks           │
│ - Generate response                 │
└────────┬────────────────────────────┘
         │ JSON Response
         ▼
┌─────────────────┐
│ User/Client     │
└─────────────────┘
```

## 🌩️ AWS Deployment Architecture

For scaling to production on AWS:

```
┌───────────────────────────────────────────────────────────┐
│                     AWS Architecture                       │
├───────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ CloudFront / ALB (API Gateway)                      │  │
│  │ - Route HTTP requests                              │  │
│  │ - Load balancing, caching                          │  │
│  └──────────────────┬──────────────────────────────────┘  │
│                     │                                       │
│  ┌──────────────────▼──────────────────┐                  │
│  │ ECS / EKS (Container Orchestration) │                  │
│  │ - Run FastAPI application           │                  │
│  │ - Auto-scaling based on load        │                  │
│  │ - Service discovery                 │                  │
│  └──────────────────┬──────────────────┘                  │
│                     │                                       │
│  ┌──────────────────▼─────────────────┐                   │
│  │ OpenSearch / Pinecone               │                   │
│  │ (Distributed Vector Store)          │                   │
│  │ - Replicated across AZs             │                   │
│  │ - High availability                 │                   │
│  └──────────────────┬──────────────────┘                   │
│                     │                                       │
│  ┌──────────────────▼──────────────────┐                  │
│  │ RDS / ElastiCache                   │                  │
│  │ - Metadata/state storage            │                  │
│  │ - Session caching                   │                  │
│  └──────────────────────────────────────┘                  │
│                                                             │
│  ┌──────────────────────────────────────┐                 │
│  │ SageMaker (Optional)                 │                 │
│  │ - Fine-tune embedding models        │                 │
│  │ - Host larger LLMs                  │                 │
│  └──────────────────────────────────────┘                 │
│                                                             │
└───────────────────────────────────────────────────────────┘
```

### AWS Service Recommendations

| Service | Purpose | Why |
|---------|---------|-----|
| **ECR** | Container registry | Store Docker images |
| **ECS Fargate** | Container orchestration | Serverless, no infra management |
| **OpenSearch** | Vector store | Scales to millions of vectors |
| **Lambda** | Scheduled scraping | Periodic data updates |
| **S3** | Vector store backup | Durability, cost-effective |
| **CloudWatch** | Monitoring/logging | Built-in, comprehensive |
| **API Gateway** | API management | Rate limiting, authentication |

## 🔐 Security Considerations

### Current Prototype
- ⚠️ No authentication (add in production)
- ⚠️ CORS allows all origins (restrict in production)
- ⚠️ API keys placeholder (implement key management)

### Production Checklist
- [ ] Add API key authentication
- [ ] Restrict CORS to known domains
- [ ] Use AWS Secrets Manager for sensitive data
- [ ] Enable TLS/HTTPS
- [ ] Implement rate limiting
- [ ] Add request validation
- [ ] Log all access attempts
- [ ] Regular security audits

## 📝 Troubleshooting

### Vector store not loading after restart
```bash
# Clear persisted data
docker volume rm technical-test_ai_data

# Rebuild and restart
docker-compose down
docker-compose up --build
```

### Out of memory errors
- Reduce model size: Use `Phi-2` or `Orca-Mini-3B` instead of Mistral-7B
- Enable quantization in `rag_assistant.py`
- Increase Docker memory limit in `docker-compose.yml`

### Slow responses on first query
- First query runs model inference (warming up)
- Subsequent queries benefit from caching
- Consider async processing for production

### Scraping fails
- Check `SCRAPE_URL` is valid and accessible
- Verify network connectivity inside container
- Check User-Agent headers (some sites block scrapers)

## 🧪 Testing

```bash
# Health check
curl http://localhost:8000/api/health

# Sample question
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is your internet speed?"}'

# View vector store stats
curl http://localhost:8000/api/stats
```

## 📈 Performance Metrics

- **Startup time**: ~60-120s (first run, including model download)
- **Embedding creation**: ~1-2 min for 10,000 chunks
- **Query latency**: ~500ms-2s (local LLM) or ~100-200ms (API LLM)
- **Memory usage**: ~6-8GB (Mistral-7B loaded) or ~2GB (retrieval-only mode)

## 🎓 Learning Resources

- [LangChain Documentation](https://python.langchain.com)
- [Chroma Vector Database](https://www.trychroma.com)
- [HuggingFace Embeddings](https://huggingface.co/sentence-transformers)
- [FastAPI Documentation](https://fastapi.tiangolo.com)

## 📄 License

This project is provided as a technical assignment prototype.

## 👤 Support

For issues or questions:
1. Check `logs/` directory for error details
2. Review this README's troubleshooting section
3. Check docker-compose logs: `docker-compose logs -f ai-assistant`

---

**Status**: Production-ready prototype with demonstration purposes.
**Last Updated**: December 2025
