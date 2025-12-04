# System Architecture Diagrams

## 1. Data Flow Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   VodafoneZiggo AI Assistant                            │
│                      Complete Data Flow                                 │
└─────────────────────────────────────────────────────────────────────────┘

INGESTION PHASE (Daily/On-Demand)
═════════════════════════════════════════════════════════════════════════

    User initiates scrape
           │
           ▼
    ┌─────────────────────┐
    │  Web Scraper        │ src/scraper.py
    │  (BeautifulSoup)    │
    │                     │
    │ Fetches HTML from   │
    │ ziggo.nl/internet   │
    └──────────┬──────────┘
               │ Raw HTML (~100KB)
               ▼
    ┌─────────────────────┐
    │  Text Extraction    │
    │  - Remove scripts   │
    │  - Remove styles    │
    │  - Extract text     │
    └──────────┬──────────┘
               │ Clean text (~50KB)
               ▼
    ┌─────────────────────────────────────┐
    │  Text Chunking                      │
    │  RecursiveCharacterTextSplitter     │
    │                                     │
    │  Chunk Size: 500 chars              │
    │  Overlap: 100 chars (context)       │
    │  Result: ~100-500 chunks            │
    └──────────┬──────────────────────────┘
               │ [chunk1, chunk2, ...]
               ▼
    ┌─────────────────────────────────────┐
    │  Embedding Model                    │
    │  all-MiniLM-L6-v2                   │
    │                                     │
    │  Input: 500 chars max               │
    │  Output: 384-dim vector             │
    │  Speed: ~200 chunks/sec             │
    │  Results: 384-dim ✕ N chunks       │
    └──────────┬──────────────────────────┘
               │ Embeddings (vectors)
               ▼
    ┌──────────────────────────────────────────┐
    │  Chroma Vector Store                     │
    │                                          │
    │  /app/data/chroma_db/                    │
    │  ├─ SQLite (metadata)                    │
    │  ├─ Vector index                         │
    │  └─ Text chunks                          │
    │                                          │
    │  Storage: Persistent across restarts     │
    │  Access: Indexed for fast retrieval      │
    └──────────┬───────────────────────────────┘
               │ Ready for queries


RETRIEVAL PHASE (Per Request)
═════════════════════════════════════════════════════════════════════════

    User sends question
    (via FastAPI endpoint)
           │
           ▼
    ┌──────────────────────────────────┐
    │  POST /api/ask                   │
    │  {"question": "..."}             │
    │                                  │
    │  Validation:                     │
    │  ✓ JSON format                   │
    │  ✓ Not empty                     │
    │  ✓ Type checking                 │
    └──────────┬───────────────────────┘
               │ Validated question
               ▼
    ┌──────────────────────────────────┐
    │  Embed Question                  │
    │  (same model as documents)       │
    │                                  │
    │  Input: "What packages..."       │
    │  Output: 384-dim vector          │
    │  Time: ~10ms                     │
    └──────────┬───────────────────────┘
               │ Question embedding
               ▼
    ┌──────────────────────────────────────┐
    │  Similarity Search                   │
    │  Chroma Vector Store                 │
    │                                      │
    │  Metric: Cosine Similarity           │
    │           cos(θ) = A·B / |A||B|     │
    │                                      │
    │  Retrieve: Top-3 most similar chunks │
    │  Each with similarity score          │
    └──────────┬───────────────────────────┘
               │ [doc1(score=0.89),
               │  doc2(score=0.76),
               │  doc3(score=0.42)]
               ▼
    ┌────────────────────────────────────────┐
    │  Response Generation                   │
    │                                        │
    │  Option A: LLM-Based (if available)   │
    │  ├─ Create prompt with context        │
    │  ├─ Include retrieved documents       │
    │  ├─ Call LLM (Mistral-7B or OpenAI)  │
    │  ├─ Generate natural response         │
    │  └─ Time: 500ms-2s                    │
    │                                        │
    │  Option B: Fallback (if LLM fails)    │
    │  ├─ Extract top chunk                 │
    │  ├─ Format as response                │
    │  └─ Time: <50ms                       │
    └──────────┬───────────────────────────┘
               │ Generated response
               ▼
    ┌────────────────────────────────────┐
    │  Response Package                  │
    │  {                                 │
    │    "question": "...",              │
    │    "answer": "Based on docs...",   │
    │    "sources": [                    │
    │      "5G coverage in...",          │
    │      "Mobile networks...",         │
    │      "Speed up to..."              │
    │    ],                              │
    │    "success": true                 │
    │  }                                 │
    └──────────┬────────────────────────┘
               │ JSON Response
               ▼
    ┌────────────────┐
    │  User/Client   │
    │  Receives      │
    │  Answer ✓      │
    └────────────────┘
