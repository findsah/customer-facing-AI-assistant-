# Architecture Diagram & Design Documentation

## 1. System Architecture Flowchart

```
┌──────────────────────────────────────────────────────────────────────┐
│                     VodafoneZiggo AI Assistant                       │
│                    End-to-End Architecture Flow                      │
└──────────────────────────────────────────────────────────────────────┘

PHASE 1: DATA INGESTION (One-time, can be scheduled)
═════════════════════════════════════════════════════

    ┌─────────────────────┐
    │  VodafoneZiggo      │
    │  Website            │
    │ ziggo.nl/internet   │
    └──────────┬──────────┘
               │ HTTPS Request
               ▼
    ┌─────────────────────────────────────────┐
    │  Web Scraper (BeautifulSoup)            │
    │  ✓ Parse HTML                          │
    │  ✓ Remove scripts/styles                │
    │  ✓ Extract clean text content           │
    └──────────┬──────────────────────────────┘
               │ Raw text: ~50KB - 500KB
               ▼
    ┌─────────────────────────────────────────┐
    │  Text Chunking (RecursiveCharTextSplit) │
    │  ✓ 500 char chunks                      │
    │  ✓ 100 char overlap                     │
    │  Result: ~100-1000 chunks               │
    └──────────┬──────────────────────────────┘
               │ Text chunks
               ▼
    ┌─────────────────────────────────────────┐
    │  Embedding Model (all-MiniLM-L6-v2)     │
    │  ✓ 384-dimensional vectors              │
    │  ✓ Batch embed all chunks               │
    │  ✓ Semantic meaning preserved           │
    └──────────┬──────────────────────────────┘
               │ Vector embeddings
               ▼
    ┌─────────────────────────────────────────┐
    │  Chroma Vector Store (Persistent)       │
    │  ✓ Store chunks + embeddings            │
    │  ✓ Save to disk: /data/chroma_db        │
    │  ✓ Indexed for fast retrieval           │
    └──────────┬──────────────────────────────┘
               │ (Stored & persistent)


PHASE 2: RETRIEVAL & RESPONSE (Per request)
═════════════════════════════════════════════

    ┌─────────────────────┐
    │  User Question      │
    │  "What packages     │
    │   do you offer?"    │
    └──────────┬──────────┘
               │ POST /api/ask
               ▼
    ┌─────────────────────────────────────────┐
    │  FastAPI Endpoint                       │
    │  ✓ Receive JSON request                 │
    │  ✓ Validate input                       │
    └──────────┬──────────────────────────────┘
               │ Question string
               ▼
    ┌─────────────────────────────────────────┐
    │  Embed Question                         │
    │  ✓ Use same model (all-MiniLM-L6-v2)    │
    │  ✓ Create 384-dim vector                │
    │  ✓ Question now in same embedding space │
    └──────────┬──────────────────────────────┘
               │ Question embedding
               ▼
    ┌─────────────────────────────────────────┐
    │  Vector Similarity Search               │
    │  ✓ Cosine similarity in Chroma          │
    │  ✓ Retrieve top-3 most similar chunks   │
    │  ✓ Each with relevance score            │
    └──────────┬──────────────────────────────┘
               │ [Doc1, Doc2, Doc3] + scores
               ▼
    ┌─────────────────────────────────────────┐
    │  Response Generation Options:           │
    │                                         │
    │  Option A: LLM-Based (Fallback-Free)   │
    │  ├─ Mistral-7B (local, offline)        │
    │  ├─ GPT-4 (API, requires keys)         │
    │  └─ Format: "Based on the docs..."     │
    │                                         │
    │  Option B: Retrieval-Only (Fast)       │
    │  └─ Concatenate top chunks             │
    └──────────┬──────────────────────────────┘
               │ Generated response
               ▼
    ┌─────────────────────────────────────────┐
    │  Response Package                       │
    │  {                                      │
    │    "question": "...",                   │
    │    "answer": "...",                     │
    │    "sources": [...],                    │
    │    "success": true                      │
    │  }                                      │
    └──────────┬──────────────────────────────┘
               │ JSON Response
               ▼
    ┌─────────────────────┐
    │  User/Client        │
    │  Receives Answer    │
    └─────────────────────┘
```

