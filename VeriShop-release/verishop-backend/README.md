# VeriShop Backend

**An Agentic Multimodal Deep Learning Framework for Trust-Aware Online Shopping and Product Verification.**

## Architecture

VeriShop uses a 7-layer architecture:

| Layer | Name | Purpose |
|-------|------|---------|
| L1 | Client Layer | FastAPI REST + WebSocket API |
| L2 | Multimodal Input Processor | Text & image preprocessing |
| L3a | NLP Pipeline | CLIP text, SBERT, NER, query expansion |
| L3b | Vision Pipeline | CLIP image, structural analysis, manipulation detection |
| L4 | Seller Credibility Engine | Review auth, price anomalies, seller scoring |
| L5 | Agentic Ranking | LLM scoring, trust model, AI synthesizer |
| L6 | Storage | SQLite + FAISS vector store |
| L7 | Output & Verification | Trust verdicts, rule filters, candidate selection |

## Quick Start

```bash
# Clone and setup
cd verishop-backend
cp .env.example .env
pip install -r requirements.txt

# Run development server
python run.py
```

The API will be available at `http://localhost:8000`.

## Docker

```bash
docker-compose up --build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/search` | Search products with trust ranking |
| GET | `/api/v1/products` | List recent products |
| GET | `/api/v1/products/{id}` | Get product details |
| GET | `/api/v1/trust/{id}` | Get trust assessment |
| WS | `/ws/search` | Real-time search with progress |

### Search Example

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "wireless headphones", "max_results": 5}'
```

## Environment Variables

See `.env.example` for all configuration options. Key settings:

- `DEBUG` — Enable debug mode and hot reload
- `CLIP_MODEL_NAME` — CLIP model for embeddings
- `SBERT_MODEL_NAME` — SBERT model for text similarity
- `LLM_PROVIDER` — LLM provider (`none` for rule-based fallback)
- `LAZY_LOAD_MODELS` — Lazy-load ML models on first use

## Project Structure

```
app/
├── main.py              # FastAPI entry point
├── config.py            # Settings
├── dependencies.py      # DI providers
├── api/v1/              # REST endpoints
├── core/                # Pipeline orchestration
├── models/              # Pydantic schemas
├── layers/
│   ├── l2_input_processor/
│   ├── l3a_nlp_pipeline/
│   ├── l3b_vision_pipeline/
│   ├── l4_seller_credibility/
│   ├── l5_agentic_ranking/
│   ├── l6_storage/
│   └── l7_output/
└── utils/               # Shared utilities
```

## Testing

```bash
pytest tests/ -v
```

## Key Design Decisions

- **Explainability**: Every trust score includes contributing factors and evidence
- **Graceful Degradation**: ML models are lazy-loaded; system works with rule-based fallbacks
- **Modularity**: Each layer is independently testable
- **Zero External Dependencies**: Uses SQLite + FAISS locally (no cloud services required)
