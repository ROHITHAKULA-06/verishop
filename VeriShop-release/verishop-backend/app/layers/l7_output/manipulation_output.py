"""L7 — Manipulation Output Generator: Formats manipulation results for output."""

from typing import Dict, Any, List
from app.models.product import Product


class ManipulationOutputGenerator:
    def generate(self, detection_results: Dict[str, Any], product: Product) -> Dict[str, Any]:
        issues = []
        if detection_results.get("is_manipulated"):
            issues.append(self._format_issue(
                detection_results.get("manipulation_type", "UNKNOWN"),
                detection_results,
            ))
        return {
            "has_issues": len(issues) > 0,
            "issues": issues,
            "summary": self._generate_summary(issues),
            "visual_indicators": [{"type": "ela_heatmap", "available": detection_results.get("ela_score", 0) > 0}],
        }

    def _format_issue(self, issue_type: str, details: Dict) -> Dict:
        severity_map = {"COPY_MOVE": "high", "IMAGE_SPLICING": "high", "METADATA_TAMPERING": "medium", "ENHANCEMENT": "low"}
        return {
            "type": issue_type, "severity": severity_map.get(issue_type, "medium"),
            "description": f"Image manipulation detected: {issue_type.replace('_', ' ').title()}",
            "evidence": details.get("evidence", []),
        }

    def _generate_summary(self, issues: List[Dict]) -> str:
        if not issues: return "No manipulation detected in product images."
        return f"Found {len(issues)} potential image manipulation issue(s). Review evidence before purchasing."
