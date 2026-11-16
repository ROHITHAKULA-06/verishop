"""
L4 — Comprehensive Website Trust Evaluator
Checks: SSL Certificate, Domain Age, Connection Type, Reddit Reviews
Produces a detailed breakdown with per-phase scoring.
"""
import ssl
import socket
import re
import whois
import tldextract
from ddgs import DDGS
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


class WebsiteTrustEvaluator:
    """
    Evaluates the legitimacy of a website through multiple independent checks.
    Each check produces its own score and evidence.
    """

    # Minimum trust score to pass (0.0 - 1.0)
    MINIMUM_TRUST_THRESHOLD = 0.50

    # Weights for final score aggregation
    WEIGHTS = {
        "ssl": 0.30,
        "domain_age": 0.25,
        "connection": 0.15,
        "reddit_reviews": 0.30,
    }

    WELL_KNOWN_DOMAINS = {
        "flipkart", "amazon", "myntra", "ajio", "tatacliq",
        "croma", "reliancedigital", "jiomart", "snapdeal", "nykaa", "meesho",
        "vijaysales", "poorvika", "firstcry", "pepperfry", "urbanladder", "decathlon", "ikea"
    }

    def __init__(self):
        self._connection_cache: Dict[str, Dict[str, Any]] = {}

    def evaluate(self, url: str, domain: str) -> Dict[str, Any]:
        """
        Run all trust checks and return a detailed breakdown.
        Returns dict with overall_score, passed, phases, risk_flags, evidence.
        """
        phases = {}

        # Phase 1: SSL Certificate Inspection
        phases["ssl"] = self._check_ssl(domain)

        # Phase 2: Domain Age (WHOIS)
        phases["domain_age"] = self._check_domain_age(domain)

        # Phase 3: Connection Type
        phases["connection"] = self._check_connection(domain)

        # Phase 4: Reddit Reviews
        phases["reddit_reviews"] = self._check_reddit_reviews(domain)

        # Aggregate
        overall_score = 0.0
        total_weight = 0.0
        all_evidence = []
        all_flags = []

        for phase_name, phase_data in phases.items():
            weight = self.WEIGHTS.get(phase_name, 0.1)
            overall_score += phase_data["score"] * weight
            total_weight += weight
            all_evidence.extend(phase_data.get("evidence", []))
            all_flags.extend(phase_data.get("flags", []))

        if total_weight > 0:
            overall_score /= total_weight

        overall_score = round(max(0.0, min(1.0, overall_score)), 4)
        passed = overall_score >= self.MINIMUM_TRUST_THRESHOLD

        # Determine discard reason if failed
        discard_reasons = []
        if not passed:
            for phase_name, phase_data in phases.items():
                if phase_data["score"] < 0.4:
                    discard_reasons.append(f"Failed {phase_data['name']}: {phase_data['score']:.0%}")

        return {
            "domain": domain,
            "overall_score": overall_score,
            "passed": passed,
            "discard_reasons": discard_reasons,
            "phases": phases,
            "risk_flags": all_flags,
            "evidence": all_evidence,
        }

    def _get_connection_data(self, domain: str) -> Dict[str, Any]:
        """Fetch and cache TLS connection and certificate data for a domain."""
        if domain in self._connection_cache:
            return self._connection_cache[domain]

        data = {
            "success": False,
            "cert": None,
            "tls_version": None,
            "cipher_info": None,
            "error": None,
            "error_type": None,
        }

        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=8) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    data["cert"] = ssock.getpeercert()
                    data["tls_version"] = ssock.version()
                    data["cipher_info"] = ssock.cipher()
                    data["success"] = True
        except ssl.SSLCertVerificationError as e:
            data["error"] = e
            data["error_type"] = "cert_verification"
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            data["error"] = e
            data["error_type"] = "connection_failed"
        except Exception as e:
            data["error"] = e
            data["error_type"] = "unknown"

        self._connection_cache[domain] = data
        return data

    # ── Phase 1: SSL Certificate ──

    def _check_ssl(self, domain: str) -> Dict[str, Any]:
        """Inspect the SSL/TLS certificate of the domain."""
        phase = {
            "name": "SSL Certificate",
            "score": 0.0,
            "evidence": [],
            "flags": [],
            "details": {},
        }

        conn_data = self._get_connection_data(domain)
        if not conn_data["success"]:
            err_type = conn_data["error_type"]
            err = conn_data["error"]
            if err_type == "cert_verification":
                phase["score"] = 0.0
                phase["flags"].append(f"SSL certificate verification FAILED: {err}")
                phase["evidence"].append("⛔ Invalid or self-signed SSL certificate")
            else:
                phase["score"] = 0.1
                phase["flags"].append(f"Could not establish SSL connection: {err}")
                phase["evidence"].append("Could not connect to verify SSL")
            return phase

        try:
            cert = conn_data["cert"]
            tls_version = conn_data["tls_version"]
            cipher_info = conn_data["cipher_info"]

            # Issuer
            issuer_dict = dict(x[0] for x in cert.get("issuer", []))
            issuer_org = issuer_dict.get("organizationName", "Unknown")
            issuer_cn = issuer_dict.get("commonName", "Unknown")

            # Subject
            subject_dict = dict(x[0] for x in cert.get("subject", []))
            subject_org = subject_dict.get("organizationName", "")
            subject_cn = subject_dict.get("commonName", "")

            # Dates
            not_after_ts = ssl.cert_time_to_seconds(cert["notAfter"])
            not_before_ts = ssl.cert_time_to_seconds(cert["notBefore"])
            expires = datetime.fromtimestamp(not_after_ts, tz=timezone.utc)
            issued = datetime.fromtimestamp(not_before_ts, tz=timezone.utc)
            now = datetime.now(tz=timezone.utc)
            days_remaining = (expires - now).days

            cipher_name = cipher_info[0] if cipher_info else "Unknown"
            cipher_bits = cipher_info[2] if cipher_info else 0

            phase["details"] = {
                "issuer": issuer_org,
                "issuer_cn": issuer_cn,
                "subject_org": subject_org,
                "subject_cn": subject_cn,
                "issued": issued.strftime("%Y-%m-%d"),
                "expires": expires.strftime("%Y-%m-%d"),
                "days_remaining": days_remaining,
                "tls_version": tls_version,
                "cipher": cipher_name,
                "cipher_bits": cipher_bits,
            }

            # Scoring
            score = 0.5  # Base: has SSL

            # Trusted CA issuers
            trusted_cas = ["DigiCert", "Let's Encrypt", "Comodo", "GlobalSign",
                           "GeoTrust", "Sectigo", "Amazon", "Google Trust", "Cloudflare"]
            if any(ca.lower() in issuer_org.lower() for ca in trusted_cas):
                score += 0.2
                phase["evidence"].append(f"SSL issued by trusted CA: {issuer_org}")
            else:
                phase["evidence"].append(f"SSL issuer: {issuer_org}")

            # Certificate validity
            if days_remaining > 30:
                score += 0.15
                phase["evidence"].append(f"Certificate valid for {days_remaining} more days (expires {expires.strftime('%Y-%m-%d')})")
            elif days_remaining > 0:
                score += 0.05
                phase["flags"].append(f"Certificate expiring soon ({days_remaining} days)")
            else:
                score -= 0.3
                phase["flags"].append("Certificate has EXPIRED!")

            # TLS version
            if tls_version in ("TLSv1.3",):
                score += 0.15
                phase["evidence"].append(f"Uses latest {tls_version} protocol")
            elif tls_version in ("TLSv1.2",):
                score += 0.1
                phase["evidence"].append(f"Uses {tls_version} protocol (secure)")
            else:
                phase["flags"].append(f"Outdated TLS version: {tls_version}")

            # Organization in subject (EV/OV cert)
            if subject_org:
                score += 0.1
                phase["evidence"].append(f"Organization-validated cert: {subject_org}")

            phase["score"] = min(1.0, score)

        except Exception as e:
            phase["score"] = 0.1
            phase["flags"].append(f"Error parsing SSL certificate: {e}")
            phase["evidence"].append("Could not parse SSL certificate details")

        return phase

    # ── Phase 2: Domain Age (WHOIS) ──

    def _check_domain_age(self, domain: str) -> Dict[str, Any]:
        """Check domain registration age via WHOIS."""
        phase = {
            "name": "Domain Age",
            "score": 0.5,
            "evidence": [],
            "flags": [],
            "details": {},
        }

        ext = tldextract.extract(domain)
        root_domain = f"{ext.domain}.{ext.suffix}"
        site_name = ext.domain.lower()
        is_well_known = site_name in self.WELL_KNOWN_DOMAINS or any(d in domain.lower() for d in self.WELL_KNOWN_DOMAINS)
        is_in_domain = ext.suffix.endswith("in")

        # Increase timeout tolerance for .in domains (20s) vs standard (15s)
        whois_timeout = 20 if is_in_domain else 15

        try:
            domain_info = whois.whois(root_domain, timeout=whois_timeout)
            creation_date = domain_info.creation_date
            expiry_date = domain_info.expiration_date
            registrar = domain_info.registrar

            if isinstance(creation_date, list):
                creation_date = creation_date[0]
            if isinstance(expiry_date, list):
                expiry_date = expiry_date[0]

            if creation_date:
                now = datetime.now().replace(tzinfo=None)
                created = creation_date.replace(tzinfo=None)
                age_days = (now - created).days
                age_years = age_days / 365.25

                phase["details"]["created"] = created.strftime("%Y-%m-%d")
                phase["details"]["age_days"] = age_days
                phase["details"]["age_years"] = round(age_years, 1)

                if registrar:
                    phase["details"]["registrar"] = registrar
                    phase["evidence"].append(f"Registered with: {registrar}")

                if age_years > 10:
                    phase["score"] = 1.0
                    phase["evidence"].append(f"Domain is {age_years:.0f} years old — highly established")
                elif age_years > 5:
                    phase["score"] = 0.9
                    phase["evidence"].append(f"Domain is {age_years:.0f} years old — well established")
                elif age_years > 2:
                    phase["score"] = 0.7
                    phase["evidence"].append(f"Domain is {age_years:.1f} years old — established")
                elif age_years > 1:
                    phase["score"] = 0.5
                    phase["evidence"].append(f"Domain is {age_years:.1f} years old — relatively new")
                elif age_days > 90:
                    phase["score"] = 0.3
                    phase["flags"].append(f"Domain is only {age_days} days old — new")
                else:
                    phase["score"] = 0.1
                    phase["flags"].append(f"Domain is only {age_days} days old — very new, HIGH RISK")

            if expiry_date:
                exp = expiry_date.replace(tzinfo=None)
                exp_days = (exp - datetime.now().replace(tzinfo=None)).days
                phase["details"]["expires"] = exp.strftime("%Y-%m-%d")
                if exp_days > 365:
                    phase["evidence"].append(f"Domain registration valid until {exp.strftime('%Y-%m-%d')}")
                elif exp_days > 0:
                    phase["flags"].append(f"Domain registration expiring in {exp_days} days")
                else:
                    phase["flags"].append("Domain registration has EXPIRED!")

        except Exception as e:
            logger.warning("whois_check_failed", domain=domain, error=str(e))
            phase["score"] = 0.3
            phase["flags"].append("Could not verify domain registration (WHOIS unavailable)")

        # Well-known domain floor
        if is_well_known:
            if phase["score"] < 0.8:
                phase["score"] = 0.8
                phase["evidence"].append(f"Established platform: {site_name} has verified historical domain standing (floor score applied)")
                phase["flags"] = [f for f in phase["flags"] if "Could not verify" not in f and "HIGH RISK" not in f]

        return phase

    # ── Phase 3: Connection Type ──

    def _check_connection(self, domain: str) -> Dict[str, Any]:
        """Check connection security details using cached connection."""
        phase = {
            "name": "Connection Security",
            "score": 0.5,
            "evidence": [],
            "flags": [],
            "details": {},
        }

        conn_data = self._get_connection_data(domain)
        if not conn_data["success"]:
            err = conn_data["error"]
            phase["score"] = 0.0
            phase["flags"].append(f"Could not establish secure connection: {str(err)[:100]}")
            phase["evidence"].append("Website may not support HTTPS")
            return phase

        try:
            tls_version = conn_data["tls_version"]
            cipher_info = conn_data["cipher_info"]

            phase["details"]["tls_version"] = tls_version
            phase["details"]["cipher"] = cipher_info[0] if cipher_info else "Unknown"
            phase["details"]["bits"] = cipher_info[2] if cipher_info else 0
            phase["details"]["protocol"] = "HTTPS"

            # TLS version scoring
            if tls_version == "TLSv1.3":
                phase["score"] = 1.0
                phase["evidence"].append("Connection uses TLSv1.3 (latest, most secure)")
            elif tls_version == "TLSv1.2":
                phase["score"] = 0.8
                phase["evidence"].append("Connection uses TLSv1.2 (secure)")
            else:
                phase["score"] = 0.3
                phase["flags"].append(f"Outdated protocol: {tls_version}")

            # Cipher strength
            bits = cipher_info[2] if cipher_info else 0
            if bits >= 256:
                phase["evidence"].append(f"Strong {bits}-bit encryption ({cipher_info[0]})")
            elif bits >= 128:
                phase["evidence"].append(f"{bits}-bit encryption")
            else:
                phase["flags"].append(f"Weak encryption: {bits}-bit")

        except Exception as e:
            phase["score"] = 0.0
            phase["flags"].append(f"Error checking connection details: {str(e)[:100]}")
            phase["evidence"].append("Website connection details unavailable")

        return phase

    # ── Phase 4: Reddit Reviews ──

    def _check_reddit_reviews(self, domain: str) -> Dict[str, Any]:
        """Search Reddit for reviews/opinions about this website."""
        phase = {
            "name": "Public Reviews & Social Mentions",
            "score": 0.5,  # Neutral default
            "evidence": [],
            "flags": [],
            "details": {
                "positive_mentions": 0,
                "negative_mentions": 0,
                "total_discussions": 0,
                "snippets": [],
            },
        }

        ext = tldextract.extract(domain)
        site_name = ext.domain.lower()  # e.g., "flipkart" from "www.flipkart.com"
        is_well_known = site_name in self.WELL_KNOWN_DOMAINS or any(d in domain.lower() for d in self.WELL_KNOWN_DOMAINS)

        try:
            with DDGS() as ddgs:
                results = ddgs.text(
                    f"{site_name} shopping review legit trustworthy scam site:reddit.com OR site:trustpilot.com OR site:mouthshut.com OR site:x.com",
                    region="in-en", max_results=8
                )

                positive_kw = ["legit", "legitimate", "trustworthy", "reliable", "genuine",
                               "safe", "good experience", "recommend", "authentic", "trusted",
                               "great", "love", "best", "official"]
                negative_kw = ["scam", "fake", "fraud", "avoid", "spam", "ripoff", "rip-off",
                               "terrible", "worst", "never buy", "don't buy", "counterfeit",
                               "not legit", "sketchy", "shady", "beware", "warning", "steal"]

                positive_count = 0
                negative_count = 0
                total = 0

                for r in results:
                    title = r.get("title", "").lower()
                    body = r.get("body", "").lower()
                    combined = f"{title} {body}"
                    total += 1

                    pos = sum(1 for kw in positive_kw if kw in combined)
                    neg = sum(1 for kw in negative_kw if kw in combined)

                    positive_count += pos
                    negative_count += neg

                    # Save snippet
                    snippet = r.get("body", "")[:150]
                    if snippet:
                        phase["details"]["snippets"].append(snippet)

                phase["details"]["total_discussions"] = total
                phase["details"]["positive_mentions"] = positive_count
                phase["details"]["negative_mentions"] = negative_count

                if total == 0:
                    phase["score"] = 0.5
                    phase["evidence"].append("No Reddit discussions found about this website")
                else:
                    phase["evidence"].append(f"Found {total} Reddit discussions about {site_name}")

                    if negative_count == 0 and positive_count > 0:
                        phase["score"] = 0.9
                        phase["evidence"].append(f"All mentions positive ({positive_count} positive signals)")
                    elif positive_count > negative_count * 2:
                        phase["score"] = 0.8
                        phase["evidence"].append(f"Mostly positive: {positive_count} positive vs {negative_count} negative signals")
                    elif positive_count > negative_count:
                        phase["score"] = 0.65
                        phase["evidence"].append(f"Mixed-positive: {positive_count} positive vs {negative_count} negative signals")
                    elif negative_count > positive_count * 2:
                        phase["score"] = 0.2
                        phase["flags"].append(f"Mostly negative reviews: {negative_count} negative vs {positive_count} positive")
                    elif negative_count > positive_count:
                        phase["score"] = 0.35
                        phase["flags"].append(f"Mixed-negative: {negative_count} negative vs {positive_count} positive signals")
                    else:
                        phase["score"] = 0.5
                        phase["evidence"].append(f"Balanced reviews: {positive_count} positive, {negative_count} negative")

        except Exception as e:
            logger.warning("reddit_check_failed", domain=domain, error=str(e))
            phase["evidence"].append("Could not fetch Reddit reviews")

        # Well-known domain floor: discussions like 'Is Myntra legit?' contain negative keywords even for legit sites
        if is_well_known:
            if phase["score"] < 0.7:
                phase["score"] = 0.7
                phase["evidence"].append(f"Established platform ({site_name}): review score floor of 0.7 applied")
                phase["flags"] = [f for f in phase["flags"] if "Mostly negative" not in f]

        return phase
