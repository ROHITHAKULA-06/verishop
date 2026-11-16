"""
L1.5 — Live Web Scraper using BeautifulSoup.
Scrapes real product pages and extracts data with robust site-specific price extraction.
"""
import asyncio
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.utils.logger import get_logger

logger = get_logger(__name__)


class WebScraper:
    """Scrapes a real product URL and extracts available product data."""

    # Do not exclude legitimate low-cost products (accessories, apparel, etc.).
    MIN_PRICE = 1.0
    MAX_PRICE = 10_00_000.0  # ₹10 lakh

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    ]

    def _get_headers(self, user_agent: str) -> Dict[str, str]:
        return {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
            "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }

    async def scrape(self, url: str, search_title: str = "", search_snippet: str = "") -> Optional[Dict[str, Any]]:
        """
        Scrape a URL and return a raw dict of extracted data.
        Handles bot detection (e.g. HTTP 503) and falls back to search snippet/title.
        """
        domain = urlparse(url).netloc
        is_https = url.startswith("https://")

        html: Optional[str] = None
        for attempt in range(2):
            ua = self.USER_AGENTS[attempt % len(self.USER_AGENTS)]
            headers = self._get_headers(ua)
            try:
                async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=headers) as client:
                    response = await client.get(url)
                    # Amazon bot detection often returns 503; others may return 403 or 429
                    if response.status_code in (503, 403, 429):
                        if attempt == 0:
                            await asyncio.sleep(0.5)
                            continue
                        logger.warning("scraper_bot_blocked", url=url, status_code=response.status_code)
                        return self._create_blocked_fallback(url, search_title, search_snippet)

                    response.raise_for_status()
                    html = response.text
                    break
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (503, 403, 429):
                    if attempt == 0:
                        await asyncio.sleep(0.5)
                        continue
                    logger.warning("scraper_http_blocked", url=url, status=e.response.status_code)
                    return self._create_blocked_fallback(url, search_title, search_snippet)
                logger.warning("scraper_http_error", url=url, error=str(e))
                return self._create_blocked_fallback(url, search_title, search_snippet)
            except Exception as e:
                if attempt == 0:
                    await asyncio.sleep(0.5)
                    continue
                logger.warning("scrape_failed", url=url, error=str(e))
                return self._create_blocked_fallback(url, search_title, search_snippet)

        if not html:
            return self._create_blocked_fallback(url, search_title, search_snippet)

        try:
            soup = BeautifulSoup(html, "html.parser")

            # Title: prefer og:title > <title> > search_title
            og_title = soup.find("meta", property="og:title")
            page_title = og_title["content"].strip() if og_title and og_title.get("content") else None
            if not page_title and soup.title and soup.title.string:
                page_title = soup.title.string.strip()
            if not page_title:
                page_title = search_title or f"Product from {domain}"

            # Description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            og_desc = soup.find("meta", property="og:description")
            description = ""
            if og_desc and og_desc.get("content"):
                description = og_desc["content"].strip()
            elif meta_desc and meta_desc.get("content"):
                description = meta_desc["content"].strip()
            elif search_snippet:
                description = search_snippet

            # Price extraction
            price = self._extract_price_for_page(soup, html, domain, page_title, description, search_snippet)

            # Image
            og_image = soup.find("meta", property="og:image")
            image_url = og_image["content"] if og_image and og_image.get("content") else None

            return {
                "url": url,
                "domain": domain,
                "is_https": is_https,
                "title": page_title[:300],
                "description": description[:2000],
                "price": price,
                "image_url": image_url,
                "reviews": self._extract_reviews_from_json_ld(soup),
                "scraped_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.warning("scrape_parse_failed", url=url, error=str(e))
            return self._create_blocked_fallback(url, search_title, search_snippet)

    def _create_blocked_fallback(self, url: str, search_title: str, search_snippet: str) -> Dict[str, Any]:
        """Return product dict when blocked or scraping fails, extracting from snippet."""
        domain = urlparse(url).netloc
        return {
            "url": url,
            "domain": domain,
            "is_https": url.startswith("https://"),
            "title": search_title or f"Product from {domain}",
            "description": search_snippet or "",
            # Search snippets are stale and may describe a different variant.
            # A price is reported only when extracted from the product page.
            "price": None,
            "price_status": "unavailable",
            "image_url": None,
            "reviews": [],
            "scraped_at": datetime.now().isoformat(),
        }

    def _extract_reviews_from_json_ld(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract published Product review entries; never synthesize reviews."""
        import json
        reviews: List[Dict[str, Any]] = []

        def walk(node: Any):
            if isinstance(node, list):
                for child in node:
                    walk(child)
            elif isinstance(node, dict):
                kind = node.get("@type", [])
                kinds = [kind] if isinstance(kind, str) else kind
                if any(str(value).lower() == "product" for value in kinds):
                    values = node.get("review", [])
                    values = values if isinstance(values, list) else [values]
                    for review in values:
                        if not isinstance(review, dict):
                            continue
                        rating = review.get("reviewRating", {})
                        if isinstance(rating, dict):
                            rating = rating.get("ratingValue")
                        try:
                            rating = float(rating)
                        except (TypeError, ValueError):
                            continue
                        if not 0 <= rating <= 5:
                            continue
                        author = review.get("author", {})
                        if isinstance(author, dict):
                            author = author.get("name", "")
                        reviews.append({
                            "reviewer_id": str(author or "public-review")[:120],
                            "rating": rating,
                            "text": str(review.get("reviewBody") or review.get("description") or "")[:2000],
                            "created_at": review.get("datePublished"),
                        })
                for key, child in node.items():
                    if key in {"@graph", "mainEntity", "mainEntityOfPage"}:
                        walk(child)

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                walk(json.loads(script.string or ""))
            except (ValueError, TypeError):
                continue
        return reviews[:50]

    def _is_valid_price(self, price: Optional[float]) -> bool:
        """Filter out obviously wrong prices like shipping fees (< ₹200) and unreasonably high values."""
        if price is None:
            return False
        return self.MIN_PRICE <= price <= self.MAX_PRICE

    def _clean_price_string(self, text: Optional[str]) -> Optional[float]:
        """Parse numeric price from text."""
        if not text:
            return None
        m = re.search(r'([\d,]+(?:\.\d{1,2})?)', str(text))
        if not m:
            return None
        raw = m.group(1).replace(",", "")
        try:
            return float(raw)
        except ValueError:
            return None

    def _extract_price_for_page(
        self,
        soup: BeautifulSoup,
        html: str,
        domain: str,
        page_title: str,
        description: str,
        search_snippet: str,
    ) -> Optional[float]:
        """Multi-stage price extraction: site-specific -> structured -> regex -> snippet."""
        d = domain.lower()
        price: Optional[float] = None

        # Prefer schema.org offers and explicit price metadata first. Both are
        # tied to the product page and avoid picking a recommendation card.
        price = self._extract_from_json_ld(soup)
        if self._is_valid_price(price):
            return price

        price = self._extract_from_meta(soup)
        if self._is_valid_price(price):
            return price

        # Retailer state and specific product-page selectors cover stores whose
        # public pages omit standard structured metadata.
        price = self._extract_product_state(soup, html)
        if self._is_valid_price(price):
            return price

        # Do not parse prose/snippets: they routinely contain MRP, EMI,
        # shipping, or prices for another item. Unknown is safer than wrong.
        return None

    def _extract_product_state(self, soup: BeautifulSoup, html: str) -> Optional[float]:
        """Read product/offer data embedded by retailers (including Myntra state)."""
        import json

        # Product-specific attributes used by Shopify, Magento, and storefronts.
        for selector in (
            '[itemprop="price"]', '[data-testid*="price"]', '[data-price]',
            '[class*="pdp-price"]', '[class*="product-price"]',
            '[class*="selling-price"]', '[class*="sale-price"]',
            '.a-price .a-offscreen', '.a-price-whole', '._30jeq3',
            '[class*="pdp__offerPrice"]', '[class*="new-price"]',
            '[class*="main-price"]', '[class*="price-box"]',
            '[class*="final-price"]', '[class*="prc-val"]',
        ):
            for node in soup.select(selector)[:8]:
                raw = node.get('content') or node.get('data-price') or node.get_text(" ", strip=True)
                value = self._clean_price_string(raw)
                if self._is_valid_price(value):
                    return value

        # Parse JSON state instead of regexing arbitrary HTML. Only recognize
        # known selling-price keys, and check retailer-specific state first.
        keys = ("discountedPrice", "sellingPrice", "salePrice", "priceAmount", "currentPrice")
        for script in soup.find_all("script"):
            raw = script.string or script.get_text()
            if not raw or not ("price" in raw.lower()):
                continue
            try:
                data = json.loads(raw.strip())
            except (ValueError, TypeError):
                continue
            candidates = self._state_prices(data, keys)
            for candidate in candidates:
                value = self._clean_price_string(candidate)
                if self._is_valid_price(value):
                    return value

        # Myntra occasionally embeds `pdpData` in a JavaScript assignment,
        # which is not valid standalone JSON. Restrict this fallback to that
        # product-state block; never scan the whole page for arbitrary prices.
        if html:
            marker = re.search(r"pdpData\s*[:=]", html, re.IGNORECASE)
            if marker:
                state = html[marker.end():marker.end() + 120_000]
                for field in ("discountedPrice", "sellingPrice", "price"):
                    match = re.search(
                        rf'["\']{field}["\']\s*:\s*["\']?([\d,]+(?:\.\d{{1,2}})?)',
                        state,
                        re.IGNORECASE,
                    )
                    if match:
                        value = self._clean_price_string(match.group(1))
                        if self._is_valid_price(value):
                            return value
        return None

    def _state_prices(self, data: Any, keys: tuple, depth: int = 0, product_context: bool = False) -> List[str]:
        if depth > 18:
            return []
        found: List[str] = []
        if isinstance(data, dict):
            kind = data.get("@type", [])
            kinds = [kind] if isinstance(kind, str) else kind
            product_context = product_context or any(
                str(value).lower() in {"product", "productgroup"} for value in kinds
            )
            # Myntra pdpData uses price, mrp and discount fields together;
            # discountedPrice is preferred. Generic price is used only when
            # no explicit selling-price key is present in that object.
            if product_context:
                for key in keys:
                    value = data.get(key)
                    if isinstance(value, (str, int, float)) and not isinstance(value, bool):
                        found.append(str(value))
            for key, value in data.items():
                child_context = product_context or key.lower() in {
                    "product", "productdata", "pdpdata", "productdetails", "item", "itemdata"
                }
                if child_context and key.lower() == "price" and isinstance(value, (str, int, float)):
                    found.append(str(value))
                if isinstance(value, (dict, list)):
                    found.extend(self._state_prices(value, keys, depth + 1, child_context))
        elif isinstance(data, list):
            for value in data[:100]:
                found.extend(self._state_prices(value, keys, depth + 1, product_context))
        return found

    # ── Site-Specific Extractors ──

    def _extract_amazon_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Amazon: JSON-LD -> 'a-price-whole' class -> meta tags."""
        # 1. JSON-LD
        price = self._extract_from_json_ld(soup)
        if self._is_valid_price(price):
            return price

        # 2. 'a-price-whole' class text
        whole_tag = soup.find(class_=re.compile(r"a-price-whole"))
        if whole_tag:
            val = self._clean_price_string(whole_tag.get_text())
            if self._is_valid_price(val):
                return val

        # Offscreen price
        offscreen = soup.select_one(".a-price .a-offscreen")
        if offscreen:
            val = self._clean_price_string(offscreen.get_text())
            if self._is_valid_price(val):
                return val

        # 3. Meta tags
        price = self._extract_from_meta(soup)
        if self._is_valid_price(price):
            return price

        return None

    def _extract_flipkart_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Flipkart: JSON-LD -> og:title with price -> Flipkart price classes."""
        # 1. JSON-LD structured data
        price = self._extract_from_json_ld(soup)
        if self._is_valid_price(price):
            return price

        # 2. og:title with price
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            val = self._extract_price_from_text(og_title["content"])
            if self._is_valid_price(val):
                return val

        # 3. Regex for Flipkart-specific price classes
        fk_classes = ["_30jeq3", "Nx9daj", "Cxhggu", "_16Jk6d", "hl05eU", "_25b18c"]
        for cls_name in fk_classes:
            tag = soup.find(class_=re.compile(cls_name))
            if tag:
                val = self._clean_price_string(tag.get_text())
                if self._is_valid_price(val):
                    return val

        return None

    def _extract_myntra_price(self, soup: BeautifulSoup, html: str) -> Optional[float]:
        """Myntra: JSON-LD -> 'pdp-price' patterns / pdpData -> meta description regex."""
        # 1. JSON-LD
        price = self._extract_from_json_ld(soup)
        if self._is_valid_price(price):
            return price

        # 2. pdp-price class
        pdp_price = soup.find(class_=re.compile(r"pdp-price", re.I))
        if pdp_price:
            val = self._clean_price_string(pdp_price.get_text())
            if self._is_valid_price(val):
                return val

        # Script data in HTML
        if html:
            m = re.search(r'"discountedPrice":\s*(\d+)', html)
            if m:
                val = float(m.group(1))
                if self._is_valid_price(val):
                    return val
            m2 = re.search(r'"price":\s*(\d+)', html)
            if m2:
                val = float(m2.group(1))
                if self._is_valid_price(val):
                    return val

        # 3. Meta description regex
        meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description")
        if meta_desc and meta_desc.get("content"):
            val = self._extract_price_from_text(meta_desc["content"])
            if self._is_valid_price(val):
                return val

        return None

    def _extract_croma_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Croma price extraction."""
        price = self._extract_from_json_ld(soup)
        if self._is_valid_price(price):
            return price

        for cls in ["new-price", "amount", "pdp-cp-price", "main-price"]:
            tag = soup.find(class_=re.compile(cls, re.I))
            if tag:
                val = self._clean_price_string(tag.get_text())
                if self._is_valid_price(val):
                    return val

        return self._extract_from_meta(soup)

    def _extract_reliance_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Reliance Digital price extraction."""
        price = self._extract_from_json_ld(soup)
        if self._is_valid_price(price):
            return price

        for cls in ["pdp__offerPrice", "sp__price", "gDOPQu"]:
            tag = soup.find(class_=re.compile(cls, re.I))
            if tag:
                val = self._clean_price_string(tag.get_text())
                if self._is_valid_price(val):
                    return val

        return self._extract_from_meta(soup)

    def _extract_tatacliq_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Tata CLiQ price extraction."""
        price = self._extract_from_json_ld(soup)
        if self._is_valid_price(price):
            return price

        for cls in ["ProductDescriptionPage__price", "ProductDetails__price", "pdp-price", "Price__actualPrice"]:
            tag = soup.find(class_=re.compile(cls, re.I))
            if tag:
                val = self._clean_price_string(tag.get_text())
                if self._is_valid_price(val):
                    return val

        return self._extract_from_meta(soup)

    def _extract_jiomart_price(self, soup: BeautifulSoup) -> Optional[float]:
        """JioMart price extraction."""
        price = self._extract_from_json_ld(soup)
        if self._is_valid_price(price):
            return price

        for cls in ["price-box", "jm-heading-xxs", "final-price"]:
            tag = soup.find(class_=re.compile(cls, re.I))
            if tag:
                val = self._clean_price_string(tag.get_text())
                if self._is_valid_price(val):
                    return val

        return self._extract_from_meta(soup)

    def _extract_vijaysales_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Vijay Sales price extraction."""
        price = self._extract_from_json_ld(soup)
        if self._is_valid_price(price):
            return price

        for cls in ["vj-price", "pdp-price", "price-box", "prc-val"]:
            tag = soup.find(class_=re.compile(cls, re.I))
            if tag:
                val = self._clean_price_string(tag.get_text())
                if self._is_valid_price(val):
                    return val

        return self._extract_from_meta(soup)

    # ── General Structured & Regex Extractors ──

    def _extract_from_meta(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract price from standard meta tags."""
        for prop in [
            "product:price:amount",
            "og:price:amount",
            "price",
            "twitter:data1",
        ]:
            tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
            if tag and tag.get("content"):
                parsed = self._clean_price_string(tag["content"])
                if self._is_valid_price(parsed):
                    return parsed
        return None

    def _extract_from_json_ld(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract the offer price attached to a Product node in JSON-LD."""
        import json

        def product_prices(node: Any):
            if isinstance(node, list):
                for child in node:
                    yield from product_prices(child)
            elif isinstance(node, dict):
                kind = node.get("@type", [])
                kinds = [kind] if isinstance(kind, str) else kind
                if any(str(k).lower() in {"product", "productgroup"} for k in kinds):
                    offers = node.get("offers", [])
                    offers = offers if isinstance(offers, list) else [offers]
                    for offer in offers:
                        if not isinstance(offer, dict):
                            continue
                        for key in ("price", "priceSpecification", "lowPrice"):
                            value = offer.get(key)
                            if isinstance(value, dict):
                                value = value.get("price")
                            if value is not None:
                                yield value
                for key, child in node.items():
                    if key in {"@graph", "mainEntity", "mainEntityOfPage"}:
                        yield from product_prices(child)

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                text = script.string or ""
                if not text:
                    continue
                data = json.loads(text)
                for raw in product_prices(data):
                    price = self._clean_price_string(str(raw))
                    if self._is_valid_price(price):
                        return price
            except Exception:
                continue
        return None

    def _find_price_in_json(self, data: Any) -> Optional[float]:
        """Recursively find price in JSON-LD structure."""
        if not isinstance(data, dict):
            return None

        for key in ["price", "lowPrice", "highPrice"]:
            if key in data:
                val = self._clean_price_string(str(data[key]))
                if self._is_valid_price(val):
                    return val

        offers = data.get("offers")
        if isinstance(offers, dict):
            p = self._find_price_in_json(offers)
            if self._is_valid_price(p):
                return p
        elif isinstance(offers, list):
            for offer in offers:
                if isinstance(offer, dict):
                    p = self._find_price_in_json(offer)
                    if self._is_valid_price(p):
                        return p

        graph = data.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                if isinstance(item, dict):
                    p = self._find_price_in_json(item)
                    if self._is_valid_price(p):
                        return p

        return None

    def _extract_first_price_after_title(
        self, soup: BeautifulSoup, html: str, page_title: str
    ) -> Optional[float]:
        """
        On a product page, pick the FIRST ₹ price after the product title,
        rather than mode.
        """
        h1 = soup.find("h1")
        start_element = h1 if h1 else soup.find("title")

        if start_element:
            for text_node in start_element.find_all_next(string=True):
                text = str(text_node)
                if "₹" in text or "Rs" in text or "INR" in text:
                    matches = re.findall(
                        r'(?:₹|Rs\.?\s*|INR\s*)\s*([\d,]+(?:\.\d{1,2})?)', text, re.IGNORECASE
                    )
                    for m in matches:
                        val = self._clean_price_string(m)
                        if self._is_valid_price(val):
                            return val

        if page_title and page_title in html:
            idx = html.find(page_title)
            after_title = html[idx + len(page_title): idx + len(page_title) + 5000]
            matches = re.findall(
                r'(?:₹|Rs\.?\s*|INR\s*)\s*([\d,]+(?:\.\d{1,2})?)', after_title, re.IGNORECASE
            )
            for m in matches:
                val = self._clean_price_string(m)
                if self._is_valid_price(val):
                    return val

        # Fallback to first ₹ price found in html
        matches = re.findall(
            r'(?:₹|Rs\.?\s*|INR\s*)\s*([\d,]+(?:\.\d{1,2})?)', html, re.IGNORECASE
        )
        for m in matches:
            val = self._clean_price_string(m)
            if self._is_valid_price(val):
                return val

        return None

    def _extract_price_from_text(self, text: str) -> Optional[float]:
        """Extract first valid ₹/Rs. price from a text snippet."""
        if not text:
            return None
        matches = re.findall(
            r'(?:₹|Rs\.?\s*|INR\s*)\s*([\d,]+(?:\.\d{1,2})?)', text, re.IGNORECASE
        )
        for m in matches:
            val = self._clean_price_string(m)
            if self._is_valid_price(val):
                return val
        return None
