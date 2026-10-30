import logging
from typing import List, Dict, Any, Callable, Optional
from urllib.parse import urlparse

from core.models import StudentProfile, ScholarshipOpportunity, MatchResult, SourcePage
from core.matcher import calculate_match, rank_matches
from services.tinyfish_client import TinyFishClient
from services.extraction import ScholarshipExtractor
from utils.helpers import classify_domain_trust
from config.settings import MAX_PROCESS_URLS

logger = logging.getLogger("SchemeRadar.Discovery")

class DiscoveryService:
    """Orchestrates live web discovery, verification, and extraction powered by TinyFish."""

    def __init__(self, tinyfish_client: Optional[TinyFishClient] = None):
        self.tinyfish = tinyfish_client or TinyFishClient()

    def discover(
        self,
        profile: StudentProfile,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        max_sources_to_process: int = MAX_PROCESS_URLS,
        sort_by: str = "Highest match",
        enable_agent: bool = True,
    ) -> Dict[str, Any]:
        """Execute the end-to-end scholarship discovery workflow with SourcePage / Opportunity separation.
        
        Args:
            profile: StudentProfile entered by student
            progress_callback: Optional callback(stage_name, percent_0_to_100)
            max_sources_to_process: Maximum priority source pages to deep-fetch
            sort_by: Ranking order
            enable_agent: Whether to deploy TinyFish Agent for dynamic browser navigation
            
        Returns:
            Dict containing matches, source_pages, metrics, and activity logs
        """
        def update_progress(msg: str, pct: int):
            logger.info(f"[{pct}%] {msg}")
            if progress_callback:
                try:
                    progress_callback(msg, pct)
                except Exception as e:
                    logger.debug(f"Progress callback exception: {e}")

        update_progress("Formulating targeted TinyFish search queries...", 10)
        queries = self._build_queries(profile)

        # Step 1: TinyFish Search API
        update_progress(f"Scanning official scholarship ecosystems across {len(queries)} queries...", 25)
        raw_search_results = []
        for q in queries:
            resp = self.tinyfish.search_schemes(q, limit=5, location="IN")
            if resp.get("success") and resp.get("results"):
                raw_search_results.extend(resp["results"])

        # Step 2: Always include central directory if not already discovered
        has_central_dir = any("scholarships.gov.in" in r.get("url", "") for r in raw_search_results)
        if not has_central_dir:
            raw_search_results.append({
                "title": "National Scholarship Portal - All Central Schemes",
                "url": "https://scholarships.gov.in/All-Scholarships",
                "snippet": "Official directory of all central and technical scholarship schemes on NSP.",
                "domain": "scholarships.gov.in",
                "site_name": "National Scholarship Portal",
            })

        # Step 3: Deduplicate URLs and prioritize official domains (.gov.in, .nic.in, .ac.in)
        update_progress("Deduplicating and prioritizing authoritative government sources...", 40)
        prioritized_items = self._deduplicate_and_prioritize(raw_search_results, max_sources_to_process)

        # Step 4: Separate SourcePage collection and ScholarshipOpportunity extraction
        source_pages: List[SourcePage] = []
        all_opportunities: List[ScholarshipOpportunity] = []
        total_to_process = len(prioritized_items)
        agent_invoked = False

        for i, item in enumerate(prioritized_items):
            current_url = item["url"]
            domain = item["domain"]
            pct = 45 + int((i / max(1, total_to_process)) * 35)

            update_progress(f"Deep-fetching portal content via TinyFish: {domain} ({i+1}/{total_to_process})...", pct)

            # TinyFish Fetch
            fetch_res = self.tinyfish.fetch_page(current_url)
            content = fetch_res.get("content", "") if fetch_res.get("success") else ""
            links = fetch_res.get("links", [])
            fetch_status = "success" if fetch_res.get("success") else ("proxy_error" if "proxy_error" in str(fetch_res.get("errors", "")).lower() else "failed")

            # 1. Record distinct SourcePage
            src_page = ScholarshipExtractor.extract_source_page(item, fetch_result=fetch_res)
            source_pages.append(src_page)

            # Strategy: Determine if TinyFish Agent is needed
            needs_agent = False
            if enable_agent and not agent_invoked:
                if fetch_status == "success" and content:
                    # If page contains JS-required notices, interactive navigation, or circular accordions
                    if any(trigger in content.lower() for trigger in ["please enable javascript", "click here to login to view circular", "expand all guidelines", "technical education", "all india council"]):
                        needs_agent = True
                elif fetch_status == "failed" and "scholarships.gov.in" in current_url:
                    needs_agent = True

            agent_data = None
            method = "TinyFish Fetch"

            if needs_agent:
                update_progress(f"Deploying TinyFish Agent browser navigation on {domain}...", pct + 2)
                method = "TinyFish Agent"
                agent_invoked = True
                agent_res = self.tinyfish.run_agent(
                    current_url,
                    goal=(
                        f"Navigate {current_url}. Find published scholarship scheme details for {profile.course} {profile.academic_year} "
                        f"students from {profile.state_of_domicile}. Extract scheme name, income limit, scholarship amount, "
                        f"application deadline, and official application link."
                    )
                )
                if agent_res.get("success") and agent_res.get("result"):
                    agent_data = agent_res.get("result")

            # 2. Extract discrete ScholarshipOpportunity records
            extracted_opps = ScholarshipExtractor.extract_opportunities(
                search_item=item,
                fetch_content=content,
                fetch_links=links,
                agent_data=agent_data,
                method=method,
                fetch_status=fetch_status,
            )

            for opp in extracted_opps:
                # Deduplicate by scheme_name
                if not any(existing.scheme_name.lower() == opp.scheme_name.lower() for existing in all_opportunities):
                    all_opportunities.append(opp)

        update_progress("Evaluating multi-tier eligibility and computing personalized scores...", 85)

        # Step 5: Matching & Scoring
        match_results: List[MatchResult] = []
        for opp in all_opportunities:
            match_res = calculate_match(profile, opp)
            match_results.append(match_res)

        ranked = rank_matches(match_results, sort_by=sort_by)

        # Step 6: Compute Distinct Phase 2 Dashboard Metrics
        total_sources = len(source_pages)
        total_extracted = len(ranked)
        verified_open = len([m for m in ranked if m.scholarship.application_status in ("Open", "Closing soon") and m.scholarship.deadline is not None])
        potential_matches = len([m for m in ranked if m.eligibility_status in ("Eligible", "Potential match")])
        requiring_verification = len([m for m in ranked if len(m.missing_criteria) > 0 or m.scholarship.verification_status != "direct_page_verified"])

        update_progress("Discovery and verification completed!", 100)

        return {
            "success": True,
            "queries_executed": queries,
            "source_pages": source_pages,
            "matches": ranked,
            "activity_log": self.tinyfish.activity_log,
            "total_search_hits": len(raw_search_results),
            "metrics": {
                "total_sources": total_sources,
                "total_extracted": total_extracted,
                "verified_open": verified_open,
                "potential_matches": potential_matches,
                "requiring_verification": requiring_verification,
                "total_discovered": total_sources,
                "closing_soon": len([m for m in ranked if m.urgency in ("Urgent", "Closing soon")]),
            }
        }

    def _build_queries(self, profile: StudentProfile) -> List[str]:
        """Construct highly targeted search queries for Indian scholarships."""
        state = profile.state_of_domicile
        course = profile.course
        year = profile.academic_year
        cat = profile.category
        
        queries = []
        
        # 1. State specific query (e.g. Karnataka SSP)
        if state and state != "All India / Central":
            queries.append(f"{state} state scholarship portal {course} {year} eligibility deadline official portal")
        
        # 2. National Scholarship Portal Directory
        queries.append(f"site:scholarships.gov.in All-Scholarships central scheme {course} {cat}")
        
        # 3. AICTE / Technical degree query
        if "Engineering" in profile.interests or course in ["B.Tech", "B.E.", "M.Tech"]:
            queries.append(f"AICTE Pragati Swanath Saksham scholarship scheme {course} {cat} eligibility amount")
        else:
            queries.append(f"UGC post matric scholarship scheme {course} {cat} eligibility")

        return queries

    def _deduplicate_and_prioritize(
        self,
        raw_items: List[Dict[str, Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Deduplicate URLs and sort so official government (.gov.in, .nic.in, .ac.in) portals are prioritized."""
        seen_urls = set()
        unique_items = []

        for item in raw_items:
            url = item.get("url", "").strip()
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            
            # Filter non-relevant media sites
            if any(bad in url.lower() for bad in ["facebook.com", "twitter.com", "instagram.com", "youtube.com", "pinterest.com"]):
                continue

            unique_items.append(item)

        # Prioritize by domain trust score
        def score_item(it: Dict[str, Any]) -> int:
            trust = classify_domain_trust(it.get("url", ""))
            return trust.get("trust_score", 0)

        sorted_items = sorted(unique_items, key=score_item, reverse=True)
        return sorted_items[:limit]