## 2. Docker & Container Architecture

```
┌────────────────────────────────────────────────────────────┐
│                   Docker Environment                       │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Container: vodafone-ai-assistant (Python 3.11-slim)      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                                                      │  │
│  │  Application Stack:                                 │  │
│  │  ├─ FastAPI + Uvicorn (Web Server)                 │  │
│  │  ├─ LangChain (Orchestration)                      │  │
│  │  ├─ Transformers (Model Loading)                  │  │
│  │  ├─ Chroma (Vector Store)                         │  │
│  │  └─ BeautifulSoup (Scraping)                      │  │
│  │                                                      │  │
│  │  Port: 8000 (FastAPI)                              │  │
│  │                                                      │  │
│  │  Volumes:                                           │  │
│  │  ├─ /app/data (Chroma DB persistence)              │  │
│  │  └─ /app/logs (Application logs)                   │  │
│  │                                                      │  │
│  │  Resources:                                         │  │
│  │  ├─ CPU: 2-4 cores (scalable)                      │  │
│  │  ├─ Memory: 8-16GB (for Mistral-7B)               │  │
│  │  │  or 2-3GB (retrieval-only mode)                 │  │
│  │  └─ GPU: Optional (NVIDIA for acceleration)        │  │
│  │                                                      │  │
│  │  Health Check:                                      │  │
│  │  └─ GET /api/health every 30s                      │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Volumes (Named, Persistent):                             │
│  ├─ ai_data → /app/data (Chroma database)               │
│  └─ ai_logs → /app/logs (Application logs)              │
│                                                             │
│  Network: ai_network (internal bridge)                     │
│                                                             │
└────────────────────────────────────────────────────────────┘

Startup Sequence:
1. Docker pulls Python base image
2. Installs pip dependencies (cached if unchanged)
3. Mounts volumes
4. Starts Uvicorn server
5. Loads embedding model (~2GB download)
6. Scrapes website (or loads existing embeddings)
7. Initializes Chroma vector store
8. Ready to accept requests on :8000
```

## 3. Embedding Model Selection

```
┌─────────────────────────────────────────────────────────┐
│        Embedding Model: all-MiniLM-L6-v2                │
│          (sentence-transformers library)                │
└─────────────────────────────────────────────────────────┘

PROPERTIES:
├─ Model Size: ~33MB
├─ Dimensions: 384
├─ Max Sequence Length: 256 tokens (~1,000 chars)
├─ Inference Speed: ~100-200 docs/sec on CPU
└─ Architecture: Distilled BERT (MiniLM = Mini Language Model)

WHY THIS MODEL?
┌──────────────────────────────────────────────────────┐
│ ✓ Open-source (no API keys needed)                  │
│ ✓ Fast inference (MiniLM = distilled, ~2MB/sec)    │
│ ✓ High quality for semantic similarity              │
│ ✓ Works perfectly for customer support (domain)     │
│ ✓ Low memory footprint                              │
│ ✓ Pre-trained on customer service data              │
│                                                       │
│ ✗ Not suited for: Code generation, image, audio    │
│ ✗ Smaller vector dim than large models (but faster) │
└──────────────────────────────────────────────────────┘

COMPARISON:
┌──────────────────┬──────────┬──────────┬──────────┐
│ Model            │ Speed    │ Quality  │ Cost     │
├──────────────────┼──────────┼──────────┼──────────┤
│ all-MiniLM-L6v2  │ ⭐⭐⭐⭐⭐ │ ⭐⭐⭐⭐   │ FREE     │
│ all-mpnet-v2     │ ⭐⭐⭐   │ ⭐⭐⭐⭐⭐ │ FREE     │
│ text-davinci-003 │ ⭐⭐    │ ⭐⭐⭐⭐⭐ │ $$ (API) │
│ Cohere           │ ⭐⭐    │ ⭐⭐⭐⭐   │ $$$ API  │
└──────────────────┴──────────┴──────────┴──────────┘

CHOSEN FOR: Speed + Quality + Cost = BEST for this use case
```