```

## 2. Component Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI Container                            │
│              (Single Container, Horizontally Scalable)          │
└──────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Application Layer (FastAPI + Uvicorn)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ REST Endpoints (src/main.py)                            │   │
│  │                                                         │   │
│  │ GET  /                    → API info                    │   │
│  │ GET  /api/health          → Health check               │   │
│  │ GET  /api/stats           → Store statistics           │   │
│  │ POST /api/ask             → Answer question (type-safe)│   │
│  │ POST /api/ask-simple      → Answer question (JSON)     │   │
│  │ GET  /docs                → Swagger UI                 │   │
│  │ GET  /redoc               → ReDoc                      │   │
│  │                                                         │   │
│  └──────────────────┬────────────────────────────────────┘   │
│                     │ HTTP Request                             │
└─────────────────────┼─────────────────────────────────────────┘
                      │
┌─────────────────────▼─────────────────────────────────────────┐
│ Business Logic Layer                                          │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ RAG Assistant (src/rag_assistant.py)                 │    │
│  │ - Orchestrates retrieval + generation               │    │
│  │ - Manages LLM lifecycle                             │    │
│  │ - Prompt engineering                                │    │
│  │ - Error handling & fallbacks                        │    │
│  └──────────────────┬───────────────────────────────────┘    │
│                     │                                         │
│  ┌──────────────────▼───────────────────────────────────┐    │
│  │ Embedding & Storage (src/embedding_store.py)        │    │
│  │ - Manages embedding model                           │    │
│  │ - Handles Chroma vector store                       │    │
│  │ - Similarity search & retrieval                     │    │
│  │ - Persistence management                           │    │
│  └──────────────────┬───────────────────────────────────┘    │
│                     │                                         │
└─────────────────────┼─────────────────────────────────────────┘
                      │
┌─────────────────────▼─────────────────────────────────────────┐
│ Data Layer                                                    │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ Chroma Vector Store (/app/data/chroma_db)           │    │
│  │ - SQLite database (metadata)                        │    │
│  │ - Vector index (FAISS-backed)                       │    │
│  │ - Text chunks storage                              │    │
│  │ - Persistent volume mounted                        │    │
│  └──────────────────┬───────────────────────────────────┘    │
│                     │                                         │
│  ┌──────────────────▼───────────────────────────────────┐    │
│  │ Models (In-Memory)                                  │    │
│  │ - all-MiniLM-L6-v2 (embeddings, 80MB)              │    │
│  │ - Mistral-7B (optional, LLM, 14GB)                 │    │
│  │ - Cached on first load                            │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
└───────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Initialization & Startup                                   │
├─────────────────────────────────────────────────────────────┤
│ 1. Load embedding model (80MB)                              │
│ 2. Try loading existing Chroma store                        │
│ 3. If not exists: Scrape content from ziggo.nl/internet    │
│ 4. Chunk text (500 char chunks, 100 overlap)               │
│ 5. Embed all chunks                                         │
│ 6. Store in Chroma (persist to disk)                       │
│ 7. Initialize RAG assistant                                │
│ 8. Load LLM (if configured)                                │
│ 9. Mark as ready (health check passes)                     │
└─────────────────────────────────────────────────────────────┘
```

## 3. AWS Deployment Target

