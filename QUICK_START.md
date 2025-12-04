# Quick Reference Guide

## 🚀 Getting Started

### Option 1: Docker (Recommended)
```bash
cd /home/syedalihassan03/technical-test
./quickstart.sh
```
**What it does:**
- Builds Docker image
- Starts container
- Waits for service readiness
- Gives you the API URL

**Time:** 2-3 minutes first run (includes model download)

### Option 2: Local Python
```bash
pip install -r requirements.txt
python init_vector_store.py --test-only
cd src
python -m uvicorn main:app --reload
```

### Option 3: Docker Compose Manual
```bash
docker-compose build
docker-compose up -d
```

---

## 📡 API Endpoints Quick Reference

### Test Health
```bash
curl http://localhost:8000/api/health
```
Response: `{"status": "healthy", "service": "...", "version": "1.0.0"}`

### Ask a Question
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What packages do you offer?"}'
```
Response:
```json
{
  "question": "What packages do you offer?",
  "answer": "Based on our documentation...",
  "sources": ["..."],
  "success": true
}
```

### Get Statistics
```bash
curl http://localhost:8000/api/stats
```
Response: Shows vector store status and document count

### Interactive Docs
Open in browser: `http://localhost:8000/docs`

---

## 🧪 Testing

### Test Everything
```bash
./test_api.sh
```

### Test Specific Endpoint
```bash
./test_api.sh http://localhost:8000
```

### Initialize Vector Store Only
```bash
python init_vector_store.py                    # From real ziggo.nl
python init_vector_store.py --test-only        # With sample data
python init_vector_store.py --url https://example.com
```

---

## 📊 Project Structure

| File | Purpose |
|------|---------|
| `src/scraper.py` | Web scraping (BeautifulSoup) |
| `src/embedding_store.py` | Vector embeddings & Chroma DB |
| `src/rag_assistant.py` | RAG pipeline & LLM integration |
| `src/main.py` | FastAPI application |
| `Dockerfile` | Container image definition |
| `docker-compose.yml` | Container orchestration |
| `requirements.txt` | Python dependencies |
| `README.md` | Full documentation |
| `ARCHITECTURE.md` | Detailed architecture & AWS |
| `DIAGRAMS.md` | Visual system diagrams |
| `SUMMARY.md` | Project summary |
| `quickstart.sh` | Automated setup script |
| `test_api.sh` | API testing script |
| `init_vector_store.py` | Standalone initialization |

---

## 🔧 Configuration

### Environment Variables (`.env`)
```env
SCRAPE_URL=https://ziggo.nl/internet    # URL to scrape
DATA_DIR=./data                          # Storage location
LOG_LEVEL=INFO                           # Logging verbosity
API_PORT=8000                            # API port
```

### Docker Compose Settings
Edit `docker-compose.yml`:
- Change `SCRAPE_URL` for different websites
- Adjust memory/CPU limits
- Enable GPU support
- Add environment variables

---

## 📚 Key Technologies

| Component | Library | Why |
|-----------|---------|-----|
| Web Scraper | BeautifulSoup | Simple, lightweight |
| Embeddings | Sentence-Transformers | Open-source, fast |
| Vector DB | Chroma | Local, persistent |
| LLM | Mistral-7B | Open-source, efficient |
| API | FastAPI | Modern, async, documented |
| Docker | Docker Compose | Easy orchestration |

---

## 🐛 Troubleshooting

### Service won't start
```bash
docker-compose logs -f ai-assistant
```
Check for:
- Port 8000 already in use
- Insufficient disk space for models
- Network issues

### Out of memory
- Run in retrieval-only mode (skip LLM)
- Reduce Mistral model size
- Use smaller embedding model
- Increase Docker memory limit

### Slow responses
- First query is slow (warming up model)
- Subsequent queries are fast
- Consider async processing
- Check container logs for errors

### Vector store not loading
```bash
# Clear persisted data
docker volume rm technical-test_ai_data

# Rebuild everything
docker-compose down
docker-compose up --build
```

---

## 🚀 Deployment

### Local
```bash
./quickstart.sh
```

### Production AWS
See `ARCHITECTURE.md` for:
- ECS/Fargate setup
- OpenSearch configuration
- Auto-scaling rules
- Monitoring setup

### Kubernetes
Docker Compose can be converted to Kubernetes manifests:
```bash
kompose convert -f docker-compose.yml
```

---

## 📈 Performance Tips

### Speed Up Queries
1. Use retrieval-only mode (skip LLM)
2. Reduce top-K from 3 to 1
3. Use smaller embedding model
4. Enable query result caching

### Reduce Memory
1. Use Phi-2 instead of Mistral-7B
2. Use quantized model versions
3. Reduce chunk size
4. Implement lazy loading

### Scale for Load
1. Increase docker-compose replicas
2. Use Kubernetes for orchestration
3. Add caching layer (Redis)
4. Use managed OpenSearch

---

## 🔐 Security Checklist

- [ ] No hardcoded API keys
- [ ] Environment variables for secrets
- [ ] CORS restricted to known domains
- [ ] HTTPS enabled in production
- [ ] Rate limiting implemented
- [ ] Input validation on all endpoints
- [ ] Audit logging enabled
- [ ] Secrets in AWS Secrets Manager

---

## 📞 Help & Support

### View Logs
```bash
docker-compose logs -f ai-assistant
docker-compose logs --tail 100
```

### Check Health
```bash
curl http://localhost:8000/api/health
```

### Debug Mode
```bash
# Set LOG_LEVEL=DEBUG in .env
# Restart container
docker-compose restart
```

### Run Tests
```bash
./test_api.sh http://localhost:8000
```

---

## 🎯 Example Questions to Try

1. "What internet speeds do you offer?"
2. "Do you have 5G coverage?"
3. "What are your customer support options?"
4. "How much does your service cost?"
5. "Can you install in my area?"
6. "What routers do you provide?"
7. "What is your cancellation policy?"

---

## 📊 Metrics to Monitor

| Metric | Target | Tool |
|--------|--------|------|
| API Response Time (p99) | < 2 seconds | CloudWatch |
| Error Rate | < 1% | CloudWatch |
| Vector Store Latency | < 100ms | CloudWatch |
| Container Memory | < 80% | CloudWatch |
| Container CPU | < 70% | CloudWatch |
| Model Load Time | < 60s | Logs |
| Embedding Time | < 1s per doc | Logs |

---

## 🚦 Status Indicators

### Healthy
```
GET /api/health → {"status": "healthy"}
GET /api/stats  → {"status": "initialized", "num_documents": >0}
```

### Issues
```
GET /api/health → {"status": "unhealthy"}
GET /api/stats  → {"status": "error"}
POST /api/ask   → HTTP 503 Service Unavailable
```

---

## 💾 Data Persistence

### What's Stored
- Chroma vector embeddings: `/data/chroma_db/`
- Application logs: `/logs/`

### Backup Strategy
- Daily backup to S3 in production
- Volume snapshots (AWS EBS)
- Retention: 30 days

### Recovery
```bash
# Restore from backup
aws s3 cp s3://backup-bucket/chroma_db.tar.gz ./
tar -xzf chroma_db.tar.gz -C ./data/
docker-compose restart
```

---

**For detailed information, see README.md, ARCHITECTURE.md, or DIAGRAMS.md**

Last Updated: December 2025