## 4. Vector Store: Chroma

```
┌────────────────────────────────────────────────────────┐
│         Vector Store: Chroma DB                        │
│     (Persistent, Local, Production-Ready)              │
└────────────────────────────────────────────────────────┘

STORAGE STRUCTURE:
data/
└── chroma_db/
    ├── chroma.sqlite3 (Metadata database)
    ├── index/
    │   └── id2doc.pkl (Vector index)
    └── logs/

HOW IT WORKS:
1. Text chunks stored with their embeddings
2. SQLite for metadata (chunk text, source, etc.)
3. Efficient indexing for cosine similarity search
4. Each query = normalize question embedding + cosine dist

RETRIEVAL (Cosine Similarity):
                    A · B
            cos(θ) = ─────────
                    |A| |B|

Where:
- A = Question embedding (384 dims)
- B = Stored chunk embedding (384 dims)
- Result: Score between 0 (unrelated) and 1 (identical)

Top-3 Retrieval Example:
┌──────────────────────────────────────────┐
│ Question: "Do you offer 5G?"             │
│ Embedding: [0.1, -0.2, 0.8, ...]        │
│                                          │
│ Vector Store Search:                     │
│ ├─ Chunk 1: "5G coverage in..." (0.89) ✓│
│ ├─ Chunk 2: "Mobile networks..." (0.76) │
│ └─ Chunk 3: "Fiber optics..." (0.42)   │
│                                          │
│ Retrieved: Top 3 chunks                  │
└──────────────────────────────────────────┘

ALTERNATIVES & WHY CHROMA:
├─ Pinecone: Requires cloud, $$
├─ Weaviate: Complex setup, more features than needed
├─ FAISS: Vector-only, no metadata
├─ Qdrant: Great but more infrastructure needed
└─ Chroma: ✓ Simple, local, persistent, perfect for MVP
```

## 5. AWS Deployment Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                  AWS Deployment Architecture                      │
│                     (Multi-Region, HA)                           │
└──────────────────────────────────────────────────────────────────┘

                         Internet
                            │
                            ▼
         ┌──────────────────────────────────┐
         │  CloudFront CDN (Edge Locations) │
         │  ✓ Cache API responses           │
         │  ✓ Compress responses            │
         │  ✓ DDoS protection (AWS Shield)  │
         └──────────────┬───────────────────┘
                        │
         ┌──────────────▼───────────────────┐
         │  API Gateway / ALB               │
         │  ✓ Route requests                │
         │  ✓ Rate limiting                 │
         │  ✓ Request validation            │
         │  ✓ CORS handling                 │
         └──────────────┬───────────────────┘
                        │
         ┌──────────────▼──────────────────────────┐
         │      Auto-Scaling Group (ECS/EKS)      │
         │  ┌────────────────────────────────────┐ │
         │  │ Task 1: FastAPI Container          │ │
         │  │ - 2 CPU, 4GB mem                   │ │
         │  │ - Port 8000                        │ │
         │  └────────────────────────────────────┘ │
         │  ┌────────────────────────────────────┐ │
         │  │ Task 2: FastAPI Container          │ │
         │  │ - 2 CPU, 4GB mem                   │ │
         │  │ - Port 8000                        │ │
         │  └────────────────────────────────────┘ │
         │  ┌────────────────────────────────────┐ │
         │  │ Task N: FastAPI Container          │ │
         │  │ (Auto-scales 1-10 based on load)   │ │
         │  └────────────────────────────────────┘ │
         │                                          │
         │  Scale triggers:                         │
         │  - CPU > 70% → add 1 task                │
         │  - Memory > 80% → add 1 task             │
         │  - Queue length > 10 → add 1 task        │
         └──────────────┬───────────────────────────┘
                        │
         ┌──────────────▼─────────────────────────────┐
         │  Shared Services (All tasks access)       │
         │                                            │
         │  OpenSearch (Vector Store)                │
         │  ├─ 3 nodes (HA across AZs)               │
         │  ├─ Persistent volume (EBS)               │
         │  ├─ Snapshot backup daily                 │
         │  └─ Replicas for HA                       │
         │                                            │
         │  ElastiCache (Redis)                      │
         │  ├─ Cache embeddings (avoid recompute)    │
         │  ├─ Session management                    │
         │  └─ Rate limiting counters                │
         │                                            │
         │  RDS Aurora PostgreSQL                    │
         │  ├─ Audit logs                            │
         │  ├─ User sessions                         │
         │  └─ Analytics data                        │
         │                                            │
         │  S3 (Data Lake)                           │
         │  ├─ Backup vector store (daily)           │
         │  ├─ Backup scraped content                │
         │  └─ Lifecycle policies (move to Glacier)  │
         │                                            │
         └──────────┬───────────────────────────────┘
                    │
         ┌──────────▼──────────────────────────────┐
         │  Data Ingestion Pipeline                │
         │                                          │
         │  Lambda Function (Scheduled)             │
         │  ├─ EventBridge rule: Daily @ 3 AM UTC  │
         │  ├─ Trigger: Scrape VodafoneZiggo       │
         │  ├─ Store raw content in S3              │
         │  ├─ Trigger ECS task for embedding      │
         │  └─ Update OpenSearch                    │
         │                                          │
         │  SageMaker (Model Optimization)         │
         │  ├─ Fine-tune embeddings on domain data │
         │  ├─ A/B test model versions             │
         │  └─ Deploy to OpenSearch                │
         │                                          │
         └──────────┬──────────────────────────────┘
                    │
         ┌──────────▼────────────────────────────┐
         │  Monitoring & Logging                 │
         │                                        │
         │  CloudWatch (All metrics)              │
         │  ├─ API response times                 │
         │  ├─ Container CPU/memory               │
         │  ├─ Vector store latency               │
         │  └─ Error rates                        │
         │                                        │
         │  X-Ray (Distributed Tracing)          │
         │  └─ Request flow visualization         │
         │                                        │
         │  SNS Alerts                            │
         │  └─ Notify ops team on threshold       │
         │                                        │
         └────────────────────────────────────────┘

