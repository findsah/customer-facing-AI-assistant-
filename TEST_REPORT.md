# End-to-End Test Report

Date: 2025-12-04
Environment: Python 3.11 (venv), FastAPI + Uvicorn
Server: http://localhost:8000 (dev) / http://localhost:8001 (alt)

## Tests Run

1) Health Check
- Command: `curl -s http://localhost:8000/api/health`
- Result: `{ "status": "healthy", "service": "VodafoneZiggo Customer Assistant", "version": "1.0.0" }`

2) Vector Store Stats
- Command: `curl -s http://localhost:8000/api/stats`
- Result: `{ "status": "initialized", "collection_name": "vodafone_ziggo", "num_documents": 4 }`

3) Q&A: Internet Speeds
- Command:
  ```bash
  curl -s -X POST http://localhost:8000/api/ask \
    -H 'Content-Type: application/json' \
    -d '{"question":"What internet speeds do you offer?"}'
  ```
- Expected: Mentions fiber/cable/5G with speeds; includes source chunks
- Observed: Answer contains speeds up to 1 Gbps and 500 Mbps; 3 sources returned

4) Q&A: Pricing
- Command:
  ```bash
  curl -s -X POST http://localhost:8000/api/ask \
    -H 'Content-Type: application/json' \
    -d '{"question":"How much does your service cost?"}'
  ```
- Expected: Mentions package prices and installation cost; includes sources
- Observed: Shows packages €35/€55/€75 and installation €50; 3 sources returned

## Notes
- Fix applied: TF-IDF vectorizer is now refit from stored documents on load, preventing dimension mismatch errors during retrieval.
- Fallback LLM mode is active (no external API key); responses are composed from retrieved chunks.

## Quick Run
```bash
# Start the API (dev)
source venv/bin/activate
python3 -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run E2E tests
./scripts/test_e2e.sh http://localhost:8000
```
