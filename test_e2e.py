import sys
import os
from pprint import pprint

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import TINYFISH_API_KEY, TINYFISH_SEARCH_URL
from services.tinyfish_client import TinyFishClient
from services.discovery import DiscoveryService
from core.models import StudentProfile, Scholarship
from core.matcher import calculate_match, rank_matches
from core.scam_checker import ScamChecker
from utils.helpers import classify_domain_trust, calculate_deadline_urgency

def run_all_tests():
    print("=" * 60)
    print("SCHEMERADAR: COMPLETE VERIFICATION & TEST SUITE")
    print("=" * 60)

    # ---------------------------------------------------------
    # TEST 1: Configuration
    # ---------------------------------------------------------
    print("\n[TEST 1] Configuration & Initialization:")
    client = TinyFishClient()
    print(f"  TINYFISH_API_KEY Configured: {client.is_configured}")
    assert client.is_configured, "TINYFISH_API_KEY must be configured in .env"
    print("  ✓ Configuration Test Passed!")

    # ---------------------------------------------------------
    # TEST 2: Search API
    # ---------------------------------------------------------
    print("\n[TEST 2] TinyFish Search API:")
    query = "Karnataka SSP scholarship 2026 B.Tech eligibility portal"
    search_res = client.search_schemes(query, limit=5)
    print(f"  Search Success: {search_res.get('success')}")
    print(f"  HTTP Status Code: {search_res.get('status_code')}")
    print(f"  Total Portals Found: {len(search_res.get('results', []))}")
    assert search_res.get("success"), "Search API must return success=True"
    assert len(search_res.get("results", [])) > 0, "Search API must return at least one result"
    first_url = search_res["results"][0]["url"]
    print(f"  Discovered Portal [1]: {first_url}")
    print("  ✓ Search API Test Passed!")

    # ---------------------------------------------------------
    # TEST 3: Fetch API
    # ---------------------------------------------------------
    print("\n[TEST 3] TinyFish Fetch API:")
    target_fetch_url = None
    fetch_res = None
    for r in search_res["results"]:
        u = r.get("url", "")
        f_res = client.fetch_page(u)
        if f_res.get("success") and len(f_res.get("content", "")) > 100:
            target_fetch_url = u
            fetch_res = f_res
            break

    if not target_fetch_url:
        target_fetch_url = "https://scholarships.gov.in"
        fetch_res = client.fetch_page(target_fetch_url)

    print(f"  Target Portal Fetched: {target_fetch_url}")
    print(f"  Fetch Success: {fetch_res.get('success')}")
    print(f"  Fetch HTTP Status: {fetch_res.get('status_code')}")
    content = fetch_res.get("content", "")
    print(f"  Fetched Markdown Character Length: {len(content)}")
    print(f"  Content Preview:\n{content[:250]}...")
    assert fetch_res.get("success"), "Fetch API must return success=True on a public portal"
    print("  ✓ Fetch API Test Passed!")

    # ---------------------------------------------------------
    # TEST 4: Agent API Live Run
    # ---------------------------------------------------------
    print("\n[TEST 4] TinyFish Agent API Live Run:")
    agent_target = "https://scholarships.gov.in"
    agent_goal = "Extract national scholarship application portal headline announcements into JSON."
    print(f"  Target URL: {agent_target}")
    agent_res = client.run_agent(agent_target, goal=agent_goal)
    print(f"  Agent Success: {agent_res.get('success')}")
    print(f"  Agent HTTP Status: {agent_res.get('status_code')}")
    print(f"  Agent Result: {str(agent_res.get('result'))[:250]}...")
    assert agent_res.get("success"), "Agent API must return success=True"
    print("  ✓ Agent API Live Run Passed!")

    # ---------------------------------------------------------
    # TEST 5: Matching Engine & Eligibility Filtering
    # ---------------------------------------------------------
    print("\n[TEST 5] Matching Engine & Eligibility Test:")
    sample_profile = StudentProfile(
        course="B.Tech",
        academic_year="2nd Year",
        college_name="BMS College of Engineering",
        academic_performance="8.5 CGPA",
        state_of_domicile="Karnataka",
        category="OBC",
        family_income_band="₹1–2.5 lakh",
        interests=["Engineering", "Computer Science", "Technology"]
    )

    test_sch = Scholarship(
        scheme_id="sch_test_001",
        scheme_name="Karnataka Post-Matric OBC / EBC Fee Concession & Scholarship",
        provider="Department of Backward Classes Welfare, Govt. of Karnataka",
        description="State financial assistance scheme for students pursuing undergraduate technical courses.",
        eligibility="Students from Karnataka belonging to Category 1, 2A, 2B, 3A, 3B with family income under 2.5 Lakhs.",
        eligible_courses=["B.Tech", "B.E.", "BCA", "Undergraduate"],
        eligible_academic_years=["1st Year", "2nd Year", "3rd Year", "4th Year"],
        eligible_states=["Karnataka"],
        eligible_categories=["OBC", "General"],
        maximum_income=250000.0,
        scholarship_amount="₹25,000 / year + tuition concession",
        application_deadline="2026-12-31",
        application_url="https://ssp.postmatric.karnataka.gov.in",
        source_url="https://ssp.karnataka.gov.in",
        application_status="Open",
        extraction_method="TinyFish Fetch",
    )

    match = calculate_match(sample_profile, test_sch)
    print(f"  Is Eligible: {match.is_eligible}")
    print(f"  Match Score: {match.match_score}/100")
    print(f"  Why This Matches You: {match.why_this_matches_you}")
    assert match.is_eligible, "Sample student should be eligible for Karnataka OBC scholarship"
    assert match.match_score >= 80, "Match score should be >= 80 for strong match"
    print("  ✓ Matching Engine Test Passed!")

    # ---------------------------------------------------------
    # TEST 6: Scam Checker
    # ---------------------------------------------------------
    print("\n[TEST 6] Scam Checker Engine:")
    scam_checker = ScamChecker(client)
    scam_msg = "Pay ₹500 registration fee to get Rs. 50,000 National Scholarship! Share OTP immediately."
    scam_res = scam_checker.investigate(scam_msg)
    print(f"  Input: {scam_msg[:40]}...")
    print(f"  Verdict: {scam_res.verdict}")
    print(f"  Red Flags: {scam_res.red_flags}")
    assert scam_res.verdict == "Suspicious", "Should flag fee demands as Suspicious"
    print("  ✓ Scam Checker Test Passed!")

    # ---------------------------------------------------------
    # TEST 7: End-to-End Discovery Pipeline
    # ---------------------------------------------------------
    print("\n[TEST 7] End-to-End Discovery Workflow:")
    discovery = DiscoveryService(client)
    
    def log_progress(stage, pct):
        print(f"    Progress [{pct}%]: {stage}")

    report = discovery.discover(
        profile=sample_profile,
        progress_callback=log_progress,
        max_sources_to_process=2,  # Quick test with 2 sources
    )

    print(f"  Discovery Success: {report['success']}")
    print(f"  Total Portals Discovered: {report['metrics']['total_discovered']}")
    print(f"  Evaluated Matches Count: {len(report['matches'])}")
    for idx, m in enumerate(report["matches"]):
        sch = m.scholarship
        print(f"\n    [Scheme {idx+1} Record]")
        print(f"      • Name: {sch.scheme_name}")
        print(f"      • Provider: {sch.provider}")
        print(f"      • Deadline: {sch.application_deadline}")
        print(f"      • Amount: {sch.scholarship_amount}")
        print(f"      • Status: {sch.application_status}")
        print(f"      • Match Score: {m.match_score}/100")
        print(f"      • Source URL: {sch.source_url}")
        print(f"      • Application URL: {sch.application_url}")
        print(f"      • Why Matches You: {m.why_this_matches_you}")
        print(f"      • Unverified Fields: {sch.missing_fields}")

    assert report["success"], "Discovery workflow must succeed"
    print("  ✓ End-to-End Discovery Test Passed!")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY! 🎯")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()