DEPLOYMENT FLOW:
1. Developer commits to GitHub
2. CodePipeline triggered
3. CodeBuild: Build Docker image, run tests
4. Push to ECR (Elastic Container Registry)
5. CodeDeploy: Deploy to ECS task definition
6. Update service to new image
7. CloudWatch monitors health
```

## 6. AWS Service Justification

```
┌────────────────────────────────────────────────────────────┐
│              Why These AWS Services?                       │
└────────────────────────────────────────────────────────────┘

SERVICE             PURPOSE                 ALTERNATIVE  WHY CHOSEN
────────────────────────────────────────────────────────────────
ECR                 Container images        DockerHub    VPC integrated
ECS Fargate         Container orchestration Lambda       Long-running, no servers
OpenSearch          Vector store            Pinecone     AWS-native, scales
ElastiCache/Redis   Caching                 Local cache  Distributed, HA
RDS Aurora          Metadata                DynamoDB     SQL queries easier
S3                  Object storage          EBS volumes  Lifecycle policies
Lambda              Scheduled scraping      CRON jobs    Event-driven
SageMaker           Model training          Local GPU    Managed training
CloudWatch          Monitoring              Datadog      Built-in, cost-effective
API Gateway         API management          ALB          Native auth, rate limit
SNS                 Alerting                SQS          Pub/sub, flexible

KEY BENEFITS:
✓ No infrastructure management (Fargate)
✓ Auto-scaling built-in
✓ Fully managed vector store (OpenSearch)
✓ Cost-effective (pay per use)
✓ High availability across AZs
✓ Integrated security (IAM, encryption)
✓ Audit logging (CloudTrail)
```

---

## Summary

This architecture supports:
- **Scalability**: Auto-scaling from 1 to 1000+ concurrent users
- **Reliability**: Multi-AZ deployment, backup & restore
- **Performance**: Vector search in <50ms with OpenSearch
- **Cost**: Pay-per-use model, ~$100-500/month at scale
- **Security**: VPC isolation, encryption, IAM access control
- **Monitoring**: Real-time observability with CloudWatch

The prototype can grow from Docker Compose → AWS ECS → EKS with minimal code changes.