```
┌──────────────────────────────────────────────────────────────────┐
│                         Internet                                 │
│                                                                  │
└──────────────────────────────┬───────────────────────────────────┘
                               │ HTTPS
              ┌────────────────▼─────────────────┐
              │    CloudFront CDN                │
              │  (Content Delivery Network)      │
              │  - Cache responses               │
              │  - DDoS protection               │
              └────────────────┬──────────────────┘
                               │
              ┌────────────────▼──────────────────┐
              │   API Gateway / ALB               │
              │  (Application Load Balancer)      │
              │  - Route requests                 │
              │  - SSL/TLS termination            │
              │  - Rate limiting                  │
              │  - Request validation             │
              │  - Sticky sessions (optional)     │
              └────────────────┬──────────────────┘
                               │
         ┌─────────────────────▼──────────────────────┐
         │                                            │
         │   ECS Fargate Auto-Scaling Group           │
         │   (Container Orchestration)                │
         │                                            │
         │  Replica 1: FastAPI Container              │
         │  ├─ 2 CPU, 4GB memory                      │
         │  ├─ Port 8000                              │
         │  └─ Health checks every 30s                │
         │                                            │
         │  Replica 2: FastAPI Container              │
         │  ├─ 2 CPU, 4GB memory                      │
         │  ├─ Port 8000                              │
         │  └─ Auto-scale: CPU > 70%                  │
         │                                            │
         │  Replica N: FastAPI Container              │
         │  └─ Auto-scales 1-10 based on metrics      │
         │                                            │
         │  Scaling Triggers:                         │
         │  - CPU > 70% for 2 min → +1 task          │
         │  - Memory > 80% → +1 task                  │
         │  - CPU < 30% for 5 min → -1 task          │
         │  - Queue length > 20 → +1 task            │
         │                                            │
         └──────────────────────┬─────────────────────┘
                                │
         ┌──────────────────────▼──────────────────────┐
         │  Shared Data Services                       │
         │                                             │
         │  ┌────────────────────────────────────┐     │
         │  │ OpenSearch (Vector Store)          │     │
         │  │ - 3 nodes (multi-AZ)               │     │
         │  │ - Data persistence                 │     │
         │  │ - Daily snapshots to S3            │     │
         │  │ - Auto-failover                    │     │
         │  │ - 1M+ vectors supported            │     │
         │  └────────────────────────────────────┘     │
         │                                             │
         │  ┌────────────────────────────────────┐     │
         │  │ ElastiCache (Redis)                │     │
         │  │ - Embedding cache                  │     │
         │  │ - Session management               │     │
         │  │ - Rate limit counters              │     │
         │  │ - TTL: 24 hours                    │     │
         │  └────────────────────────────────────┘     │
         │                                             │
         │  ┌────────────────────────────────────┐     │
         │  │ RDS Aurora PostgreSQL              │     │
         │  │ - User metadata                    │     │
         │  │ - Audit logs                       │     │
         │  │ - Analytics                        │     │
         │  │ - Multi-AZ failover                │     │
         │  └────────────────────────────────────┘     │
         │                                             │
         │  ┌────────────────────────────────────┐     │
         │  │ S3 (Data Lake)                     │     │
         │  │ - Backup vectors (nightly)         │     │
         │  │ - Scraped content archive          │     │
         │  │ - Logs archival (daily)            │     │
         │  │ - Lifecycle: Move to Glacier >30d  │     │
         │  └────────────────────────────────────┘     │
         │                                             │
         │  ┌────────────────────────────────────┐     │
         │  │ Lambda (Scheduled Tasks)           │     │
         │  │ - EventBridge rule: Daily 3 AM UTC │     │
         │  │ - Trigger: Scrape & update vectors │     │
         │  │ - Timeout: 15 minutes              │     │
         │  └────────────────────────────────────┘     │
         │                                             │
         └──────────────────────────────────────────────┘
                                │
         ┌──────────────────────▼──────────────────────┐
         │  Monitoring & Logging                       │
         │                                             │
         │  ┌────────────────────────────────────┐     │
         │  │ CloudWatch                         │     │
         │  │ - API response times               │     │
         │  │ - Container CPU/memory usage       │     │
         │  │ - Vector search latency            │     │
         │  │ - Error rates & exceptions         │     │
         │  │ - Custom metrics                   │     │
         │  └────────────────────────────────────┘     │
         │                                             │
         │  ┌────────────────────────────────────┐     │
         │  │ X-Ray (Distributed Tracing)        │     │
         │  │ - Request flow visualization       │     │
         │  │ - Latency analysis                 │     │
         │  │ - Service dependencies             │     │
         │  └────────────────────────────────────┘     │
         │                                             │
         │  ┌────────────────────────────────────┐     │
         │  │ SNS Alerts                         │     │
         │  │ - High error rate > 5%             │     │
         │  │ - Latency p99 > 2s                 │     │
         │  │ - Service unavailable              │     │
         │  │ - Notifications to Slack/PagerDuty │     │
         │  └────────────────────────────────────┘     │
         │                                             │
         └─────────────────────────────────────────────┘
```

## 4. Request/Response Flow

```
┌──────────────────────────────────────────────────────────────┐
│                  Complete Request Flow                       │
└──────────────────────────────────────────────────────────────┘

USER REQUEST
============
POST /api/ask
Headers: Content-Type: application/json
Body: {
  "question": "What 5G packages do you offer?"
}

                    ▼ ENTER API


FASTAPI VALIDATION
==================
✓ Check JSON format
✓ Validate against Pydantic Question model
✓ Check question not empty
✓ Strip whitespace

                    ▼


RAG ASSISTANT
=============
1. Embed question (all-MiniLM-L6-v2)
   Input:  "What 5G packages do you offer?"
   Output: 384-dimensional vector

2. Search Chroma vector store
   Metric: Cosine similarity
   Top-K: 3 results
   
   Results:
   - Doc 1: "5G coverage in..." (score: 0.89) ✓
   - Doc 2: "Mobile packages..." (score: 0.76) ✓
   - Doc 3: "Fiber optics..." (score: 0.42)

3. Generate response (LLM or fallback)
   
   LLM Mode (Mistral-7B):
   - Create prompt with context
   - Include retrieved documents
   - Call model (~1 second)
   - Generate answer
   
   Fallback Mode:
   - Concatenate top 2 chunks
   - Format as answer
   - ~50ms

4. Package response
   {
     "question": "What 5G packages...",
     "answer": "Based on our documentation, 
               we offer 5G packages with...",
     "sources": [
       "5G coverage in major cities...",
       "Mobile packages starting from..."
     ],
     "success": true
   }

                    ▼ EXIT API


USER RECEIVES
=============
HTTP 200 OK
Content-Type: application/json
Body: {
  "question": "What 5G packages do you offer?",
  "answer": "We offer 5G packages with coverage 
            in major cities...",
  "sources": ["..."],
  "success": true
}


ERROR SCENARIOS
===============
1. Empty question
   → HTTP 400 Bad Request
   → "Question cannot be empty"

2. Service not initialized
   → HTTP 503 Service Unavailable
   → "Assistant not initialized"

3. Processing error
   → HTTP 500 Internal Server Error
   → "Error processing question: [details]"
```

---

**These diagrams show the complete architecture from request to response, local deployment to AWS scaling.**
