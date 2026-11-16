# VeriShop

VeriShop is a local product discovery and comparison prototype. It includes a FastAPI backend and a React/Vite interface. Search uses several public web-search queries, then reads up to 100 discovered product pages per request (the UI defaults to 50). This is not a complete Google Shopping feed: Google does not provide a public unauthenticated endpoint for every Shopping-region result, and web-search providers return a bounded, changing set. Trust scores are heuristic signals; they are not proof that a seller or product is safe.

## Requirements

- Python 3.10 or newer (Python 3.11 is a good default)
- Node.js 18 or newer and npm
- Internet access for package installation and live search

The backend's ML dependencies (PyTorch, Transformers, FAISS and spaCy) can take time and disk space to install. Search engines and retailers may rate-limit or block requests. The application returns no fabricated live listings when that happens.

## Start the backend

From the project root:

```bash
cd verishop-backend
python3 -m venv .venv
source .venv/bin/activate           # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env                # Windows: Copy-Item .env.example .env
python run.py
```

The API is at `http://localhost:8000`; interactive API documentation is at `http://localhost:8000/docs`. Keep the terminal open while using the frontend.

## Start the frontend

In another terminal, from the project root:

```bash
cd verishop-frontend
npm install
npm run dev
```

Open the local URL Vite prints (normally `http://localhost:5173`). To point the UI at another API URL, create `verishop-frontend/.env.local` with:

```env
VITE_API_URL=http://localhost:8000
```

For a production frontend build, run `npm run build`; the output is written to `verishop-frontend/dist/`.

## Optional Docker startup

With Docker Compose installed, from `verishop-backend/` run:

```bash
docker compose up --build
```

## Search behavior and retailer coverage

The scraper uses product JSON-LD offers, price metadata, retailer product-page state, known page selectors, and published product reviews when a page exposes them. Search includes Amazon India, Flipkart, Myntra, Croma, Reliance Digital, Tata CLiQ, JioMart, Vijay Sales, Poorvika, Snapdeal, ShopClues, Ajio, Nykaa, Meesho, FirstCry, Pepperfry, Urban Ladder, Decathlon and IKEA, along with other stores that expose standard product metadata. Website trust separately weighs domain/TLS signals and indexed public reviews/social mentions from Reddit, Trustpilot, MouthShut and X. These mentions come from public web search, not authenticated platform APIs, and may be incomplete. Retailers frequently change markup, vary prices by size/colour/pincode/login, use client-rendered pages, or block automated traffic. There is no universal scraper that can guarantee extraction from every page. If a store blocks access or no unambiguous product price is present, the listing is omitted and the response reports which retrieval stage failed. Always verify the final price, variant and seller at checkout.

This project does not include retailer credentials or official affiliate/API keys. For reliable production price feeds, integrate each retailer's approved product API/feed where available. The browser-only demo mode is sample data and should not be used as live shopping information.

## API

- `GET /api/v1/health` — health status
- `POST /api/v1/search` — product search and ranking
- `GET /api/v1/products` — recent products
- `GET /api/v1/products/{id}` — product detail
- `GET /api/v1/trust/{id}` — trust assessment
- `WS /ws/search` — WebSocket search

Example:

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"wireless headphones","max_results":5}'
```

## Configuration

Copy `verishop-backend/.env.example` to `verishop-backend/.env`. Defaults run without an LLM key. `ALLOWED_ORIGINS` controls frontend CORS, `LLM_PROVIDER=none` selects the local rule-based fallback, and the database/index paths default to local `data/` paths. Never commit `.env` or API keys.

## Known limits

- Search and page availability depend on third-party services, network region and retailer anti-bot controls.
- Product variants and delivery pincode can change the displayed price.
- A trust score is a ranking aid, not a guarantee, and the scraper does not authenticate product reviews.
- Computer-vision and language model features depend on model downloads and available hardware; lazy loading is enabled by default.
