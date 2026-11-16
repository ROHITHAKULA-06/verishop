<div align="center">

# VeriShop

### Compare product listings. See the signals behind each trust score.

A local product-discovery and trust-analysis prototype built with **FastAPI**, **React**, and **Vite**.

[Features](#-features) · [Quick start](#-quick-start) · [How scoring works](#-how-scoring-works) · [API](#-api) · [Limitations](#-important-limitations)

</div>

---

## ✨ Features

- **Product discovery:** searches public web results with general and retailer-specific queries.
- **Price extraction:** reads product offers and price metadata, retailer page state, and targeted page selectors.
- **Trust-first ranking:** sorts listings by trust score, then uses relevance and blended score as secondary signals.
- **Threshold-based review:** choose a minimum score; results below it remain visible in **Discarded** for inspection.
- **Separate website signal:** website trust is shown independently from product and seller signals.
- **Review signals:** consumes product reviews exposed in public structured page data and indexed public web mentions where available.
- **Honest missing-data handling:** unavailable prices are labelled; blocked or missing sources are reported instead of being filled with made-up live prices.
- **Local development:** no database service or cloud account is required for the default setup.

## 🚀 Quick start

### Requirements

- Python **3.10+** (Python 3.11 recommended)
- Node.js **18+** and npm
- Internet access for first-time dependency installation and live search

### Windows

1. Install Python and Node.js, ensuring both are available on `PATH`.
2. Extract the project ZIP.
3. Double-click **`setup_and_run.bat`** in the project root.
4. Wait for the API and frontend windows; the script opens the app at <http://localhost:5173>.

Keep both server windows open while using VeriShop. The first setup may take several minutes because the backend has machine-learning dependencies.

### macOS / Linux

From the extracted project root:

```bash
chmod +x setup_and_run.sh
./setup_and_run.sh
```

The script installs dependencies, starts both services, waits for readiness, opens the browser, and stops the services when you press **Ctrl+C**.

### Manual setup

**Terminal 1 — backend**

```bash
cd verishop-backend
python3 -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

# Create .env only if it does not already exist
# macOS / Linux: cp .env.example .env
# Windows:       Copy-Item .env.example .env

python run.py
```

The API runs at <http://localhost:8000>; Swagger documentation is at <http://localhost:8000/docs>.

**Terminal 2 — frontend**

```bash
cd verishop-frontend
npm install
npm run dev
```

Open the URL printed by Vite, normally <http://localhost:5173>.

## 🧭 How scoring works

1. **Discover:** several public web-search queries find candidate product pages.
2. **Extract:** VeriShop reads the page for a product title, available price, image, and any structured reviews.
3. **Assess:** product/seller signals and website signals are scored separately. Public indexed discussions may contribute when found.
4. **Rank:** results are ordered primarily by trust score, with relevance and blended score used as secondary signals.
5. **Review:** the selected minimum trust score divides results into **Meets threshold** and **Discarded**. A **Caution** or **Untrusted** verdict remains visible on the listing.

A user-selected score threshold is a filter for organizing results; it is not proof that a store or product is safe.

## 🛍️ Retailer coverage

Search queries include Amazon India, Flipkart, Myntra, Croma, Reliance Digital, Tata CLiQ, JioMart, Vijay Sales, Poorvika, Snapdeal, ShopClues, Ajio, Nykaa, Meesho, FirstCry, Pepperfry, Urban Ladder, Decathlon, and IKEA. Other pages may work when they expose compatible product metadata.

Retailers can change markup, personalize prices by size/colour/pincode/login, render content in the browser, or block automated access. VeriShop can only report links and prices it can discover and read at search time.

## 🔌 API

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/health` | Backend health |
| `POST` | `/api/v1/search` | Search and rank product listings |
| `GET` | `/api/v1/products` | Recent stored products |
| `GET` | `/api/v1/products/{id}` | Product details |
| `GET` | `/api/v1/trust/{id}` | Trust assessment |
| `WS` | `/ws/search` | WebSocket search updates |

Example request:

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"wireless headphones","max_results":50,"min_trust_score":0.5}'
```

`max_results` accepts 1–100. Search providers return a bounded, changing set of results; this value does not guarantee that many listings will be found.

## ⚙️ Configuration

Copy `verishop-backend/.env.example` to `verishop-backend/.env` if needed. The default setup uses `LLM_PROVIDER=none` and does not require an LLM key. Keep `.env` and API keys private.

The frontend uses `http://localhost:8000` by default. To point it to another API, create `verishop-frontend/.env.local`:

```env
VITE_API_URL=http://localhost:8000
```

## 🗂️ Project layout

```text
VeriShop/
├── setup_and_run.bat          # One-command Windows setup and launch
├── setup_and_run.sh           # One-command macOS/Linux setup and launch
├── verishop-backend/
│   ├── app/api/               # FastAPI routes
│   ├── app/core/              # Search and scoring orchestration
│   ├── app/layers/            # Retrieval, trust, ranking, storage
│   ├── data/                  # Local runtime data
│   └── requirements.txt
└── verishop-frontend/
    ├── src/components/        # Search, results, and score displays
    └── package.json
```

## ⚠️ Important limitations

- **Not a complete Google Shopping feed:** VeriShop uses public web-search results. It cannot guarantee every listing displayed by Google Shopping or any retailer.
- **Prices can vary:** product variant, delivery location, login state, promotions, and time can change the final price. Confirm at the retailer before buying.
- **Public pages can block access:** a missing listing may mean the search provider returned no link, the store blocked the request, or the page did not expose a readable price.
- **Reviews may be incomplete:** only publicly available structured product reviews and indexed public discussions are used. These are not authenticated platform feeds and may be sparse or stale.
- **Scores are estimates:** domain age, HTTPS, public reviews, and listing data are signals—not guarantees of seller identity, product authenticity, or transaction safety.
- **Production integrations need approval:** reliable large-scale coverage should use retailer-authorized feeds/APIs and platform-authorized review/social APIs where available.

## 🧪 Development

The backend contains a `tests/` directory. Run its test suite from `verishop-backend/` after installing dependencies:

```bash
python -m pytest
```

Build the frontend for production with:

```bash
cd verishop-frontend
npm run build
```

## 📄 License

No license is included. Add a `LICENSE` file before redistributing this project under an open-source license.
