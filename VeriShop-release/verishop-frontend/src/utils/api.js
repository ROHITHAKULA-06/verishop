/**
 * VeriShop API Client & Mock Data Provider
 * Handles backend communication with http://localhost:8000 and offline mock fallbacks.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Perform product search via VeriShop backend
 * @param {Object} params
 * @param {string} [params.query]
 * @param {string} [params.image_base64]
 * @param {string} [params.image_url]
 * @param {number} [params.max_results=50]
 * @param {number} [params.min_trust_score=0.0]
 * @param {boolean} [params.include_evidence=true]
 * @param {AbortSignal} [signal]
 * @returns {Promise<Object>} SearchResponse
 */
export async function searchProducts(params, signal) {
  const {
    query,
    image_base64,
    image_url,
    max_results = 50,
    min_trust_score = 0.0,
    include_evidence = true,
  } = params;

  const payload = {
    query: query?.trim() || null,
    image_base64: image_base64 || null,
    image_url: image_url || null,
    max_results: Number(max_results),
    min_trust_score: Number(min_trust_score),
    include_evidence: Boolean(include_evidence),
  };

  try {
    const response = await fetch(`${API_BASE}/api/v1/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      signal,
    });

    if (!response.ok) {
      let errorDetail = `HTTP error ${response.status}: ${response.statusText}`;
      try {
        const errorJson = await response.json();
        errorDetail = errorJson.detail || errorJson.error || errorDetail;
      } catch {
        // use fallback statusText
      }
      throw new Error(errorDetail);
    }

    const data = await response.json();
    return data;
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error('Search request was cancelled.');
    }
    // Re-throw with enriched message if connection refused
    if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
      const connErr = new Error(
        `Unable to connect to VeriShop backend at ${API_BASE}. Please ensure the server is running on port 8000.`
      );
      connErr.isNetworkError = true;
      throw connErr;
    }
    throw err;
  }
}

/**
 * Check backend health status
 * @returns {Promise<Object>}
 */
export async function checkBackendHealth() {
  try {
    const response = await fetch(`${API_BASE}/api/v1/health`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    if (!response.ok) {
      throw new Error(`Health check returned status ${response.status}`);
    }
    return await response.json();
  } catch (err) {
    throw new Error(`Backend unavailable at ${API_BASE}`);
  }
}

/**
 * Realistic Mock Data for Demo & Testing when backend is offline
 */
export function getMockSearchResults(query = 'iPhone 15 Pro') {
  return {
    request_id: 'mock-req-' + Math.random().toString(36).substring(2, 9),
    query_type: 'TEXT',
    total_found: 5,
    processing_time_ms: 1840.5,
    metadata: {
      source_count: 5,
      cached: false,
      algorithm_version: 'v2.4-agentic',
    },
    results: [
      {
        rank: 1,
        relevance_score: 0.98,
        blended_score: 0.94,
        explanation: 'Verified official retail partner with valid SSL, aged domain (17+ yrs), pristine Reddit community consensus, and authentic seller credentials.',
        product: {
          id: 'prod-001-apple',
          title: 'Apple iPhone 15 Pro (128 GB) - Natural Titanium',
          description: 'A17 Pro chip, aerospace-grade titanium design with textured matte glass back, Action button, and 48MP main camera.',
          pricing: {
            price: 129900.0,
            original_price: 134900.0,
            discount_pct: 3.7,
            currency: 'INR',
          },
          source: {
            source_name: 'amazon.in',
            source_url: 'https://www.amazon.in/dp/B0CHWV2WYK',
          },
          seller_name: 'Appario Retail Pvt Ltd (Authorized Apple Reseller)',
          images: [
            {
              url: 'https://images.unsplash.com/photo-1695048133142-1a20484d2569?auto=format&fit=crop&w=600&q=80',
              is_primary: true,
            },
          ],
        },
        trust_score: {
          overall_score: 0.94,
          verdict: 'TRUSTED',
          confidence: 0.96,
          risk_flags: [],
          factors: [
            {
              name: 'SSL Certificate',
              factor_name: 'SSL Certificate',
              score: 0.98,
              weight: 0.25,
              evidence: [
                'Valid Extended Validation (EV) SSL certificate from DigiCert Inc.',
                'TLS 1.3 protocol enabled with forward secrecy',
                'Certificate valid for another 284 days',
              ],
            },
            {
              name: 'Domain Age & History',
              factor_name: 'Domain Age & History',
              score: 0.96,
              weight: 0.25,
              evidence: [
                'Domain registered in 2004 (20+ years of active history)',
                'Clean DNS record with DNSSEC validation active',
                'Zero registered scam or phishing incident reports',
              ],
            },
            {
              name: 'Reddit & Community Reviews',
              factor_name: 'Reddit & Community Reviews',
              score: 0.91,
              weight: 0.25,
              evidence: [
                'Sentiment analysis across r/IndiaTech and r/apple: 92% positive sentiment',
                'No report of counterfeit or empty box delivery for this seller ID',
                'Verified delivery confirmation frequency > 99.4%',
              ],
            },
            {
              name: 'Seller Credibility',
              factor_name: 'Seller Credibility',
              score: 0.93,
              weight: 0.25,
              evidence: [
                'Authorized Tier-1 brand distributor status verified',
                'Return and replacement policy explicitly honors Apple 1-Year India Warranty',
                '4.8/5 seller feedback rating over 120,000+ customer reviews',
              ],
            },
          ],
        },
      },
      {
        rank: 2,
        relevance_score: 0.95,
        blended_score: 0.91,
        explanation: 'Top e-commerce platform with Flipkart Assured certification, verified GSTIN, high buyer satisfaction, and secure payment gateway.',
        product: {
          id: 'prod-002-flipkart',
          title: 'Apple iPhone 15 Pro (Natural Titanium, 128 GB)',
          description: 'Experience titanium strength, Super Retina XDR display with ProMotion up to 120Hz, and USB-C with USB 3 speeds.',
          pricing: {
            price: 128999.0,
            original_price: 134900.0,
            discount_pct: 4.3,
            currency: 'INR',
          },
          source: {
            source_name: 'flipkart.com',
            source_url: 'https://www.flipkart.com/apple-iphone-15-pro-natural-titanium-128-gb/p/itm12345678',
          },
          seller_name: 'IndiFlashMart (Flipkart Assured)',
          images: [
            {
              url: 'https://images.unsplash.com/photo-1592750475338-74b7b21085ab?auto=format&fit=crop&w=600&q=80',
              is_primary: true,
            },
          ],
        },
        trust_score: {
          overall_score: 0.89,
          verdict: 'TRUSTED',
          confidence: 0.92,
          risk_flags: [],
          factors: [
            {
              name: 'SSL Certificate',
              factor_name: 'SSL Certificate',
              score: 0.95,
              weight: 0.25,
              evidence: [
                'Valid RSA 2048-bit certificate issued by DigiCert Global Root CA',
                'Strict Transport Security (HSTS) with preloading enabled',
              ],
            },
            {
              name: 'Domain Age & Authority',
              factor_name: 'Domain Age & Authority',
              score: 0.94,
              weight: 0.25,
              evidence: [
                'Domain active since 2007 (17+ years)',
                'High domain authority rank #12 in India e-commerce category',
              ],
            },
            {
              name: 'Reddit Consensus',
              factor_name: 'Reddit Consensus',
              score: 0.82,
              weight: 0.25,
              evidence: [
                'Discussions on r/India: Open-box delivery option recommended',
                'High buyer confidence when Flipkart Assured badge is verified',
              ],
            },
            {
              name: 'Connection Security',
              factor_name: 'Connection Security',
              score: 0.92,
              weight: 0.25,
              evidence: [
                'PCI-DSS Compliant checkout architecture',
                'Tokenized card storage and UPI verification protocol',
              ],
            },
          ],
        },
      },
      {
        rank: 3,
        relevance_score: 0.92,
        blended_score: 0.85,
        explanation: 'Major national brick-and-mortar electronics retail chain. Reliable warranty service with in-store pickup option.',
        product: {
          id: 'prod-003-croma',
          title: 'Apple iPhone 15 Pro (128GB ROM, 8GB RAM, Black Titanium)',
          description: '6.1-inch Super Retina XDR OLED Display, Dynamic Island, A17 Pro Chip Hexa Core Processor, Tata Retail assurance.',
          pricing: {
            price: 130900.0,
            original_price: 134900.0,
            discount_pct: 2.9,
            currency: 'INR',
          },
          source: {
            source_name: 'croma.com',
            source_url: 'https://www.croma.com/apple-iphone-15-pro-128gb-black-titanium/p/300762',
          },
          seller_name: 'Infiniti Retail Ltd (A Tata Enterprise)',
          images: [
            {
              url: 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=600&q=80',
              is_primary: true,
            },
          ],
        },
        trust_score: {
          overall_score: 0.88,
          verdict: 'TRUSTED',
          confidence: 0.90,
          risk_flags: [],
          factors: [
            {
              name: 'SSL Certificate',
              factor_name: 'SSL Certificate',
              score: 0.92,
              weight: 0.25,
              evidence: [
                'Valid SSL issued by GeoTrust TLS RSA CA G1',
                'Zero protocol vulnerabilities detected',
              ],
            },
            {
              name: 'Domain Reputation',
              factor_name: 'Domain Reputation',
              score: 0.91,
              weight: 0.25,
              evidence: [
                'Official web portal for Croma / Tata Enterprise',
                'Physical showroom network backs customer redressal',
              ],
            },
            {
              name: 'Reddit Feedback',
              factor_name: 'Reddit Feedback',
              score: 0.85,
              weight: 0.25,
              evidence: [
                'Positive reviews for direct store collection and warranty honoring',
                'Minimal shipping complaint reports on consumer forums',
              ],
            },
            {
              name: 'Price Consistency',
              factor_name: 'Price Consistency',
              score: 0.86,
              weight: 0.25,
              evidence: [
                'Matches authorized retail MSRP with standard bank card discount',
                'No anomalous discount flags detected',
              ],
            },
          ],
        },
      },
      {
        rank: 4,
        relevance_score: 0.86,
        blended_score: 0.72,
        explanation: 'Regional refurbished electronics retailer. Authentic warranty provided, but buyer should note pre-owned status and shorter warranty period.',
        product: {
          id: 'prod-004-cashify',
          title: 'Apple iPhone 15 Pro - Refurbished Superb Condition (128 GB)',
          description: 'Tested across 32 quality checkpoints, 100% functional, 6-month warranty included.',
          pricing: {
            price: 94999.0,
            original_price: 134900.0,
            discount_pct: 29.5,
            currency: 'INR',
          },
          source: {
            source_name: 'cashify.in',
            source_url: 'https://www.cashify.in/buy-refurbished-mobile-phones/apple-iphone-15-pro',
          },
          seller_name: 'Cashify Certified Refurbished',
          images: [
            {
              url: 'https://images.unsplash.com/photo-1574944985070-8f3ebc6b79d2?auto=format&fit=crop&w=600&q=80',
              is_primary: true,
            },
          ],
        },
        trust_score: {
          overall_score: 0.68,
          verdict: 'CAUTION',
          confidence: 0.82,
          risk_flags: [
            'Refurbished unit: original Apple warranty may be lapsed',
            'Non-OEM replacement parts possible for minor repairs',
          ],
          factors: [
            {
              name: 'SSL Certificate',
              factor_name: 'SSL Certificate',
              score: 0.92,
              weight: 0.25,
              evidence: ['Valid SSL issued by Cloudflare Inc ECC CA-3'],
            },
            {
              name: 'Domain Age',
              factor_name: 'Domain Age',
              score: 0.88,
              weight: 0.25,
              evidence: ['Domain registered 10+ years ago, verified company entity'],
            },
            {
              name: 'Community Feedback',
              factor_name: 'Community Feedback',
              score: 0.62,
              weight: 0.25,
              evidence: [
                'Mixed Reddit feedback on refurbished battery health degradation',
                'Return process can require multiple inspections',
              ],
            },
            {
              name: 'Warranty Scope',
              factor_name: 'Warranty Scope',
              score: 0.58,
              weight: 0.25,
              evidence: [
                'Third-party seller warranty (6 months) instead of official 12-month manufacturer warranty',
              ],
            },
          ],
        },
      },
      {
        rank: 5,
        relevance_score: 0.74,
        blended_score: 0.28,
        explanation: 'CRITICAL ALERT: Newly registered domain offering an unrealistically deep 80% discount. Multiple scam indicators and missing legal identity.',
        product: {
          id: 'prod-005-scam',
          title: 'Brand New Apple iPhone 15 Pro 256GB - Factory Sealed Flash Sale',
          description: 'Hurry up! Clearance sale with 80% OFF. Direct import from manufacturer, free shipping today only.',
          pricing: {
            price: 24999.0,
            original_price: 134900.0,
            discount_pct: 81.5,
            currency: 'INR',
          },
          source: {
            source_name: 'super-tech-clearance-deals.shop',
            source_url: 'https://super-tech-clearance-deals.shop/products/iphone15pro-sale',
          },
          seller_name: 'Global Deals Hub International (Unregistered)',
          images: [
            {
              url: 'https://images.unsplash.com/photo-1580910051074-3eb694886505?auto=format&fit=crop&w=600&q=80',
              is_primary: true,
            },
          ],
        },
        trust_score: {
          overall_score: 0.18,
          verdict: 'UNTRUSTED',
          confidence: 0.95,
          risk_flags: [
            'Domain registered only 11 days ago (whois privacy protected)',
            'Price anomaly: 81.5% below median retail pricing',
            'No verified physical address, corporate registration, or GSTIN found',
            'Prepaid-only checkout with untraceable QR UPI payment gateway',
            'Free basic SSL certificate with shared host IP flagged for prior phishing',
          ],
          factors: [
            {
              name: 'SSL Certificate & Host Security',
              factor_name: 'SSL Certificate & Host Security',
              score: 0.35,
              weight: 0.25,
              evidence: [
                'Basic Let\'s Encrypt free certificate issued 11 days ago',
                'IP address shared with 420 other suspicious parked domains',
              ],
            },
            {
              name: 'Domain Age & WHOIS',
              factor_name: 'Domain Age & WHOIS',
              score: 0.08,
              weight: 0.25,
              evidence: [
                'Domain age: 11 days old (High phishing risk threshold < 30 days)',
                'Registrant identity masked via privacy proxy in Panama',
              ],
            },
            {
              name: 'Community & Blacklist Check',
              factor_name: 'Community & Blacklist Check',
              score: 0.12,
              weight: 0.25,
              evidence: [
                'Flagged on 2 open-source anti-phishing blacklists',
                'Identical site template used in reported Instagram ad scam campaign',
              ],
            },
            {
              name: 'Price Anomaly Check',
              factor_name: 'Price Anomaly Check',
              score: 0.15,
              weight: 0.25,
              evidence: [
                'Price deviation: 81.5% below brand MSRP',
                'Probability of legitimate retail fulfillment < 1.2%',
              ],
            },
          ],
        },
      },
    ],
  };
}
