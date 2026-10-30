import json
import logging
import time
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import requests

from config.settings import (
    TINYFISH_API_KEY,
    TINYFISH_SEARCH_URL,
    TINYFISH_FETCH_URL,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RETRY_BACKOFF,
)
from core.models import TinyFishLogEntry

logger = logging.getLogger("SchemeRadar.TinyFishClient")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class TinyFishClient:
    """Official TinyFish REST API Client for SchemeRadar.
    Supports Search API, Fetch API, and Agent API with live activity logging.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or TINYFISH_API_KEY or "").strip()
        self.activity_log: List[TinyFishLogEntry] = []
        if not self.api_key:
            logger.warning("No TINYFISH_API_KEY configured. Live web queries will fail unless configured.")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _log_activity(self, operation: str, target: str, status: str, details: str):
        """Append an entry to the in-memory TinyFish activity log."""
        entry = TinyFishLogEntry(
            operation=operation,
            target=target,
            status=status,
            details=details,
        )
        self.activity_log.append(entry)
        logger.info(f"[TinyFish Log] {operation} | {status} | {target[:60]} | {details[:80]}")

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "SchemeRadar-ScholarshipDiscovery/1.0",
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def search_schemes(self, query: str, limit: int = 5, location: str = "IN") -> Dict[str, Any]:
        """Search Indian government & educational scholarship sites using TinyFish Search API.
        
        Args:
            query: The search phrase
            limit: Maximum results to return
            location: Two-letter country code for geo-targeting (default: "IN" for India)
            
        Returns:
            Dict containing 'success', 'results' list, and 'raw' payload
        """
        if not self.is_configured:
            self._log_activity("SEARCH", query, "FAILED", "TINYFISH_API_KEY is not configured")
            return {
                "success": False,
                "error": "TINYFISH_API_KEY is not configured.",
                "results": [],
            }

        url = TINYFISH_SEARCH_URL
        params = {
            "query": query,
            "location": location,
        }
        headers = self._get_headers()

        logger.info(f"Invoking TinyFish Search API for query: {query[:60]}... (location={location})")
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    normalized_results = self._normalize_search_results(data, limit)
                    self._log_activity(
                        "SEARCH",
                        query,
                        "SUCCESS",
                        f"HTTP 200: Discovered {len(normalized_results)} portals"
                    )
                    return {
                        "success": True,
                        "status_code": 200,
                        "query": query,
                        "total_found": len(normalized_results),
                        "results": normalized_results,
                        "raw": data,
                    }
                elif response.status_code in (429, 502, 503, 504):
                    logger.warning(f"Search API returned {response.status_code}. Retrying ({attempt}/{MAX_RETRIES})...")
                    time.sleep(RETRY_BACKOFF ** attempt)
                else:
                    error_msg = f"Search API failed with HTTP {response.status_code}: {response.text[:200]}"
                    logger.error(error_msg)
                    self._log_activity("SEARCH", query, "FAILED", f"HTTP {response.status_code}")
                    return {"success": False, "status_code": response.status_code, "error": error_msg, "results": []}

            except requests.exceptions.RequestException as e:
                logger.warning(f"Search API request exception on attempt {attempt}: {str(e)}")
                if attempt == MAX_RETRIES:
                    self._log_activity("SEARCH", query, "FAILED", f"Connection error: {str(e)[:60]}")
                    return {"success": False, "error": f"Search API connection error: {str(e)}", "results": []}
                time.sleep(RETRY_BACKOFF ** attempt)

        self._log_activity("SEARCH", query, "FAILED", "Max retries exceeded")
        return {"success": False, "error": "Search API maximum retries exceeded.", "results": []}

    def _normalize_search_results(self, data: Any, limit: int) -> List[Dict[str, Any]]:
        """Normalize various TinyFish Search API JSON response structures into a uniform list."""
        raw_items = []
        if isinstance(data, list):
            raw_items = data
        elif isinstance(data, dict):
            for key in ["results", "data", "items", "organic_results"]:
                if key in data and isinstance(data[key], list):
                    raw_items = data[key]
                    break
            if not raw_items and "title" in data and "url" in data:
                raw_items = [data]

        normalized = []
        for item in raw_items[:limit]:
            if not isinstance(item, dict):
                continue
            title = item.get("title") or item.get("name") or "Government Scholarship Portal"
            target_url = item.get("url") or item.get("link") or ""
            snippet = item.get("snippet") or item.get("description") or item.get("text") or ""
            site_name = item.get("site_name") or ""
            
            if not target_url or not target_url.startswith("http"):
                continue

            parsed_url = urlparse(target_url)
            domain = parsed_url.netloc.lower()

            normalized.append({
                "title": title.strip(),
                "url": target_url.strip(),
                "snippet": snippet.strip(),
                "domain": domain,
                "site_name": site_name.strip(),
            })

        return normalized

    def fetch_page(self, url: str, purpose: Optional[str] = None) -> Dict[str, Any]:
        """Fetch clean Markdown content and outbound links from a target scholarship page using TinyFish Fetch API.
        
        Args:
            url: Target web page URL
            purpose: Intent guidance for clean extraction
            
        Returns:
            Dict containing 'success', 'content' (Markdown/text), 'title', 'links', 'errors', etc.
        """
        if not self.is_configured:
            self._log_activity("FETCH", url, "FAILED", "TINYFISH_API_KEY is not configured")
            return {"success": False, "error": "TINYFISH_API_KEY is not configured.", "content": "", "links": [], "errors": []}

        headers = self._get_headers()
        headers["Content-Type"] = "application/json"

        default_purpose = (
            "Extract complete scholarship details: scheme name, eligibility criteria, "
            "minimum/maximum family income, eligible courses, states, application deadline, "
            "scholarship grant amount, and official application URL."
        )

        payload = {
            "urls": [url],
            "format": "markdown",
            "purpose": purpose or default_purpose,
            "links": True,
            "per_url_timeout_ms": 30000,
        }

        logger.info(f"Invoking TinyFish Fetch API for URL: {url}")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = requests.post(
                    TINYFISH_FETCH_URL,
                    json=payload,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT,
                )

                if response.status_code == 200:
                    data = response.json()
                    content, page_title, links, errors = self._extract_fetch_text(data)
                    is_ok = bool(content) and len(errors) == 0
                    
                    if is_ok:
                        self._log_activity(
                            "FETCH",
                            url,
                            "SUCCESS",
                            f"Extracted {len(content)} chars markdown, {len(links)} links"
                        )
                    else:
                        err_str = "; ".join(e.get("error", "") for e in errors) if errors else "Empty content"
                        status_label = "PROXY_ERROR" if "proxy_error" in err_str.lower() else "FAILED"
                        self._log_activity("FETCH", url, status_label, f"Errors: {err_str[:60]}")

                    return {
                        "success": is_ok,
                        "status_code": 200,
                        "url": url,
                        "title": page_title,
                        "content": content,
                        "links": links,
                        "errors": errors,
                        "raw": data,
                    }
                elif response.status_code in (429, 502, 503, 504):
                    logger.warning(f"Fetch API returned {response.status_code}. Retrying ({attempt}/{MAX_RETRIES})...")
                    time.sleep(RETRY_BACKOFF ** attempt)
                else:
                    error_msg = f"Fetch API HTTP {response.status_code}: {response.text[:200]}"
                    logger.warning(error_msg)
                    self._log_activity("FETCH", url, "FAILED", f"HTTP {response.status_code}")
                    return {"success": False, "status_code": response.status_code, "error": error_msg, "content": "", "links": [], "errors": [{"error": error_msg}]}

            except requests.exceptions.RequestException as e:
                logger.warning(f"Fetch API request exception on attempt {attempt}: {str(e)}")
                if attempt == MAX_RETRIES:
                    self._log_activity("FETCH", url, "FAILED", f"Connection error: {str(e)[:60]}")
                    return {"success": False, "error": f"Fetch API connection error: {str(e)}", "content": "", "links": [], "errors": [{"error": str(e)}]}
                time.sleep(RETRY_BACKOFF ** attempt)

        self._log_activity("FETCH", url, "FAILED", "Max retries exceeded")
        return {"success": False, "error": "Fetch API max retries exceeded.", "content": "", "links": [], "errors": []}

    def _extract_fetch_text(self, data: Any) -> tuple[str, str, List[str], List[Dict[str, Any]]]:
        """Extract markdown text, title, links (as normalized strings), and errors from TinyFish Fetch API response."""
        content = ""
        title = ""
        raw_links = []
        errors = []

        if isinstance(data, dict):
            errors = data.get("errors", [])
            results = data.get("results")
            if isinstance(results, list) and len(results) > 0:
                first = results[0]
                if isinstance(first, dict):
                    content = first.get("text") or first.get("content") or first.get("markdown") or ""
                    title = first.get("title") or ""
                    raw_links = first.get("links") or []
            elif "text" in data or "content" in data or "markdown" in data:
                content = data.get("text") or data.get("content") or data.get("markdown") or ""
                title = data.get("title") or ""
                raw_links = data.get("links") or []

        # Normalize links to clean List[str]
        normalized_links: List[str] = []
        seen = set()
        for item in raw_links:
            u = ""
            if isinstance(item, str):
                u = item.strip()
            elif isinstance(item, dict):
                u = (item.get("url") or item.get("href") or "").strip()
            if u and u.startswith("http") and u not in seen:
                seen.add(u)
                normalized_links.append(u)

        return str(content).strip(), str(title).strip(), normalized_links, errors

    def run_agent(self, url: str, goal: Optional[str] = None, event_callback: Optional[Any] = None) -> Dict[str, Any]:
        """Run TinyFish Agent to navigate interactive, JS-heavy, or expandable scholarship pages.
        Uses the robust SSE endpoint to stream live navigation steps with an output schema.
        Never falls back to goal text or commentary as extracted scholarship information.
        
        Args:
            url: Target web page URL
            goal: Natural language instructions for navigation and extraction
            event_callback: Optional callable(event_dict) to receive live progress events
            
        Returns:
            Dict containing 'success', 'result' (dict or None), and 'status_code'
        """
        if not self.is_configured:
            self._log_activity("AGENT", url, "FAILED", "TINYFISH_API_KEY is not configured")
            return {"success": False, "error": "TINYFISH_API_KEY is not configured.", "result": None}

        headers = self._get_headers()
        headers["Content-Type"] = "application/json"

        default_goal = (
            "Navigate this scholarship portal page. Find published scholarship schemes for undergraduate / technical students. "
            "Extract: 1) Scheme name, 2) Eligible courses, 3) Income limits, 4) Scholarship amount, "
            "5) Application closing deadline, 6) Official application link. Return structured JSON."
        )

        output_schema = {
            "type": "object",
            "properties": {
                "scheme_name": {"type": "string"},
                "provider": {"type": "string"},
                "description": {"type": "string"},
                "eligibility": {"type": "string"},
                "eligible_courses": {"type": "array", "items": {"type": "string"}},
                "eligible_academic_years": {"type": "array", "items": {"type": "string"}},
                "eligible_states": {"type": "array", "items": {"type": "string"}},
                "eligible_categories": {"type": "array", "items": {"type": "string"}},
                "maximum_income": {"type": "number"},
                "scholarship_amount": {"type": "string"},
                "application_deadline": {"type": "string"},
                "application_url": {"type": "string"},
                "application_status": {"type": "string"}
            }
        }

        # Do NOT pass max_steps to avoid HTTP 403 on tier-limited accounts
        payload = {
            "url": url,
            "goal": goal or default_goal,
            "output_schema": output_schema,
            "browser_profile": "lite",
            "agent_config": {
                "max_duration_seconds": 45
            }
        }

        sse_url = "https://agent.tinyfish.ai/v1/automation/run-sse"
        logger.info(f"Invoking TinyFish Agent SSE on URL: {url}")
        self._log_activity("AGENT", url, "STREAMING", f"Goal: {(goal or default_goal)[:60]}")

        final_result = None
        streaming_url = None
        start_time = time.time()
        max_agent_wait_secs = 35  # Cap wait to 35s for crisp demo responsiveness

        try:
            with requests.post(
                sse_url,
                json=payload,
                headers=headers,
                stream=True,
                timeout=45,
            ) as response:
                if response.status_code != 200:
                    logger.warning(f"Agent SSE HTTP {response.status_code}: {response.text[:200]}")
                    self._log_activity("AGENT", url, "FAILED", f"HTTP {response.status_code}")
                    return {"success": False, "status_code": response.status_code, "error": f"HTTP {response.status_code}", "result": None}

                for line in response.iter_lines():
                    if time.time() - start_time > max_agent_wait_secs:
                        logger.info("Agent reached wait threshold; finalizing with captured steps.")
                        break

                    if not line:
                        continue
                    decoded = line.decode("utf-8", errors="ignore").strip()
                    if decoded.startswith("data:"):
                        raw_json = decoded[5:].strip()
                        try:
                            event = json.loads(raw_json)
                            evt_type = event.get("type", "")
                            
                            if event_callback:
                                try:
                                    event_callback(event)
                                except Exception:
                                    pass

                            if evt_type == "STREAMING_URL":
                                streaming_url = event.get("streaming_url")
                                self._log_activity("AGENT", url, "LIVE_VIEW", f"Live browser stream: {streaming_url}")
                            elif evt_type == "PROGRESS":
                                step_desc = event.get("purpose") or event.get("action") or event.get("message") or ""
                                if step_desc:
                                    self._log_activity("AGENT", url, "NAVIGATING", f"Step: {step_desc[:80]}")
                            elif evt_type in ("COMPLETE", "DONE", "FINISHED"):
                                candidate = event.get("result") or event.get("data")
                                if isinstance(candidate, str) and candidate.strip().startswith("{"):
                                    try:
                                        final_result = json.loads(candidate)
                                    except Exception:
                                        final_result = candidate
                                else:
                                    final_result = candidate
                                break
                            elif evt_type == "TF_API_RESULT":
                                if not final_result:
                                    final_result = event.get("result")
                        except json.JSONDecodeError:
                            continue

                # Ensure final_result is structured dict, not arbitrary progress text or prompt goal
                extracted_data = None
                if isinstance(final_result, dict):
                    extracted_data = final_result
                elif isinstance(final_result, str) and final_result.strip().startswith("{"):
                    try:
                        extracted_data = json.loads(final_result)
                    except Exception:
                        extracted_data = None

                status_text = "SUCCESS" if extracted_data else "COMPLETED_WITHOUT_SCHEMA"
                detail_msg = f"Extracted: {extracted_data.get('scheme_name', 'No name')}" if extracted_data else "No structured schema extracted"
                self._log_activity("AGENT", url, status_text, detail_msg)

                return {
                    "success": True,
                    "status_code": 200,
                    "url": url,
                    "result": extracted_data,
                    "streaming_url": streaming_url,
                }

        except Exception as e:
            logger.warning(f"Agent SSE connection error: {str(e)}")
            self._log_activity("AGENT", url, "FAILED", f"Error: {str(e)[:60]}")
            return {"success": False, "error": str(e), "result": None}

